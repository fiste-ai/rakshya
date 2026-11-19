//! Character spans from token tags. See `rakshya/spans.py`.

use crate::Span;
use regex::Regex;
use std::sync::OnceLock;

pub const SENTENCE_END: &str = "।?!";
pub const SPACE: &str = " \t\r\n\u{a0}";
const LOST: usize = 4;
const HYPHENS: &str = "-\u{2010}\u{2011}\u{2012}\u{2013}\u{2014}\u{2015}\u{2212}";
const NAMES: [&str; 3] = ["PERSON", "LOCATION", "ORGANIZATION"];
/// Numbers that have four digits or more, whatever their kind, under their final and their older names.
#[rustfmt::skip]
const NUMBERS: [&str; 13] = [
    "NATIONAL_ID", "TAX_ID", "PASSPORT", "DRIVER_LICENSE", "VOTER_ID", "BANK_ACCOUNT", "CREDIT_CARD", "PHONE",
    "CITIZENSHIP_NO", "PASSPORT_NO", "LICENSE_NO", "CARD_NUMBER", "OFFICE_PHONE",
];
/// Release 0.1 called the tax number PAN. A model that still does is read under the new name.
const ALIASES: [(&str, &str); 1] = [("PAN", "TAX_ID")];

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

/// For each tag, the tags that may stand before it: a tag that continues a span follows only a tag of its label.
pub fn follows(tags: &[String]) -> Vec<Vec<usize>> {
    let parts: Vec<Option<(char, &str)>> = tags.iter().map(|tag| split_tag(tag)).collect();
    parts
        .iter()
        .map(|part| match part {
            Some((prefix, label)) if !"BSU".contains(*prefix) => {
                (0..tags.len()).filter(|&i| matches!(parts[i], Some((_, before)) if before == *label)).collect()
            }
            _ => (0..tags.len()).collect(),
        })
        .collect()
}

/// The tags of a piece that fit together: the best sequence in which I-X follows only B-X or I-X.
///
/// `scores` holds for every token one score for each tag, row after row, as the model gives them. A token
/// without characters gets "O" and ends a stretch, and the first token of a stretch may take any tag. Where
/// two tags give one sum, the one earlier in `tags` is taken. The sums are made in 64-bit floats, token after
/// token, as `fit_tags` in `rakshya/spans.py` makes them.
pub fn fit_tags(scores: &[f32], offsets: &[(usize, usize)], tags: &[String]) -> Vec<usize> {
    let width = tags.len();
    let before = follows(tags);
    let nothing = tags.iter().position(|tag| tag == "O").unwrap_or(0);
    let mut out = vec![nothing; offsets.len()];
    let mut t = 0;
    while t < offsets.len() {
        if offsets[t].1 <= offsets[t].0 {
            t += 1;
            continue;
        }
        let start = t;
        while t < offsets.len() && offsets[t].1 > offsets[t].0 {
            t += 1;
        }
        let mut best: Vec<f64> = scores[start * width..(start + 1) * width].iter().map(|&x| f64::from(x)).collect();
        let mut back: Vec<Vec<usize>> = Vec::with_capacity(t - start);
        for s in start + 1..t {
            let row = &scores[s * width..(s + 1) * width];
            let mut from = vec![0; width];
            let mut next = vec![0.0; width];
            for j in 0..width {
                let mut at = before[j][0];
                for &i in &before[j][1..] {
                    if best[i] > best[at] {
                        at = i;
                    }
                }
                from[j] = at;
                next[j] = best[at] + f64::from(row[j]);
            }
            back.push(from);
            best = next;
        }
        let mut k = 0;
        for i in 1..width {
            if best[i] > best[k] {
                k = i;
            }
        }
        for s in (start + 1..t).rev() {
            out[s] = k;
            k = back[s - start - 1][k];
        }
        out[start] = k;
    }
    out
}

/// Move a span that starts inside a word back to the start of that word.
pub fn to_word_start(text: &[char], spans: &[Span]) -> Vec<Span> {
    let mut sorted = spans.to_vec();
    sorted.sort();
    let mut out: Vec<Span> = Vec::new();
    for (mut start, end, label) in sorted {
        let floor = out.last().map_or(0, |span| span.1);
        if in_word(text[start]) {
            let mut first = start;
            while first > floor && in_word(text[first - 1]) {
                first -= 1;
            }
            // more than a lost piece: another word that the page ran against the name
            if start - first <= LOST {
                start = first;
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

/// Cut a name or a date that runs over a line break into one span for each line.
pub fn split_lines(text: &[char], spans: &[Span]) -> Vec<Span> {
    let space = |ch: char| SPACE.contains(ch);
    let mut out = Vec::new();
    for (start, end, label) in spans {
        let (start, end) = (*start, *end);
        let named = NAMES.contains(&label.as_str()) || label == "DATE";
        if !named || !text[start..end].contains(&'\n') {
            out.push((start, end, label.clone()));
            continue;
        }
        let mut at = start;
        while at <= end {
            let mut stop = at;
            while stop < end && text[stop] != '\n' {
                stop += 1;
            }
            let (mut a, mut b) = (at, stop);
            while a < b && space(text[a]) {
                a += 1;
            }
            while b > a && space(text[b - 1]) {
                b -= 1;
            }
            if b > a {
                out.push((a, b, label.clone()));
            }
            at = stop + 1;
        }
    }
    out
}

/// Four digits that begin with 19 or 20, in Latin or Devanagari digits.
fn is_year(value: &[char]) -> bool {
    value.len() == 4
        && value.iter().all(|&ch| is_digit(ch))
        && "1१2२".contains(value[0])
        && "9९0०".contains(value[1])
        && "1१".contains(value[0]) == "9९".contains(value[1])
}

/// Cut a date that is two years joined by a hyphen into the two years.
pub fn split_ranges(text: &[char], spans: &[Span]) -> Vec<Span> {
    let space = |ch: char| SPACE.contains(ch);
    let mut out = Vec::new();
    for (start, end, label) in spans {
        let (start, end) = (*start, *end);
        let value = &text[start..end];
        let mut two = false;
        if label == "DATE" && value.len() >= 9 && is_year(&value[..4]) && is_year(&value[value.len() - 4..]) {
            let (mut a, mut b) = (4, value.len() - 4);
            while a < b && space(value[a]) {
                a += 1;
            }
            while b > a && space(value[b - 1]) {
                b -= 1;
            }
            two = b - a == 1 && HYPHENS.contains(value[a]);
        }
        if two {
            out.push((start, start + 4, label.clone()));
            out.push((end - 4, end, label.clone()));
        } else {
            out.push((start, end, label.clone()));
        }
    }
    out
}

/// True when four numbers stand joined by dots in `value`, the two inner ones of at most three digits.
pub fn four_numbers(value: &[char]) -> bool {
    let mut lengths: Vec<usize> = Vec::new();
    let mut digits = 0;
    for ch in value.iter().copied().chain(std::iter::once(' ')) {
        if is_digit(ch) {
            digits += 1;
        } else if ch == '.' && digits > 0 {
            lengths.push(digits);
            digits = 0;
        } else {
            if digits > 0 {
                lengths.push(digits);
            }
            if lengths.len() >= 4 && (0..lengths.len() - 3).any(|k| lengths[k + 1] <= 3 && lengths[k + 2] <= 3) {
                return true;
            }
            lengths.clear();
            digits = 0;
        }
    }
    false
}

/// How many words a value has: its stretches without white space.
pub fn words(value: &[char]) -> usize {
    let (mut count, mut inside) = (0, false);
    for &ch in value {
        if SPACE.contains(ch) {
            inside = false;
        } else if !inside {
            count += 1;
            inside = true;
        }
    }
    count
}

/// False for a span that cannot be personal data of the kind its label names, nor of another kind.
/// See `plausible` in `rakshya/spans.py` for what passes without a figure and in figures alone.
pub fn plausible(value: &[char], label: &str) -> bool {
    let digits = value.iter().filter(|&&ch| is_digit(ch)).count();
    let worded = digits == 0 && words(value) >= 4;
    if NUMBERS.contains(&label) {
        return digits >= 4 || worded;
    }
    let colons = value.iter().filter(|&&ch| ch == ':').count();
    match label {
        "VEHICLE_PLATE" | "VEHICLE_ID" => digits >= 2 && value.iter().any(|&ch| in_word(ch)),
        "DATE" | "DOB" => {
            if digits == 0 {
                words(value) >= 2
            } else {
                !(value.contains(&':') && value.iter().all(|&ch| is_digit(ch) || ch == ':'))
            }
        }
        "ID_NUMBER" | "MEDICAL_ID" | "EMPLOYEE_STUDENT_ID" | "PROPERTY_UTILITY_ID" => digits >= 2 || worded,
        "IP_ADDRESS" => digits > 0 && (four_numbers(value) || colons >= 2),
        "UPI_ID" => value.contains(&'@'),
        "SECRET" | "USERNAME" | "PAYMENT_ID" => value.len() >= 3,
        // One label of 1.0 for what was three. Figures alone are a code or the number of a device. Figures with
        // dots or colons are held to the form of an address of a machine, as before; anything else to the length
        // of a password or a user name.
        "DIGITAL_SECRET" => {
            if digits == value.len() {
                digits >= 3
            } else if value.iter().all(|&ch| is_digit(ch) || ch == '.' || ch == ':') {
                digits > 0 && (four_numbers(value) || colons >= 2)
            } else {
                value.len() >= 3
            }
        }
        _ => true,
    }
}

/// The spans of the tagger with repeated names, names over a line break and two years cut apart, and impossible ones dropped.
/// A vowel sign, a virama, a nukta or another sign that is written on the letter before it.
pub fn is_mark(ch: char) -> bool {
    static MARK: OnceLock<Regex> = OnceLock::new();
    let mark = MARK.get_or_init(|| Regex::new(r"^[\p{Mn}\p{Mc}]$").unwrap());
    let mut buffer = [0u8; 4];
    mark.is_match(ch.encode_utf8(&mut buffer))
}

/// Move an edge that cuts a letter in two. See `whole_letters` in `rakshya/spans.py`.
pub fn whole_letters(text: &[char], spans: &[Span]) -> Vec<Span> {
    let mut out = Vec::new();
    for (start, end, label) in spans {
        let (mut start, mut end) = (*start, *end);
        while end < text.len() && is_mark(text[end]) && text[end] != '\u{903}' {
            end += 1;
        }
        while start < end && is_mark(text[start]) {
            start += 1;
        }
        if start < end {
            out.push((start, end, label.clone()));
        }
    }
    out
}

/// One span for an organisation and its short form in brackets. See `join_short_forms` in `rakshya/spans.py`.
pub fn join_short_forms(text: &[char], spans: &[Span]) -> Vec<Span> {
    let blank = |ch: char| ch == ' ' || ch == '\u{a0}';
    let mut sorted: Vec<Span> = spans.to_vec();
    sorted.sort();
    let mut out: Vec<Span> = Vec::new();
    for (start, end, label) in sorted {
        if let Some(last) = out.last_mut() {
            if label == "ORGANIZATION" && last.2 == "ORGANIZATION" && last.1 <= start {
                let gap: Vec<char> = text[last.1..start].iter().copied().filter(|ch| !blank(*ch)).collect();
                let mut close = end;
                while close < text.len() && blank(text[close]) {
                    close += 1;
                }
                let one_word = !text[start..end].iter().any(|ch| SPACE.contains(*ch));
                if gap == ['('] && close < text.len() && text[close] == ')' && one_word {
                    last.1 = close + 1;
                    continue;
                }
            }
        }
        out.push((start, end, label));
    }
    out
}

const BLANK: &str = " \t\u{a0}";
/// Before a hyphen these are the first half of one name, not a place of their own.
const HALVES: [&str; 16] = [
    "sub", "उप", "जम्मू", "jammu", "टिमोर", "timor", "गिनी", "guinea", "बोस्निया", "bosnia", "अंडमान", "andaman", "दमन", "daman",
    "दादरा", "dadra",
];
const ROADS: [&str; 12] = [
    "राजमार्ग", "सडक", "सडकखण्ड", "लोकमार्ग", "द्रुतमार्ग", "रेलमार्ग", "कोरिडोर", "expressway", "highway", "road", "corridor", "railway",
];

/// Where the last word of text[start..end] begins.
fn last_word(text: &[char], start: usize, end: usize) -> usize {
    let mut at = end;
    while at > start && !SPACE.contains(text[at - 1]) {
        at -= 1;
    }
    at
}

fn lower(text: &[char], start: usize, end: usize) -> String {
    text[start..end].iter().collect::<String>().to_lowercase()
}

/// Cut a place span at the hyphens that join places. See `split_places` in `rakshya/spans.py`.
pub fn split_places(text: &[char], spans: &[Span]) -> Vec<Span> {
    let mut out = Vec::new();
    for (start, end, label) in spans {
        let (start, end) = (*start, *end);
        let mut parts: Vec<(usize, usize)> = Vec::new();
        let (mut at, mut i) = (start, start);
        while label == "LOCATION" && i < end {
            if HYPHENS.contains(text[i]) {
                let (mut a, mut b) = (i, i + 1);
                while a > at && BLANK.contains(text[a - 1]) {
                    a -= 1;
                }
                while b < end && BLANK.contains(text[b]) {
                    b += 1;
                }
                parts.push((at, a));
                at = b;
                i = b;
            } else {
                i += 1;
            }
        }
        parts.push((at, end));
        let alone = parts.iter().all(|&(a, b)| b >= a + 3 && !is_digit(text[a]) && !text[a].is_ascii_lowercase());
        let first = &parts[..parts.len() - 1];
        if parts.len() == 1 || !alone || first.iter().any(|&(a, b)| HALVES.contains(&lower(text, last_word(text, a, b), b).as_str())) {
            out.push((start, end, label.clone()));
            continue;
        }
        // Where the last place ends in the word for a road, the road is named by its ends and the word stays outside.
        let (a, mut b) = parts[parts.len() - 1];
        let mut word = last_word(text, a, b);
        if word > a && ROADS.contains(&lower(text, word, b).as_str()) {
            b = word;
            while b > a && SPACE.contains(text[b - 1]) {
                b -= 1;
            }
            word = last_word(text, a, b);
            if word > a && ["राष्ट्रीय", "national"].contains(&lower(text, word, b).as_str()) {
                b = word;
                while b > a && SPACE.contains(text[b - 1]) {
                    b -= 1;
                }
            }
            let last = parts.len() - 1;
            parts[last] = (a, b);
        }
        for (a, b) in parts {
            out.push((a, b, label.clone()));
        }
    }
    out
}

/// What stands before the name of a person and is no part of it, and the particle of respect after it.
const TITLES: [&str; 16] = [
    "श्रीमती", "सुश्री", "श्री", "डा.", "डा", "डॉ.", "डॉ", "प्रा.", "प्रो.", "Dr.", "Dr", "Prof.", "Er.", "Mr.", "Mrs.", "Ms.",
];
const RESPECT: [&str; 2] = ["जी", "ज्यू"];

/// Where the name of a person begins after the titles that stand before it. Two characters of the name are left.
fn without_titles(text: &[char], mut start: usize, end: usize) -> usize {
    'again: loop {
        for title in TITLES {
            let word: Vec<char> = title.chars().collect();
            let mut stop = start + word.len();
            if stop < end && text[start..stop] == word[..] && (SPACE.contains(text[stop]) || title.ends_with('.')) {
                while stop < end && SPACE.contains(text[stop]) {
                    stop += 1;
                }
                if end - stop >= 2 {
                    start = stop;
                    continue 'again;
                }
            }
        }
        return start;
    }
}

/// Leave out what stands at the edge of a span and is never part of it. See `trim_edges` in `rakshya/spans.py`.
/// The labels of numbers, beside `NUMBERS`, that never begin or end with half a pair of brackets.
const OF_NUMBERS: [&str; 6] = ["ID_NUMBER", "MEDICAL_ID", "EMPLOYEE_STUDENT_ID", "PROPERTY_UTILITY_ID", "VEHICLE_ID", "VEHICLE_PLATE"];

/// A span without the round bracket at its edge that does not close inside it, or was not opened inside it.
/// See `without_stray_bracket` in `rakshya/spans.py`.
pub fn without_stray_bracket(text: &[char], start: usize, end: usize) -> (usize, usize) {
    let value = &text[start..end];
    if value.first() == Some(&'(') && !value.contains(&')') {
        (start + 1, end)
    } else if value.last() == Some(&')') && !value.contains(&'(') {
        (start, end - 1)
    } else {
        (start, end)
    }
}

pub fn trim_edges(text: &[char], spans: &[Span]) -> Vec<Span> {
    let mut out = Vec::new();
    for (start, end, label) in spans {
        let (mut start, mut end) = (*start, *end);
        if label == "PHONE" || label == "OFFICE_PHONE" {
            // Eleven or twelve figures that begin as a mobile number of Nepal are the number and the next cell.
            let value: String = text[start..end].iter().collect();
            if (end - start == 11 || end - start == 12) && crate::rules::mobile_with_more(&value) {
                end = start + 10;
            }
            while start < end && (text[start] == '/' || text[start] == ' ' || text[start] == '\u{a0}') {
                start += 1;
            }
            (start, end) = without_stray_bracket(text, start, end);
        } else if NUMBERS.contains(&label.as_str()) || OF_NUMBERS.contains(&label.as_str()) {
            (start, end) = without_stray_bracket(text, start, end);
        } else if NAMES.contains(&label.as_str()) || label == "DATE" {
            if label == "PERSON" {
                start = without_titles(text, start, end);
                for word in RESPECT {
                    let chars: Vec<char> = word.chars().collect();
                    if end >= start + chars.len() + 3 {
                        let cut = end - chars.len() - 1;
                        if text[cut + 1..end] == chars[..] && (text[cut] == ' ' || text[cut] == '\u{a0}') {
                            end = cut;
                            break;
                        }
                    }
                }
            }
            let value = &text[start..end];
            if value.first() == Some(&'(') && !value.contains(&')') {
                start += 1;
            } else if value.last() == Some(&')') && !value.contains(&'(') {
                end -= 1;
            }
            while start < end && SPACE.contains(text[start]) {
                start += 1;
            }
            while end > start && SPACE.contains(text[end - 1]) {
                end -= 1;
            }
        }
        if start < end {
            out.push((start, end, label.clone()));
        }
    }
    out
}

pub fn tidy(text: &[char], spans: &[Span]) -> Vec<Span> {
    let cut = whole_letters(text, &split_places(text, &split_ranges(text, &split_lines(text, &split_repeats(text, spans)))));
    let kept: Vec<Span> = cut.into_iter().filter(|(a, b, label)| plausible(&text[*a..*b], label)).collect();
    join_short_forms(text, &trim_edges(text, &kept))
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
///
/// A model of 1.0 knows more than the rules in two ways (`whole` and `finer` of `kinds.json`). Where its span holds
/// everything that the rules find there, and what they find is what such a span may hold, its span stands and
/// theirs go. Else, where it gives the finer label for what the rules have by its form, the match of the rules
/// keeps its edges and takes the label of the model.
pub fn merge(tagger: &[Span], rules: &[Span]) -> Vec<Span> {
    let kinds = crate::kinds::kinds();
    let allowed = |table: &std::collections::HashMap<String, Vec<String>>, mine: &str, theirs: &str| {
        table.get(mine).map_or(false, |of| of.iter().any(|label| label == theirs))
    };
    let mut rules: Vec<Span> = rules.to_vec();
    let mut gone = vec![false; rules.len()];
    let mut kept: Vec<Span> = Vec::new();
    for t in tagger {
        let touching: Vec<usize> = (0..rules.len()).filter(|&k| !(t.1 <= rules[k].0 || rules[k].1 <= t.0)).collect();
        if touching.is_empty() {
            kept.push(t.clone());
        } else if touching.iter().all(|&k| t.0 <= rules[k].0 && rules[k].1 <= t.1 && allowed(&kinds.whole, &t.2, &rules[k].2)) {
            kept.push(t.clone());
            for &k in &touching {
                gone[k] = true;
            }
        } else if touching.iter().all(|&k| allowed(&kinds.finer, &t.2, &rules[k].2)) {
            for &k in &touching {
                rules[k].2 = t.2.clone();
            }
        }
    }
    let mut out: Vec<Span> = rules.into_iter().zip(gone).filter(|(_, gone)| !gone).map(|(rule, _)| rule).collect();
    out.extend(kept);
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

/// The current name of a label.
pub fn canonical(label: &str) -> &str {
    ALIASES.iter().find(|(old, _)| *old == label).map_or(label, |(_, new)| new)
}

/// The tags of a model with these labels. A label under an old name is read under its current one.
pub fn tag_names(labels: &[String]) -> Vec<String> {
    let mut tags = vec!["O".to_string()];
    for label in labels {
        let label = canonical(label);
        tags.push(format!("B-{label}"));
        tags.push(format!("I-{label}"));
    }
    tags
}
