//! Character spans from token tags. See `gopya/spans.py`.

use crate::Span;
use regex::Regex;
use std::sync::OnceLock;

pub const SENTENCE_END: &str = "।?!";
pub const SPACE: &str = " \t\r\n\u{a0}";
const NAMES: [&str; 3] = ["PERSON", "LOCATION", "ORGANIZATION"];
const NUMBERS: [&str; 8] =
    ["CITIZENSHIP_NO", "NATIONAL_ID", "PAN", "PASSPORT_NO", "LICENSE_NO", "VOTER_ID", "BANK_ACCOUNT", "PHONE"];

/// A Latin or a Devanagari digit.
pub fn is_digit(ch: char) -> bool {
    ch.is_ascii_digit() || ('०'..='९').contains(&ch)
}

/// True for letters and the vowel signs that attach to them; false for digits and the danda.
pub fn in_word(ch: char) -> bool {
    static WORD: OnceLock<Regex> = OnceLock::new();
    let word = WORD.get_or_init(|| Regex::new(r"^[\p{L}\p{Mn}\p{Mc}]$").unwrap());
    let mut buffer = [0u8; 4];
    word.is_match(ch.encode_utf8(&mut buffer))
}

/// Drop leading whitespace from each token's character range.
pub fn clean_offsets(text: &[char], offsets: &[(usize, usize)]) -> Vec<(usize, usize)> {
    offsets
        .iter()
        .map(|&(mut a, b)| {
            while a < b && text[a].is_whitespace() {
                a += 1;
            }
            (a, b)
        })
        .collect()
}

/// (prefix, label) for a tag such as "B-PERSON"; None for "O".
fn split_tag(tag: &str) -> Option<(char, &str)> {
    if tag == "O" {
        return None;
    }
    let mut chars = tag.chars();
    let first = chars.next().unwrap();
    if tag.len() > 2 && chars.next() == Some('-') {
        Some((first, &tag[2..]))
    } else {
        Some(('I', tag))
    }
}

/// Merge token tags into character spans. With `trims`, the end of each span is pulled
/// back by the trim of its last token.
pub fn decode(tags: &[&str], offsets: &[(usize, usize)], trims: Option<&[usize]>) -> Vec<Span> {
    let mut found: Vec<(usize, usize, &str, usize)> = Vec::new();
    let mut open = false;
    for (i, tag) in tags.iter().enumerate() {
        let (a, b) = offsets[i];
        let Some((prefix, label)) = split_tag(tag) else {
            open = false;
            continue;
        };
        if b <= a {
            open = false;
            continue;
        }
        // A token that starts where the next one starts is the word marker on its own: no characters.
        let marker = i + 1 < offsets.len() && offsets[i + 1].0 == a && a < offsets[i + 1].1;
        if open && !"BSU".contains(prefix) && found.last().unwrap().2 == label {
            if !marker {
                let last = found.last_mut().unwrap();
                last.1 = b;
                last.3 = i;
            }
        } else {
            found.push((a, if marker { a } else { b }, label, i));
            open = true;
        }
    }
    found
        .into_iter()
        .filter(|(a, b, _, _)| b > a)
        .map(|(a, mut b, label, last)| {
            if let Some(trims) = trims {
                if trims[last] > 0 {
                    b = (offsets[last].0 + 1).max(b.saturating_sub(trims[last]));
                }
            }
            (a, b, label.to_string())
        })
        .collect()
}

/// Move a span that starts inside a word back to the start of that word.
pub fn to_word_start(text: &[char], spans: &[Span]) -> Vec<Span> {
    let mut sorted = spans.to_vec();
    sorted.sort();
    let mut out: Vec<Span> = Vec::new();
    for (mut start, end, label) in sorted {
        let floor = out.last().map_or(0, |span| span.1);
        if in_word(text[start]) {
            while start > floor && in_word(text[start - 1]) {
                start -= 1;
            }
        }
        out.push((start, end, label));
    }
    out
}

/// Cut a name that is the same two or more words said twice into one span for each copy.
pub fn split_repeats(text: &[char], spans: &[Span]) -> Vec<Span> {
    let space = |ch: char| SPACE.contains(ch);
    let mut out = Vec::new();
    for (start, end, label) in spans {
        let (start, end) = (*start, *end);
        let mut words: Vec<(usize, usize)> = Vec::new();
        let mut at = start;
        while at < end {
            if space(text[at]) {
                at += 1;
                continue;
            }
            let mut stop = at;
            while stop < end && !space(text[stop]) {
                stop += 1;
            }
            words.push((at, stop));
            at = stop;
        }
        let n = words.len();
        let word = |k: usize| &text[words[k].0..words[k].1];
        let mut unit = 0;
        if NAMES.contains(&label.as_str()) {
            for size in 2..=n / 2 {
                if n % size == 0 && (size..n).all(|k| word(k) == word(k % size)) {
                    unit = size;
                    break;
                }
            }
        }
        if unit > 0 {
            for k in (0..n).step_by(unit) {
                out.push((words[k].0, words[k + unit - 1].1, label.clone()));
            }
        } else {
            out.push((start, end, label.clone()));
        }
    }
    out
}

/// False for a span that cannot be personal data of the kind its label names, nor of another kind.
pub fn plausible(value: &[char], label: &str) -> bool {
    let digits = value.iter().filter(|&&ch| is_digit(ch)).count();
    if NUMBERS.contains(&label) {
        return digits >= 4;
    }
    match label {
        "VEHICLE_PLATE" => digits >= 2 && value.iter().any(|&ch| in_word(ch)),
        "DATE" => digits > 0 && !(value.contains(&':') && value.iter().all(|&ch| is_digit(ch) || ch == ':')),
        _ => true,
    }
}

/// The spans of the tagger with repeated names cut apart and impossible ones dropped.
pub fn tidy(text: &[char], spans: &[Span]) -> Vec<Span> {
    split_repeats(text, spans).into_iter().filter(|(a, b, label)| plausible(&text[*a..*b], label)).collect()
}

/// Cut a text into the pieces the tagger reads one at a time.
pub fn segments(text: &[char], limit: usize, hard: usize) -> Vec<(usize, usize)> {
    let n = text.len();
    let space = |ch: char| SPACE.contains(ch);
    let mut cuts = vec![0];
    for (i, &ch) in text.iter().enumerate() {
        let sentence = SENTENCE_END.contains(ch) && i + 1 < n && space(text[i + 1]) && text[i + 1] != '\n';
        if (ch == '\n' || sentence) && i + 1 < n {
            cuts.push(i + 1);
        }
    }
    cuts.push(n);
    let mut atoms = Vec::new();
    for pair in cuts.windows(2) {
        let (mut start, end) = (pair[0], pair[1]);
        while end - start > hard {
            let mut cut = start + hard;
            while cut > start + hard / 2 && !space(text[cut]) {
                cut -= 1;
            }
            if !space(text[cut]) {
                cut = start + hard;
            }
            atoms.push((start, cut));
            start = cut;
        }
        atoms.push((start, end));
    }
    let mut out = Vec::new();
    let (mut start, mut end) = (0, 0);
    for (a, b) in atoms {
        if end > start && b - start > limit {
            out.push((start, end));
            start = a;
        }
        end = b;
    }
    if end > start {
        out.push((start, end));
    }
    out
}

/// Rule matches, plus every tagger span that touches none of them.
pub fn merge(tagger: &[Span], rules: &[Span]) -> Vec<Span> {
    let mut out: Vec<Span> = rules.to_vec();
    out.extend(tagger.iter().filter(|t| rules.iter().all(|r| t.1 <= r.0 || r.1 <= t.0)).cloned());
    out.sort();
    out
}

/// Replace each span with a numbered placeholder; equal text gets the same number.
pub fn redact(text: &[char], spans: &[Span]) -> String {
    let mut sorted = spans.to_vec();
    sorted.sort();
    let mut seen: Vec<(String, String)> = Vec::new();
    let mut out = String::new();
    let mut last = 0;
    for (start, end, label) in sorted {
        if start < last {
            continue;
        }
        let surface: String = text[start..end].iter().collect();
        if !seen.iter().any(|(l, s)| *l == label && *s == surface) {
            seen.push((label.clone(), surface.clone()));
        }
        let same: Vec<&(String, String)> = seen.iter().filter(|(l, _)| *l == label).collect();
        let number = same.iter().position(|(_, s)| *s == surface).unwrap() + 1;
        out.extend(text[last..start].iter());
        out.push_str(&format!("[{label}_{number}]"));
        last = end;
    }
    out.extend(text[last..].iter());
    out
}
