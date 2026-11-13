//! Rule-based recognizers for identifiers as they are written in Nepal. See `gopya/rules.py`.
//!
//! The patterns are not written here. They are read from `rules.json`, which
//! `python -m gopya.rules --export wasm/rules.json` writes, so this file holds only the
//! checks that the Python module makes in code.

use crate::Span;
use regex::{Captures, Regex};
use serde::Deserialize;
use std::collections::HashMap;
use std::sync::OnceLock;

#[derive(Deserialize)]
struct Fold {
    digits: String,
    hyphens: String,
    spaces: String,
}

#[derive(Deserialize)]
struct Tables {
    fold: Fold,
    strong: Vec<(String, String)>,
    weak: Vec<(String, String)>,
    any_keyword: String,
    after_year: String,
    phone_gated: String,
    mobile: String,
    mobile_prefix: String,
    fixed_line: String,
    landline_intl: String,
    landline: String,
    email: String,
    license_shape: String,
    numeric_dates: Vec<(String, String)>,
    date_gated: String,
    word_dates: Vec<String>,
    day_month: String,
    month_suffix: String,
    plates: Vec<String>,
}

struct Rules {
    fold: HashMap<char, char>,
    marks: HashMap<char, char>,
    strong: Vec<(String, Regex)>,
    weak: Vec<(String, Regex)>,
    any_keyword: Regex,
    after_year: Regex,
    phone_gated: Regex,
    mobile: Regex,
    mobile_prefix: Regex,
    fixed_line: Regex,
    landlines: [Regex; 2],
    email: Regex,
    license_shape: Regex,
    numeric_dates: Vec<(Regex, bool)>,
    date_gated: Regex,
    word_dates: Vec<Regex>,
    day_month: Regex,
    month_suffix: Regex,
    plates: Vec<Regex>,
}

fn compile(pattern: &str) -> Regex {
    Regex::new(pattern).unwrap_or_else(|error| panic!("pattern not accepted: {error}"))
}

/// A pattern that must match from the first character, as `re.match` does.
fn at_start(pattern: &str) -> Regex {
    compile(&format!("^(?:{pattern})"))
}

/// A pattern that must match the whole text, as `re.fullmatch` does.
fn whole(pattern: &str) -> Regex {
    compile(&format!("^(?:{pattern})$"))
}

fn rules() -> &'static Rules {
    static RULES: OnceLock<Rules> = OnceLock::new();
    RULES.get_or_init(|| {
        let t: Tables = serde_json::from_str(include_str!("../rules.json")).expect("rules.json");
        let mut marks = HashMap::new();
        for ch in t.fold.hyphens.chars() {
            marks.insert(ch, '-');
        }
        for ch in t.fold.spaces.chars() {
            marks.insert(ch, ' ');
        }
        let mut fold = marks.clone();
        for (i, digit) in t.fold.digits.chars().enumerate() {
            fold.insert(digit, char::from_digit(i as u32, 10).unwrap());
        }
        let pairs = |list: &[(String, String)]| list.iter().map(|(label, p)| (label.clone(), compile(p))).collect();
        Rules {
            fold,
            marks,
            strong: pairs(&t.strong),
            weak: pairs(&t.weak),
            any_keyword: compile(&t.any_keyword),
            after_year: at_start(&t.after_year),
            phone_gated: compile(&t.phone_gated),
            mobile: compile(&t.mobile),
            mobile_prefix: at_start(&t.mobile_prefix),
            fixed_line: whole(&t.fixed_line),
            landlines: [compile(&t.landline_intl), compile(&t.landline)],
            email: compile(&t.email),
            license_shape: compile(&t.license_shape),
            numeric_dates: t.numeric_dates.iter().map(|(p, order)| (compile(p), order == "dmy")).collect(),
            date_gated: compile(&t.date_gated),
            word_dates: t.word_dates.iter().map(|p| compile(p)).collect(),
            day_month: compile(&t.day_month),
            month_suffix: whole(&t.month_suffix),
            plates: t.plates.iter().map(|p| compile(p)).collect(),
        }
    })
}

/// The folded text with the tables that turn the byte offsets of a match into character offsets.
struct Text {
    utf8: String,
    chars: Vec<char>,
    index: Vec<usize>,
    bytes: Vec<usize>,
}

impl Text {
    /// With `digits`, Devanagari digits become Latin ones; without, only hyphens and spaces are folded.
    fn new(text: &str, digits: bool) -> Text {
        let fold = if digits { &rules().fold } else { &rules().marks };
        let chars: Vec<char> = text.chars().map(|ch| *fold.get(&ch).unwrap_or(&ch)).collect();
        let utf8: String = chars.iter().collect();
        let mut index = vec![0; utf8.len() + 1];
        let mut bytes = Vec::with_capacity(chars.len() + 1);
        for (i, (byte, _)) in utf8.char_indices().enumerate() {
            index[byte] = i;
            bytes.push(byte);
        }
        index[utf8.len()] = chars.len();
        bytes.push(utf8.len());
        Text { utf8, chars, index, bytes }
    }

    /// Characters `start..end` as a slice of the text.
    fn slice(&self, start: usize, end: usize) -> &str {
        &self.utf8[self.bytes[start]..self.bytes[end.min(self.chars.len())]]
    }

    fn range(&self, m: regex::Match) -> (usize, usize) {
        (self.index[m.start()], self.index[m.end()])
    }

    fn at(&self, i: usize) -> char {
        self.chars.get(i).copied().unwrap_or(' ')
    }
}

type Candidate = (usize, usize, &'static str, (u8, usize));

fn digit(ch: char) -> bool {
    ch.is_ascii_digit()
}

fn letter(ch: char) -> bool {
    ch.is_ascii_alphabetic()
}

fn digits(value: &str) -> usize {
    value.chars().filter(|&ch| digit(ch)).count()
}

fn number(caps: &Captures, name: &str, default: i64) -> i64 {
    caps.name(name).map_or(default, |m| m.as_str().parse().unwrap_or(default))
}

/// True when the number at start..end is not a piece of a longer number.
fn alone(t: &Text, start: usize, end: usize) -> bool {
    let n = t.chars.len();
    let before = if start > 0 { t.chars[start - 1] } else { ' ' };
    let after = if end < n { t.chars[end] } else { ' ' };
    if digit(before) || digit(after) {
        return false;
    }
    if (after == '-' || after == '/') && end + 1 < n && digit(t.chars[end + 1]) {
        return false;
    }
    if (before == '-' || before == '/') && start > 1 && digit(t.chars[start - 2]) {
        return false;
    }
    true
}

/// True when the match does not begin inside a word of its own script.
fn word_start(t: &Text, start: usize, latin: bool) -> bool {
    if start == 0 {
        return true;
    }
    let before = t.chars[start - 1];
    if latin {
        !letter(before)
    } else {
        !('\u{900}'..='\u{97f}').contains(&before)
    }
}

/// The Devanagari letters and signs that follow position `end` without a break.
fn rest_of_word(t: &Text, end: usize) -> &str {
    let mut stop = end;
    while stop < t.chars.len() && ('\u{900}'..='\u{97f}').contains(&t.chars[stop]) && !"।॥".contains(t.chars[stop]) {
        stop += 1;
    }
    t.slice(end, stop)
}

fn plausible_date(year: i64, a: i64, b: i64, day_first: bool) -> bool {
    let month_first = (1..=12).contains(&a) && (1..=32).contains(&b);
    (1900..=2099).contains(&year) && (month_first || (day_first && (1..=12).contains(&b) && (1..=32).contains(&a)))
}

fn label_of(name: &str) -> &'static str {
    const LABELS: [&str; 7] =
        ["CITIZENSHIP_NO", "NATIONAL_ID", "PAN", "PASSPORT_NO", "LICENSE_NO", "VOTER_ID", "BANK_ACCOUNT"];
    LABELS.iter().copied().find(|label| *label == name).unwrap_or_else(|| panic!("label {name} is not known"))
}

fn ids(t: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    for (strong, table) in [(true, &r.strong), (false, &r.weak)] {
        for (name, pattern) in table {
            let label = label_of(name);
            for caps in pattern.captures_iter(&t.utf8) {
                let value = caps.name("val").unwrap();
                let gap = caps.name("gap").unwrap().as_str();
                let (start, end) = t.range(value);
                if !alone(t, start, end) || r.any_keyword.is_match(gap) {
                    continue;
                }
                if label == "CITIZENSHIP_NO" {
                    let count = digits(value.as_str());
                    if count < (if strong { 4 } else { 5 }) || count > 17 {
                        continue;
                    }
                    if !strong && r.after_year.is_match(t.slice(end, end + 5)) {
                        continue;
                    }
                }
                if end < t.chars.len() && letter(t.chars[end]) {
                    continue;
                }
                out.push((start, end, label, (if strong { 0 } else { 1 }, gap.chars().count())));
            }
        }
    }
}

fn phones(t: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    for caps in r.mobile.captures_iter(&t.utf8) {
        let number = caps.name("n").unwrap();
        let end = t.index[caps.get(0).unwrap().end()];
        let start = t.index[caps.name("cc").unwrap_or(number).start()];
        let text = number.as_str();
        if alone(t, start, end)
            && r.mobile_prefix.is_match(text)
            && text.chars().count() - digits(text) <= 3
            && !(start > 0 && t.chars[start - 1] == '+')
        {
            out.push((start, end, "PHONE", (2, 0)));
        }
    }
    for pattern in &r.landlines {
        for caps in pattern.captures_iter(&t.utf8) {
            let (start, end) = t.range(caps.get(0).unwrap());
            let joined = format!("{}{}", &caps["area"], &caps["rest"]);
            if alone(t, start, end) && r.fixed_line.is_match(&joined) {
                out.push((start, end, "PHONE", (2, 0)));
            }
        }
    }
    for caps in r.phone_gated.captures_iter(&t.utf8) {
        let (start, end) = t.range(caps.name("val").unwrap());
        let gap = caps.name("gap").unwrap().as_str();
        if alone(t, start, end) && !r.any_keyword.is_match(gap) {
            out.push((start, end, "PHONE", (2, gap.chars().count())));
        }
    }
}

fn dates(t: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    for (pattern, day_first) in &r.numeric_dates {
        for caps in pattern.captures_iter(&t.utf8) {
            let (start, end) = t.range(caps.get(0).unwrap());
            if caps["s1"] == caps["s2"]
                && alone(t, start, end)
                && plausible_date(number(&caps, "y", 0), number(&caps, "a", 0), number(&caps, "b", 0), *day_first)
            {
                out.push((start, end, "DATE", (4, 0)));
            }
        }
    }
    for caps in r.date_gated.captures_iter(&t.utf8) {
        let (start, end) = t.range(caps.name("val").unwrap());
        if alone(t, start, end) {
            out.push((start, end, "DATE", (3, caps.name("gap").unwrap().as_str().chars().count())));
        }
    }
    for pattern in &r.word_dates {
        for caps in pattern.captures_iter(&t.utf8) {
            let (start, end) = t.range(caps.get(0).unwrap());
            let year = number(&caps, "y", 2000);
            let day = number(&caps, "d", 1);
            if (1900..=2099).contains(&year)
                && (1..=32).contains(&day)
                && alone(t, start, end)
                && word_start(t, start, t.chars[start].is_ascii())
                && !letter(t.at(end))
            {
                out.push((start, end, "DATE", (4, 0)));
            }
        }
    }
    for caps in r.day_month.captures_iter(&t.utf8) {
        let (start, end) = t.range(caps.get(0).unwrap());
        let rest = rest_of_word(t, end);
        if (1..=32).contains(&number(&caps, "d", 0)) && alone(t, start, end) && (rest.is_empty() || r.month_suffix.is_match(rest))
        {
            out.push((start, end, "DATE", (4, 0)));
        }
    }
}

/// `marks` is the text with its digits unfolded: a Devanagari digit is never part of an address.
fn others(t: &Text, marks: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    for m in r.email.find_iter(&marks.utf8) {
        let (start, end) = marks.range(m);
        out.push((start, end, "EMAIL", (2, 0)));
    }
    for m in r.license_shape.find_iter(&t.utf8) {
        let (start, end) = t.range(m);
        if alone(t, start, end) {
            out.push((start, end, "LICENSE_NO", (3, 0)));
        }
    }
    for (i, pattern) in r.plates.iter().enumerate() {
        for m in pattern.find_iter(&t.utf8) {
            let (start, end) = t.range(m);
            if alone(t, start, end) && word_start(t, start, i == 1 || i == 3) {
                out.push((start, end, "VEHICLE_PLATE", (2, 0)));
            }
        }
    }
}

/// The identifiers in `text` as sorted spans that do not overlap.
///
/// Where candidates overlap, a number named by a keyword wins over one recognised by shape,
/// the nearer keyword wins over the farther, and then the longer match wins.
pub fn find(text: &str) -> Vec<Span> {
    let t = Text::new(text, true);
    let mut found: Vec<Candidate> = Vec::new();
    ids(&t, &mut found);
    phones(&t, &mut found);
    dates(&t, &mut found);
    others(&t, &Text::new(text, false), &mut found);
    // The Python key is (priority, start - end, start); a longer match has the smaller second part.
    found.sort_by_key(|c| (c.3, std::cmp::Reverse(c.1 - c.0), c.0));
    let mut taken: Vec<Span> = Vec::new();
    for (start, end, label, _) in found {
        if taken.iter().all(|(s, e, _)| end <= *s || *e <= start) {
            taken.push((start, end, label.to_string()));
        }
    }
    taken.sort();
    taken
}
