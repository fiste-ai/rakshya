//! What 1.0 split off from older labels, told by the words beside a span, and what each profile gives out.
//! See `rakshya/kinds.py`.
//!
//! The words and the patterns are not written here. They are read from `kinds.json`, which
//! `python -m rakshya.kinds --export wasm/kinds.json` writes, so this file holds only the
//! checks that the Python module makes in code.

use crate::Span;
use regex::Regex;
use serde::Deserialize;
use std::collections::HashMap;
use std::sync::OnceLock;

#[derive(Deserialize)]
struct Tables {
    cues: Vec<(String, Vec<String>)>,
    own: Vec<String>,
    mac: String,
    sentence_end: String,
    figures: String,
    month: String,
    birth: String,
    born_after: String,
    not_birth: String,
    stars: String,
    crosses: String,
    other_letter: String,
    maskable: Vec<String>,
    aliases: HashMap<String, String>,
    office: Vec<String>,
    personal: Vec<String>,
    finer: HashMap<String, Vec<String>>,
    whole: HashMap<String, Vec<String>>,
}

pub struct Kinds {
    /// The words that name a kind of number, in the order in which they are tried.
    cues: Vec<(String, Vec<Vec<char>>)>,
    own: Vec<String>,
    mac: Regex,
    sentence_end: Vec<char>,
    figures: Regex,
    month: Regex,
    birth: Regex,
    born_after: Regex,
    not_birth: Regex,
    stars: Regex,
    crosses: Regex,
    other_letter: Regex,
    maskable: Vec<String>,
    aliases: HashMap<String, String>,
    office: Vec<String>,
    personal: Vec<String>,
    /// The label of a model, and the labels of the rules that it refines: the match of the rules keeps its edges.
    pub finer: HashMap<String, Vec<String>>,
    /// The label of a model whose span stands whole, and what the rules may find inside it.
    pub whole: HashMap<String, Vec<String>>,
}

fn compile(pattern: &str) -> Regex {
    Regex::new(pattern).unwrap_or_else(|error| panic!("pattern not accepted: {error}"))
}

pub fn kinds() -> &'static Kinds {
    static KINDS: OnceLock<Kinds> = OnceLock::new();
    KINDS.get_or_init(|| {
        let t: Tables = serde_json::from_str(include_str!("../kinds.json")).expect("kinds.json");
        Kinds {
            cues: t.cues.into_iter().map(|(label, words)| (label, words.iter().map(|word| word.chars().collect()).collect())).collect(),
            own: t.own,
            mac: compile(&format!("^(?:{})$", t.mac)),
            sentence_end: t.sentence_end.chars().collect(),
            figures: compile(&t.figures),
            month: compile(&t.month),
            birth: compile(&t.birth),
            born_after: compile(&format!("^(?:{})", t.born_after)),
            not_birth: compile(&t.not_birth),
            stars: compile(&t.stars),
            crosses: compile(&t.crosses),
            other_letter: compile(&t.other_letter),
            maskable: t.maskable,
            aliases: t.aliases,
            office: t.office,
            personal: t.personal,
            finer: t.finer,
            whole: t.whole,
        }
    })
}

fn text_of(chars: &[char], start: usize, end: usize) -> String {
    chars[start..end].iter().collect()
}

/// The final name of a label.
pub fn canonical(label: &str) -> String {
    kinds().aliases.get(label).cloned().unwrap_or_else(|| label.to_string())
}

/// The final name of a label; whose a phone number or a mailbox is stays as it is said.
fn said(label: &str) -> String {
    let k = kinds();
    if k.office.iter().any(|l| l == label) || k.own.iter().any(|l| l == label) {
        label.to_string()
    } else {
        canonical(label)
    }
}

/// Whether a number or an e-mail address is written with a part of it masked.
pub fn masked(value: &str) -> bool {
    let k = kinds();
    k.stars.is_match(value) || (k.crosses.is_match(value) && !k.other_letter.is_match(value))
}

/// Where `needle` starts last in `hay` so that it ends at or before `end`, as `str.rfind(needle, 0, end)` gives it.
fn rfind(hay: &[char], needle: &[char], end: usize) -> Option<usize> {
    if needle.is_empty() || needle.len() > end {
        return None;
    }
    (0..=end - needle.len()).rev().find(|&at| hay[at..at + needle.len()] == *needle)
}

/// The nearest word before a span that names a kind, as (where it starts, the kind).
fn nearest_cue(chars: &[char], start: usize) -> Option<(usize, &'static str)> {
    let k = kinds();
    let base = start.saturating_sub(48);
    let before: Vec<char> = text_of(chars, base, start).to_lowercase().chars().collect();
    let mut best: Option<(usize, &'static str)> = None;
    for (label, words) in &k.cues {
        for cue in words {
            let mut at = rfind(&before, cue, before.len());
            // A cue in Latin letters counts at the start of a word only: "ration" is not in "registration".
            while let Some(found) = at {
                if found > 0 && cue[0].is_ascii() && before[found - 1].is_ascii_alphabetic() {
                    at = rfind(&before, cue, found);
                } else {
                    break;
                }
            }
            if let Some(found) = at {
                if best.map_or(true, |(nearest, _)| found > nearest) {
                    best = Some((found, label.as_str()));
                }
            }
        }
    }
    best.map(|(found, label)| (base + found, label))
}

/// Whether a date has at least two of day, month and year.
fn enough(value: &str) -> bool {
    let k = kinds();
    k.figures.find_iter(value).count() + usize::from(k.month.is_match(value)) >= 2
}

/// A Latin letter, a figure or an underscore: what must not stand against a Latin word for birth.
fn word_like(ch: char) -> bool {
    ch.is_ascii_alphanumeric() || ch == '_'
}

/// The last word for birth in the 48 characters before `start`, as the place where it ends.
fn birth_cue(chars: &[char], start: usize) -> Option<usize> {
    let k = kinds();
    let base = start.saturating_sub(48);
    let window = text_of(chars, base, start);
    let mut found = None;
    for caps in k.birth.captures_iter(&window) {
        let whole = caps.get(0).unwrap();
        let a = base + window[..whole.start()].chars().count();
        let mut b = base + window[..whole.end()].chars().count();
        if caps.name("word").is_some() {
            if (a > 0 && word_like(chars[a - 1])) || (b < start && word_like(chars[b])) {
                continue;
            }
            if b < start && chars[b] == '.' {
                b += 1; // "D.O.B."
            }
        } else if caps.name("stem").is_some() && b < start && ('\u{0900}'..='\u{097f}').contains(&chars[b]) {
            continue;
        }
        found = Some(b);
    }
    found
}

/// Whether the date at [start, end) is given as a date of birth. `others` are the other spans of the text.
fn of_birth(chars: &[char], start: usize, end: usize, others: &[&Span]) -> bool {
    let k = kinds();
    if !enough(&text_of(chars, start, end)) {
        return false;
    }
    if k.born_after.is_match(&text_of(chars, end, (end + 30).min(chars.len()))) {
        return true;
    }
    let Some(cue) = birth_cue(chars, start) else {
        return false;
    };
    let gap = text_of(chars, cue, start);
    let between: Vec<&str> = others.iter().filter(|o| cue <= o.0 && o.0 < start).map(|o| o.2.as_str()).collect();
    // A place may stand between ("born in Dharan on ..."); another date or a number makes this one something else,
    // and so do more words than name the date.
    let most = if between.is_empty() { 24 } else { 40 };
    if start - cue > most || gap.chars().any(|ch| k.sentence_end.contains(&ch)) || k.not_birth.is_match(&gap) {
        return false;
    }
    between.iter().all(|label| *label == "LOCATION")
}

/// The spans with a number under its kind and a date of birth as one, where the words beside them tell.
/// This is `retype` of the Python module with the places where a person lives left as they are.
fn retyped(chars: &[char], spans: &[Span]) -> Vec<Span> {
    let k = kinds();
    let mut list: Vec<Span> = spans.iter().map(|(start, end, label)| (*start, *end, said(label))).collect();
    list.sort();
    let mut out: Vec<Span> = Vec::with_capacity(list.len());
    for (start, end, label) in &list {
        let mut new = label.clone();
        if label == "ID_NUMBER" {
            let cue = nearest_cue(chars, *start);
            if k.mac.is_match(&text_of(chars, *start, *end)) {
                new = "DIGITAL_SECRET".to_string();
            } else if let Some((at, kind)) = cue {
                if !chars[at.min(*start)..*start].iter().any(|ch| k.sentence_end.contains(ch)) {
                    new = kind.to_string();
                }
            }
        } else if label == "DATE" {
            let others: Vec<&Span> = list.iter().filter(|o| o.0 != *start).collect();
            if of_birth(chars, *start, *end, &others) {
                new = "DOB".to_string();
            }
        }
        out.push((*start, *end, new));
    }
    out.sort();
    out
}

/// Spans as they leave the code where every label is asked for: under the final names.
pub fn all(chars: &[char], spans: &[Span]) -> Vec<Span> {
    retyped(chars, spans).into_iter().map(|(start, end, label)| (start, end, canonical(&label))).collect()
}

/// What the profile "personal" gives out: personal data only, without the phone number and the mailbox of an
/// office and without a number that is already masked.
pub fn personal(chars: &[char], spans: &[Span]) -> Vec<Span> {
    let k = kinds();
    let own: Vec<Span> = spans.iter().filter(|span| !k.office.contains(&span.2)).cloned().collect();
    all(chars, &own)
        .into_iter()
        .filter(|(start, end, label)| {
            k.personal.contains(label) && !(k.maskable.contains(label) && masked(&text_of(chars, *start, *end)))
        })
        .collect()
}
