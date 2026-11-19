//! Rule-based recognizers for identifiers as they are written in Nepal, in India and on the web.
//! See `rakshya/rules.py`.
//!
//! The patterns are not written here. They are read from `rules.json`, which
//! `python -m rakshya.rules --export wasm/rules.json` writes, so this file holds only the
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
    landlines: Vec<String>,
    email: String,
    license_shape: String,
    glued_phone: String,
    next_phone: String,
    sentence_break: String,
    symbol: String,
    national: HashMap<String, (usize, usize)>,
    numeric_dates: Vec<(String, String)>,
    date_gated: String,
    era_after: String,
    era_end: String,
    decade: String,
    time: String,
    whole_date: String,
    copyright: String,
    word_dates: Vec<String>,
    day_month: String,
    month_suffix: String,
    plates: Vec<String>,
    shapes: Vec<(String, String, u8, String)>,
    mark_shapes: Vec<(String, String, u8, String)>,
    not_ip: String,
    clock: String,
    domain: String,
    secret_gated: String,
    not_secret: String,
    bearer: String,
    otp_before: String,
    username_gated: String,
    social_gated: String,
}

/// A check takes a match as the text and its range, and gives the part of it to report, if any.
type Check = fn(&Text, usize, usize) -> Option<(usize, usize)>;

/// A row of `SHAPES` or `MARK_SHAPES`.
struct Shape {
    label: &'static str,
    check: Check,
    rank: u8,
    pattern: Regex,
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
    landlines: Vec<Regex>,
    email: Regex,
    license_shape: Regex,
    glued_phone: Regex,
    next_phone: Regex,
    sentence_break: Regex,
    symbol: Regex,
    national: HashMap<String, (usize, usize)>,
    numeric_dates: Vec<(Regex, bool)>,
    date_gated: Regex,
    era_after: Regex,
    era_end: Regex,
    decade: Regex,
    time: Regex,
    whole_date: Regex,
    whole_date_here: Regex,
    copyright: Regex,
    word_dates: Vec<Regex>,
    day_month: Regex,
    month_suffix: Regex,
    plates: Vec<Regex>,
    shapes: Vec<Shape>,
    mark_shapes: Vec<Shape>,
    not_ip: Regex,
    clock: Regex,
    domain: Regex,
    secret_gated: Regex,
    not_secret: Regex,
    bearer: Regex,
    otp_before: Regex,
    usernames: [Regex; 2],
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
        let shapes = |list: &[(String, String, u8, String)]| {
            let shape = |(label, check, rank, p): &(String, String, u8, String)| Shape {
                label: label_of(label),
                check: check_of(check),
                rank: *rank,
                pattern: compile(p),
            };
            list.iter().map(shape).collect()
        };
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
            landlines: t.landlines.iter().map(|p| compile(p)).collect(),
            email: compile(&t.email),
            license_shape: compile(&t.license_shape),
            glued_phone: compile(&t.glued_phone),
            next_phone: at_start(&t.next_phone),
            sentence_break: compile(&t.sentence_break),
            symbol: at_start(&t.symbol),
            national: t.national,
            numeric_dates: t.numeric_dates.iter().map(|(p, order)| (compile(p), order == "dmy")).collect(),
            date_gated: compile(&t.date_gated),
            era_after: at_start(&t.era_after),
            era_end: compile(&t.era_end),
            decade: at_start(&t.decade),
            time: compile(&t.time),
            whole_date: compile(&t.whole_date),
            whole_date_here: at_start(&t.whole_date),
            copyright: compile(&t.copyright),
            word_dates: t.word_dates.iter().map(|p| compile(p)).collect(),
            day_month: compile(&t.day_month),
            month_suffix: whole(&t.month_suffix),
            plates: t.plates.iter().map(|p| compile(p)).collect(),
            shapes: shapes(&t.shapes),
            mark_shapes: shapes(&t.mark_shapes),
            not_ip: compile(&t.not_ip),
            clock: whole(&t.clock),
            domain: whole(&t.domain),
            secret_gated: compile(&t.secret_gated),
            not_secret: whole(&t.not_secret),
            bearer: compile(&t.bearer),
            otp_before: compile(&t.otp_before),
            usernames: [compile(&t.username_gated), compile(&t.social_gated)],
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

    /// Characters `start..end` as a slice of the text. As in Python, a range past the end is cut short.
    fn slice(&self, start: usize, end: usize) -> &str {
        let end = end.min(self.chars.len());
        &self.utf8[self.bytes[start.min(end)]..self.bytes[end]]
    }

    fn range(&self, m: regex::Match) -> (usize, usize) {
        (self.index[m.start()], self.index[m.end()])
    }

    fn at(&self, i: usize) -> char {
        self.chars.get(i).copied().unwrap_or(' ')
    }

    /// The character before position `i`, or a space at the start of the text.
    fn before(&self, i: usize) -> char {
        if i > 0 {
            self.chars[i - 1]
        } else {
            ' '
        }
    }

    /// Where `word` first stands within characters `start..end`, as `str.find` says.
    fn find(&self, word: &str, start: usize, end: usize) -> Option<usize> {
        self.slice(start, end).find(word).map(|byte| self.index[self.bytes[start] + byte])
    }
}

type Candidate = (usize, usize, &'static str, (u8, usize));

/// True when `value` is figures only, in Latin or Devanagari, and begins as a mobile number of Nepal does.
pub fn mobile_with_more(value: &str) -> bool {
    let r = rules();
    let figures: String = value.chars().map(|ch| *r.fold.get(&ch).unwrap_or(&ch)).collect();
    figures.chars().all(digit) && r.mobile_prefix.is_match(&figures)
}

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
/// Case markers that are written against the word before them, in Nepali and in Hindi.
const AFTER_A_WORD: [&str; 12] = ["को", "का", "की", "के", "ले", "मा", "लाई", "बाट", "सँग", "में", "से", "पर"];

/// A Devanagari letter or sign.
fn devanagari(ch: char) -> bool {
    ('\u{900}'..='\u{97f}').contains(&ch)
}

/// True when no Devanagari letter or sign stands at `at`, or a case marker does and the word ends after it.
fn ends_word(t: &Text, at: usize) -> bool {
    if !devanagari(t.at(at)) {
        return true;
    }
    AFTER_A_WORD.iter().any(|marker| {
        let chars: Vec<char> = marker.chars().collect();
        at + chars.len() <= t.chars.len() && t.chars[at..at + chars.len()] == chars[..] && !devanagari(t.at(at + chars.len()))
    })
}

fn alone(t: &Text, start: usize, end: usize) -> bool {
    alone_in(t, start, end, &[], false)
}

/// As `alone`. `cells` are positions where a cell of a table ends: what starts there starts a number of its
/// own. With `listed` a slash and a digit may follow, as after a phone number in a list.
fn alone_in(t: &Text, start: usize, end: usize, cells: &[usize], listed: bool) -> bool {
    let n = t.chars.len();
    let before = if start > 0 && !cells.contains(&start) { t.chars[start - 1] } else { ' ' };
    let after = if end < n { t.chars[end] } else { ' ' };
    if digit(before) || digit(after) {
        return false;
    }
    if (after == '-' || (after == '/' && !listed)) && end + 1 < n && digit(t.chars[end + 1]) {
        return false;
    }
    if (before == '-' || before == '/') && start > 1 && digit(t.chars[start - 2]) {
        return false;
    }
    true
}

/// True when no digit follows position `end`, nor a hyphen or a slash with a digit behind it.
fn ends(t: &Text, end: usize) -> bool {
    let after = t.at(end);
    !(digit(after) || ((after == '-' || after == '/') && end + 1 < t.chars.len() && digit(t.chars[end + 1])))
}

/// True when the digits against the end of a date are the next cell of a table and not the rest of a longer number.
fn next_cell(t: &Text, end: usize) -> bool {
    let n = t.chars.len();
    let mut stop = end;
    while stop < n && digit(t.chars[stop]) {
        stop += 1;
    }
    let after = t.at(stop);
    if stop < n && (after == '-' || after == '/') && digit(t.at(stop + 1)) {
        return rules().whole_date_here.captures(t.slice(end, n)).map_or(false, |caps| caps["s1"] == caps["s2"]);
    }
    stop - end <= 2 || (stop - end == 4 && matches!(t.slice(end, end + 2), "19" | "20"))
}

/// Dates written year-month-day that stand against a neighbouring cell of a table, and where every such date ends.
fn whole_dates(t: &Text) -> (Vec<(usize, usize)>, Vec<usize>) {
    let n = t.chars.len();
    let mut out = Vec::new();
    let mut cells: Vec<usize> = Vec::new();
    for caps in rules().whole_date.captures_iter(&t.utf8) {
        let (start, end) = t.range(caps.get(0).unwrap());
        let before = if start > 0 && !cells.contains(&start) { t.chars[start - 1] } else { ' ' };
        let after = t.at(end);
        if caps["s1"] != caps["s2"]
            || digit(before)
            || ((before == '-' || before == '/') && start > 1 && digit(t.chars[start - 2]))
            || ((after == '-' || after == '/') && end + 1 < n && digit(t.chars[end + 1]))
            || (digit(after) && !next_cell(t, end))
        {
            continue;
        }
        if digit(after) || cells.contains(&start) {
            out.push((start, end));
        }
        cells.push(end);
    }
    (out, cells)
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

/// The end of a date with the era that follows it in Latin letters, where that is a word of its own.
fn with_era(t: &Text, end: usize) -> usize {
    match rules().era_after.find(t.slice(end, t.chars.len())) {
        Some(m) => {
            let stop = t.index[t.bytes[end] + m.end()];
            let after = t.at(stop);
            if letter(after) || digit(after) {
                end
            } else {
                stop
            }
        }
        None => end,
    }
}

/// True when the letters against the year that ends a date may be the next word of a page that runs its cells
/// together ("March 7, 2016by Admin"): the date has a space or a comma inside, so it is no code, and what
/// follows is not the "s" of a decade.
fn runs_on(t: &Text, start: usize, end: usize) -> bool {
    let inside = t.slice(start, end);
    let first = t.at(end);
    (inside.contains(' ') || inside.contains(',')) && !((first == 's' || first == 'S') && !letter(t.at(end + 1)))
}

/// False for figures after a keyword that are no date as they stand: a year has a day or a month at its other
/// end, and "2076-03-1014" is a date with the next cell of a table run on to it.
fn gated_date(value: &str) -> bool {
    let parts: Vec<&str> = value.split(|ch| ch == '-' || ch == '/' || ch == '.').collect();
    parts[0].len() < 3 || parts[parts.len() - 1].len() < 3
}

fn label_of(name: &str) -> &'static str {
    #[rustfmt::skip]
    const LABELS: [&str; 16] = [
        "PHONE", "URL", "USERNAME", "IP_ADDRESS", "CITIZENSHIP_NO", "NATIONAL_ID", "TAX_ID", "PASSPORT_NO", "LICENSE_NO",
        "VOTER_ID", "ID_NUMBER", "BANK_ACCOUNT", "CARD_NUMBER", "UPI_ID", "VEHICLE_PLATE", "SECRET",
    ];
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
                let (mut start, mut end) = t.range(value);
                if !alone(t, start, end) || r.any_keyword.is_match(gap) || r.sentence_break.is_match(gap) {
                    continue;
                }
                if gap.chars().last().map_or(false, letter) {
                    continue; // the end of a longer token: "TXN7576964714"
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
                if label == "ID_NUMBER" {
                    // Capitals written against the number are its first part, not a keyword: "MRN4416013".
                    let keyword = caps.name("kw").unwrap();
                    let word = keyword.as_str();
                    if (gap.is_empty() || gap == "-") && word.len() <= 4 && word.chars().all(|ch| ch.is_ascii_uppercase()) {
                        start = t.index[keyword.start()];
                    }
                    // A word written against the number ("236345Section") is not part of it.
                    let mut stop = end;
                    while stop > start && letter(t.chars[stop - 1]) {
                        stop -= 1;
                    }
                    if end - stop >= 3 && t.chars[stop..end].iter().any(|ch| ch.is_lowercase()) {
                        end = stop;
                    }
                    while end > start && "-/".contains(t.chars[end - 1]) {
                        end -= 1;
                    }
                    if digits(t.slice(start, end)) < 3 {
                        continue;
                    }
                    // The letter after the symbol number of an examination belongs to it: "0234567 B".
                    if r.symbol.is_match(word)
                        && end < t.chars.len()
                        && t.chars[end] == ' '
                        && t.at(end + 1).is_ascii_uppercase()
                        && !wordy(t.at(end + 2))
                    {
                        end += 2;
                    }
                    // The one Devanagari letter that ends a number written in groups with full stops belongs to it:
                    // "०२१.०८.३१९ख". A word written against the number does not.
                    if t.chars[start..end].contains(&'.')
                        && end < t.chars.len()
                        && ('क'..='ह').contains(&t.chars[end])
                        && ends_word(t, end + 1)
                    {
                        end += 1;
                    }
                }
                if label == "SECRET" && end < t.chars.len() && t.chars[end] == ' ' && digit(t.at(end + 1)) {
                    continue; // the first group of a longer number
                }
                if label == "CARD_NUMBER" {
                    let written = value.as_str().chars().filter(|&ch| !"- ".contains(ch)).count();
                    if digits(value.as_str()) < 4 || !(12..=19).contains(&written) {
                        continue;
                    }
                }
                if label == "UPI_ID" && ".-".contains(t.at(end)) && letter(t.at(end + 1)) {
                    continue; // the start of an e-mail address
                }
                out.push((start, end, label, (if strong { 0 } else { 1 }, gap.chars().count())));
            }
        }
    }
}

fn phones(t: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    let first = out.len();
    single_phones(t, out);
    // A bare number of six to ten digits after a phone number and a comma, a slash or a bar is one more of the list.
    let mut ends: Vec<usize> = out[first..].iter().map(|candidate| candidate.1).collect();
    let mut k = 0;
    while k < ends.len() {
        if let Some(caps) = r.next_phone.captures(t.slice(ends[k], t.chars.len())) {
            let m = caps.name("n").unwrap();
            let base = t.bytes[ends[k]];
            let (start, end) = (t.index[base + m.start()], t.index[base + m.end()]);
            let after = t.at(end);
            if !(digit(after) || letter(after) || (after == '-' && digit(t.at(end + 1)))) && !ends.contains(&end) {
                out.push((start, end, "PHONE", (2, 0)));
                ends.push(end);
            }
        }
        k += 1;
    }
}

fn single_phones(t: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    for caps in r.mobile.captures_iter(&t.utf8) {
        let number = caps.name("n").unwrap();
        let end = t.index[caps.get(0).unwrap().end()];
        let start = t.index[caps.name("cc").unwrap_or(number).start()];
        let text = number.as_str();
        if alone_in(t, start, end, &[], true)
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
            if alone_in(t, start, end, &[], true) && r.fixed_line.is_match(&joined) {
                out.push((start, end, "PHONE", (2, 0)));
            }
        }
    }
    for caps in r.phone_gated.captures_iter(&t.utf8) {
        let (start, mut end) = t.range(caps.name("val").unwrap());
        let gap = caps.name("gap").unwrap().as_str();
        if end - start > 3 && t.chars[end - 2] == ' ' && digit(t.chars[end - 3]) {
            end -= 2; // a single digit after a space is the next cell of a table, not the end of the number
        }
        if gap.chars().last().map_or(false, letter) {
            continue; // the end of a longer token: "TXN7576964714"
        }
        if alone_in(t, start, end, &[], true) && !r.any_keyword.is_match(gap) {
            out.push((start, end, "PHONE", (2, gap.chars().count())));
        }
    }
}

fn dates(t: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    let (whole, mut cells) = whole_dates(t);
    for (start, end) in whole {
        out.push((start, end, "DATE", (4, 0)));
    }
    // What stands against the minutes of a time of day starts a cell of its own.
    for m in r.time.find_iter(&t.utf8) {
        let (start, end) = t.range(m);
        if !(start > 0 && digit(t.chars[start - 1])) {
            cells.push(end);
        }
    }
    for caps in r.copyright.captures_iter(&t.utf8) {
        let last = caps.name("to").or(caps.name("val")).unwrap();
        if ends(t, t.index[last.end()]) {
            let (start, end) = t.range(caps.name("val").unwrap());
            out.push((start, end, "DATE", (4, 0)));
            if let Some(to) = caps.name("to") {
                let (start, end) = t.range(to);
                out.push((start, end, "DATE", (4, 0)));
            }
        }
    }
    for (pattern, day_first) in &r.numeric_dates {
        for caps in pattern.captures_iter(&t.utf8) {
            let (start, end) = t.range(caps.get(0).unwrap());
            if caps["s1"] == caps["s2"]
                && alone(t, start, end)
                && plausible_date(number(&caps, "y", 0), number(&caps, "a", 0), number(&caps, "b", 0), *day_first)
            {
                out.push((start, with_era(t, end), "DATE", (4, 0)));
            }
        }
    }
    for caps in r.date_gated.captures_iter(&t.utf8) {
        let value = caps.name("val").unwrap();
        let (mut start, end) = t.range(value);
        let gap = caps.name("gap").unwrap().as_str();
        // The era at the end of what stands between the keyword and the date is part of the date.
        if let Some(era) = r.era_end.find(gap) {
            start -= gap[era.start()..].chars().count();
        }
        if alone(t, start, end) && gated_date(value.as_str()) {
            out.push((start, end, "DATE", (3, gap.chars().count())));
        }
    }
    for pattern in &r.word_dates {
        for caps in pattern.captures_iter(&t.utf8) {
            let (start, end) = t.range(caps.get(0).unwrap());
            let y = caps.name("y");
            let short = y.map_or(false, |m| m.as_str().len() == 3);
            let year = number(&caps, "y", 2000) + if short { 2000 } else { 0 };
            let day = number(&caps, "d", 1);
            let closes = y.map_or(false, |m| t.index[m.end()] == end); // the year ends the date
            // A date that starts with a word is not the rest of the number before it, and a capital after a
            // small letter starts a word on a page that runs its cells together.
            let mut own = cells.clone();
            if !digit(t.chars[start]) {
                own.push(start);
            }
            let capital = start > 0 && t.chars[start].is_ascii_uppercase() && t.chars[start - 1].is_ascii_lowercase();
            if !((1900..=2099).contains(&year)
                && (1..=32).contains(&day)
                && alone_in(t, start, end, &own, false)
                && (capital || word_start(t, start, t.chars[start].is_ascii())))
            {
                continue;
            }
            if letter(t.at(end)) && !(closes && runs_on(t, start, end)) {
                continue;
            }
            if closes && r.decade.is_match(t.slice(end, t.chars.len())) {
                continue;
            }
            // A month that ends the date ends its word or carries only case markers, as after a day.
            if let Some(m) = caps.name("m") {
                if t.index[m.end()] == end {
                    let rest = rest_of_word(t, end);
                    if !rest.is_empty() && !r.month_suffix.is_match(rest) {
                        continue;
                    }
                }
            }
            out.push((start, if closes { with_era(t, end) } else { end }, "DATE", (4, 0)));
        }
    }
    for caps in r.day_month.captures_iter(&t.utf8) {
        let (start, end) = t.range(caps.get(0).unwrap());
        let rest = rest_of_word(t, end);
        if (1..=32).contains(&number(&caps, "d", 0))
            && alone_in(t, start, end, &cells, false)
            && (rest.is_empty() || r.month_suffix.is_match(rest))
        {
            out.push((start, end, "DATE", (4, 0)));
        }
    }
}

/// Where an e-mail address starts when a phone number is written against it.
///
/// Text copied from a web page runs the cells of a table together, and the address then seems to
/// begin with the number before it ("Phone9841234567ram@example.com"). A mobile or a landline
/// number of Nepal followed by a letter, inside the part before the "@", is read as that number.
fn after_phone(t: &Text, start: usize, end: usize) -> usize {
    let r = rules();
    let at = (start..end).find(|&i| t.chars[i] == '@').expect("an address has an @");
    let local = t.slice(start, at);
    let mut cut = start;
    for caps in r.glued_phone.captures_iter(local) {
        let found = caps.name("n").unwrap();
        let number = found.as_str();
        let valid = if number.starts_with('0') {
            r.fixed_line.is_match(&number[1..].replace('-', ""))
        } else {
            let mobile = number.strip_prefix("977").map_or(number, |rest| rest.trim_start_matches('-'));
            r.mobile_prefix.is_match(mobile) && mobile.matches('-').count() <= 1
        };
        let from = start + local[..found.start()].chars().count();
        let to = start + local[..found.end()].chars().count();
        let before = if from > 0 { t.chars[from - 1] } else { ' ' };
        if valid && !digit(before) && at - to >= 2 {
            cut = to;
        }
    }
    cut
}

/// `marks` is the text with its digits unfolded: a Devanagari digit is never part of an address.
fn others(t: &Text, marks: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    for m in r.email.find_iter(&marks.utf8) {
        let (start, end) = marks.range(m);
        out.push((after_phone(marks, start, end), end, "EMAIL", (2, 0)));
    }
    for m in r.license_shape.find_iter(&t.utf8) {
        let (start, end) = t.range(m);
        if alone(t, start, end) {
            out.push((start, end, "LICENSE_NO", (3, 0)));
        }
    }
    for (i, pattern) in r.plates.iter().enumerate() {
        let latin = i == 1 || i == 3;
        for m in pattern.find_iter(&t.utf8) {
            let (start, end) = t.range(m);
            if latin && letter(t.at(end)) {
                continue; // "ko 20 ka 250ru" is not a plate
            }
            if alone(t, start, end) && word_start(t, start, latin) {
                out.push((start, end, "VEHICLE_PLATE", (2, 0)));
            }
        }
    }
}

fn only_digits(value: &str) -> Vec<u32> {
    value.chars().filter_map(|ch| ch.to_digit(10)).collect()
}

/// The check of payment card numbers (ISO/IEC 7812).
fn luhn(digits: &[u32]) -> bool {
    let double = |d: u32| if d > 4 { d * 2 - 9 } else { d * 2 };
    let total: u32 = digits.iter().rev().enumerate().map(|(i, &d)| if i % 2 == 1 { double(d) } else { d }).sum();
    total % 10 == 0
}

/// ISO 13616: move the first four characters to the end, read letters as 10 to 35, and divide by 97.
fn iban_valid(value: &str) -> bool {
    let value: Vec<char> = value.chars().filter(|&ch| ch != ' ').collect();
    if !(15..=34).contains(&value.len()) {
        return false;
    }
    let mut rest = 0;
    for &ch in value[4..].iter().chain(&value[..4]) {
        let n = ch as u32 - if digit(ch) { 48 } else { 55 };
        rest = (rest * (if n < 10 { 10 } else { 100 }) + n) % 97;
    }
    rest == 1
}

/// True when the first digits and the count of digits are those of a card network.
///
/// Maestro is too wide to tell from other numbers by form, and fifteen digits that start with 35
/// are the number of a phone (IMEI), not a card.
fn card_issuer(d: &[u32]) -> bool {
    let n = d.len();
    let two = d[0] * 10 + d[1];
    let three = two * 10 + d[2];
    let four = three * 10 + d[3];
    if d[0] == 4 {
        return matches!(n, 13 | 16 | 19); // Visa
    }
    if (51..=55).contains(&two) || (2221..=2720).contains(&four) {
        return n == 16; // Mastercard
    }
    if two == 34 || two == 37 {
        return n == 15; // American Express
    }
    if matches!(two, 36 | 38 | 39) || (300..=305).contains(&three) {
        return n == 14 || n == 16; // Diners Club
    }
    if two == 35 {
        return (16..=19).contains(&n); // JCB
    }
    if matches!(two, 60 | 62 | 64 | 65 | 81 | 82) || three == 508 {
        return (16..=19).contains(&n); // Discover, UnionPay, RuPay
    }
    false
}

/// A Latin letter or a digit.
fn wordy(ch: char) -> bool {
    letter(ch) || digit(ch)
}

/// True when no Latin letter, digit or character of `also` touches the range on either side.
fn apart(t: &Text, start: usize, end: usize, also: &str) -> bool {
    let (before, after) = (t.before(start), t.at(end));
    !(wordy(before) || wordy(after) || also.contains(before) || also.contains(after))
}

/// `str.isalpha` of Python: every character is a letter, and there is at least one.
fn is_alpha(value: &str) -> bool {
    static LETTERS: OnceLock<Regex> = OnceLock::new();
    LETTERS.get_or_init(|| whole(r"\p{L}+")).is_match(value)
}

/// `str.islower` of Python: there is a character in lower case, and none in upper or title case.
fn is_lower(value: &str) -> bool {
    static LOWER: OnceLock<Regex> = OnceLock::new();
    LOWER.get_or_init(|| whole(r"[^\p{Uppercase}\p{Lt}]*\p{Lowercase}[^\p{Uppercase}\p{Lt}]*")).is_match(value)
}

fn check_number(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    (alone(t, start, end) && apart(t, start, end, "+")).then_some((start, end))
}

fn check_word(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    apart(t, start, end, "-_").then_some((start, end))
}

/// A card number in one of its written forms with a valid check digit. When three more digits
/// follow the sixteen, the nineteen are tried first and then the sixteen.
fn check_card(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    for stop in [end, end - 4] {
        let d = only_digits(t.slice(start, stop));
        if (13..=19).contains(&d.len()) && alone(t, start, stop) && apart(t, start, stop, "") && card_issuer(&d) && luhn(&d) {
            return Some((start, stop));
        }
        if !(d.len() == 19 && "- ".contains(t.chars[stop - 4])) {
            break;
        }
    }
    None
}

/// The longest run that passes the check. The pattern may have taken in a capital word after the number.
fn check_iban(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    if wordy(t.before(start)) {
        return None;
    }
    let mut stop = end;
    while stop > start + 14 {
        if iban_valid(t.slice(start, stop)) && !wordy(t.at(stop)) {
            return Some((start, stop));
        }
        stop = start + t.chars[start..stop].iter().rposition(|&ch| ch == ' ')?;
    }
    None
}

fn check_ipv4(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    let parts: Vec<&str> = t.slice(start, end).split('.').collect();
    let value = |part: &str| part.parse::<u32>().unwrap();
    let (before, after) = (t.before(start), t.at(end));
    if parts.iter().any(|part| value(part) > 255 || (part.len() > 1 && part.starts_with('0'))) {
        return None;
    }
    if wordy(before) || "./-".contains(before) || wordy(after) || (".-".contains(after) && digit(t.at(end + 1))) {
        return None;
    }
    let lead = format!(" {}", t.slice(start.saturating_sub(24), start));
    if rules().not_ip.is_match(&lead) || parts.iter().all(|part| value(part) < 10) {
        return None; // a version or a section number
    }
    Some((start, end))
}

fn check_ipv6(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    let value = t.slice(start, end);
    let groups = value.split(':').filter(|group| !group.is_empty()).count();
    if !apart(t, start, end, ":.") || groups > 8 || (groups < 8 && !value.contains("::")) {
        return None;
    }
    if groups < 2 || !value.chars().any(digit) {
        return None;
    }
    if groups < 3 && !value.chars().any(letter) {
        return None; // "12::30"
    }
    Some((start, end))
}

fn check_mac(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    (apart(t, start, end, ":-") && t.slice(start, end).chars().any(digit)).then_some((start, end))
}

fn check_ssn(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    let (area, group, serial) = (t.slice(start, start + 3), t.slice(start + 4, start + 6), t.slice(start + 7, end));
    if area == "000" || area == "666" || area.starts_with('9') || group == "00" || serial == "0000" {
        return None;
    }
    if group.parse::<u32>().unwrap() == (area.parse::<u32>().unwrap() + 1) % 100 {
        return None; // a fiscal year of Nepal before a serial number: 078-79-0012
    }
    (alone(t, start, end) && apart(t, start, end, "")).then_some((start, end))
}

/// A number that starts with "+" and a country code.
///
/// The pattern takes groups of digits as long as they come, so it may run on into the next cell of
/// a table. The match is cut back, group by group, until it has no more digits than a number of
/// its country has (fifteen in all for a country that is not listed) and does not end in a single
/// digit after a space.
fn check_plus_phone(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    let r = rules();
    let before = if start > 0 { t.chars[start - 1] } else { ' ' };
    if wordy(before) || before == '+' {
        return None;
    }
    let run: String = t.chars[start..end].iter().filter(|&&ch| digit(ch)).collect();
    let code = [3, 2, 1].iter().map(|&n| &run[..run.len().min(n)]).find(|&head| r.national.contains_key(head)).unwrap_or("");
    let (low, mut high) = if code.is_empty() { (8, 15) } else { r.national[code] };
    if code == "977" && !r.mobile_prefix.is_match(&run[3..]) {
        high = 8; // a landline: area code and number are eight digits together
    }
    let mut stop = end;
    while stop > start {
        let value = &t.chars[start..stop];
        let last = value[value.len() - 1];
        let group_end = (digit(last) || last == ')') && (stop == end || "- .(".contains(t.chars[stop]));
        let count = value.iter().filter(|&&ch| digit(ch)).count() as i64 - code.len() as i64;
        if group_end && count < low as i64 {
            return None;
        }
        let stray = value.len() > 2 && value[value.len() - 2] == ' ' && digit(last);
        let open = value.iter().filter(|&&ch| ch == '(').count();
        let closed = value.iter().filter(|&&ch| ch == ')').count();
        if group_end && count <= high as i64 && !stray && open == closed {
            return Some((start, stop));
        }
        stop -= 1;
    }
    None
}

/// The length of a web address without the punctuation that ends a sentence or closes a bracket.
fn trim_address(value: &[char]) -> usize {
    let count = |bracket: char, end: usize| value[..end].iter().filter(|&&ch| ch == bracket).count();
    let mut end = value.len();
    while end > 0 {
        let ch = value[end - 1];
        if ".,;:!?'*([".contains(ch)
            || (ch == ')' && count('(', end) < count(')', end))
            || (ch == ']' && count('[', end) < count(']', end))
        {
            end -= 1;
        } else {
            break;
        }
    }
    end
}

/// Where a label written against the address starts ("...gov.npPhone"), or the length of the address.
///
/// Only an address without a path is cut: its last part is then in one case, like an e-mail address's.
fn host_end(value: &[char]) -> usize {
    let rest = match value.windows(3).position(|three| three == [':', '/', '/']) {
        Some(at) => &value[at + 3..],
        None => value,
    };
    if rest.iter().any(|&ch| "/?#".contains(ch)) {
        return value.len();
    }
    let last = value.iter().rposition(|&ch| ch == '.').map_or(0, |dot| dot + 1);
    for i in last + 2..value.len() {
        if value[i].is_uppercase() && value[i - 1].is_lowercase() {
            return i;
        }
    }
    value.len()
}

fn check_url(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    if start > 0 && wordy(t.chars[start - 1]) && t.slice(start, start + 4).to_lowercase() == "www." {
        return None; // "http" may be written against the word before it; "www." inside a word is no address
    }
    // A second address may be written against the first, and a page that shortens an address ends it with three dots.
    let again = ["http://", "https://", "..."].iter().filter_map(|word| t.find(word, start + 4, end)).min().unwrap_or(end);
    let stop = start + trim_address(&t.chars[start..again]);
    let stop = start + host_end(&t.chars[start..stop]);
    (t.chars[start..stop].contains(&'.') && stop - start > 6).then_some((start, stop))
}

fn check_domain(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    let before = t.before(start);
    if wordy(before) || "@._-/%+\\".contains(before) {
        return None;
    }
    let stop = start + trim_address(&t.chars[start..end]);
    let value = &t.chars[start..stop];
    let cut = value.iter().position(|&ch| "/?#".contains(ch)).unwrap_or(value.len());
    let host = &value[..cut];
    let after = t.at(stop);
    let tld = host.iter().rposition(|&ch| ch == '.').map_or(0, |dot| dot + 1);
    let lower = is_lower(t.slice(start + tld, start + cut));
    // The name ends the match. A letter of the same case after it means the name goes on.
    let goes_on = letter(after) && !(lower && after.is_uppercase());
    if cut == value.len() && (after == '@' || digit(after) || after == '-' || goes_on) {
        return None;
    }
    if !(lower || host.iter().filter(|&&ch| letter(ch)).all(|ch| ch.is_uppercase())) {
        return None; // "office.In" at the start of a sentence
    }
    Some((start, stop))
}

/// A name with a path after it. The path must be more than the punctuation that was trimmed off.
fn check_path_domain(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    check_domain(t, start, end).filter(|&(start, stop)| t.slice(start, stop.saturating_sub(1)).contains('/'))
}

fn check_handle(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    let r = rules();
    let before = t.before(start);
    // The body of the handle is start + 1..stop.
    let dots = |mut stop: usize| {
        while stop > start + 1 && t.chars[stop - 1] == '.' {
            stop -= 1;
        }
        stop
    };
    let mut stop = dots(end);
    if t.slice(stop, stop + 3) == "://" {
        // An address written against the handle.
        let body = t.slice(start + 1, stop);
        if body.ends_with("https") {
            stop -= 5;
        } else if body.ends_with("http") {
            stop -= 4;
        }
        stop = dots(stop);
    }
    let body = t.slice(start + 1, stop);
    if wordy(before) || "@._%+-/".contains(before) || t.at(stop) == '@' || stop - start < 4 || !body.chars().any(letter) {
        return None;
    }
    if r.domain.is_match(body) || r.clock.is_match(body) {
        return None; // "@gmail.com" names a mail service, "@11am" a time
    }
    Some((start, stop))
}

fn check_upi(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    let (before, after) = (t.before(start), t.at(end));
    if wordy(before) || "._-@".contains(before) || wordy(after) || (".-".contains(after) && wordy(t.at(end + 1))) {
        return None;
    }
    Some((start, end))
}

fn check_key(t: &Text, start: usize, end: usize) -> Option<(usize, usize)> {
    apart(t, start, end, "_-").then_some((start, end))
}

fn check_of(name: &str) -> Check {
    match name {
        "card" => check_card,
        "iban" => check_iban,
        "ipv4" => check_ipv4,
        "ipv6" => check_ipv6,
        "mac" => check_mac,
        "ssn" => check_ssn,
        "plus_phone" => check_plus_phone,
        "number" => check_number,
        "word" => check_word,
        "url" => check_url,
        "domain" => check_domain,
        "path_domain" => check_path_domain,
        "handle" => check_handle,
        "upi" => check_upi,
        "key" => check_key,
        _ => panic!("check {name} is not known"),
    }
}

/// Each match that passes its check. The search goes on from where the accepted part ends, so that
/// what a check cut off the end of a match (a second address, a second number) is looked at again.
fn shapes(t: &Text, table: &[Shape], out: &mut Vec<Candidate>) {
    for shape in table {
        let mut at = 0;
        while let Some(m) = shape.pattern.find_at(&t.utf8, t.bytes[at]) {
            let (start, end) = t.range(m);
            let span = (shape.check)(t, start, end);
            if let Some((start, stop)) = span {
                out.push((start, stop, shape.label, (shape.rank, 0)));
            }
            at = span.map_or(end, |span| span.1).max(start + 1);
        }
    }
}

/// The keywords of `secret_gated` that name a password, which may be shorter than a key.
const PASSWORDS: [&str; 6] = ["password", "passwd", "pwd", "passcode", "पासवर्ड", "पासवोर्ड"];

/// Passwords, keys and user names that a word before them names. `t` has its digits unfolded.
fn credentials(t: &Text, out: &mut Vec<Candidate>) {
    let r = rules();
    for caps in r.secret_gated.captures_iter(&t.utf8) {
        let (mut start, mut end) = t.range(caps.name("val").unwrap());
        if "\"'".contains(t.chars[start]) {
            (start, end) = (start + 1, end - 1);
        } else {
            while end > start && ".,;)".contains(t.chars[end - 1]) {
                end -= 1;
            }
        }
        let (value, gap) = (t.slice(start, end), &caps["gap"]);
        let long_one = !PASSWORDS.contains(&caps["kw"].to_lowercase().as_str());
        if end - start < (if long_one { 8 } else { 4 }) || r.not_secret.is_match(value) {
            continue;
        }
        if gap.contains("is") && is_alpha(value) && is_lower(value) {
            continue; // "the password is only for members"
        }
        out.push((start, end, "SECRET", (1, gap.chars().count())));
    }
    for caps in r.bearer.captures_iter(&t.utf8) {
        let (start, end) = t.range(caps.name("val").unwrap());
        out.push((start, end, "SECRET", (2, 0)));
    }
    for caps in r.otp_before.captures_iter(&t.utf8) {
        let (start, end) = t.range(caps.name("val").unwrap());
        if alone(t, start, end) {
            out.push((start, end, "SECRET", (1, 0)));
        }
    }
    for (pattern, handle_like) in r.usernames.iter().zip([false, true]) {
        for caps in pattern.captures_iter(&t.utf8) {
            let (start, mut end) = t.range(caps.name("val").unwrap());
            while end > start && ".-".contains(t.chars[end - 1]) {
                end -= 1;
            }
            let value = t.slice(start, end);
            // An e-mail address, a word about user names, or a number that another rule reads.
            if t.at(end) == '@' || end - start < 3 || r.not_secret.is_match(value) || !value.chars().any(letter) {
                continue;
            }
            // After the name of a service a plain word is more often a person's name.
            if handle_like && !(value.starts_with('@') || value.chars().any(|ch| digit(ch) || "_.".contains(ch))) {
                continue;
            }
            // The keywords that end in "=" have no gap.
            let gap = caps.name("gap").map_or(0, |gap| gap.as_str().chars().count());
            out.push((start, end, "USERNAME", (1, gap)));
        }
    }
}

/// The identifiers in `text` as sorted spans that do not overlap.
///
/// Where candidates overlap, a number named by a keyword wins over one recognised by shape,
/// the nearer keyword wins over the farther, and then the longer match wins.
pub fn find(text: &str) -> Vec<Span> {
    let r = rules();
    let (t, marks) = (Text::new(text, true), Text::new(text, false));
    let mut found: Vec<Candidate> = Vec::new();
    ids(&t, &mut found);
    phones(&t, &mut found);
    dates(&t, &mut found);
    others(&t, &marks, &mut found);
    shapes(&t, &r.shapes, &mut found);
    shapes(&marks, &r.mark_shapes, &mut found);
    credentials(&marks, &mut found);
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
