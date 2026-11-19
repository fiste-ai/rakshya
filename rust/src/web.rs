//! The interface a web page calls. Offsets going out are UTF-16 units, so that
//! `text.slice(start, end)` in JavaScript gives the span.

use crate::tagger::Tagger;
use crate::{kinds, rules, spans, Span};
use std::cell::RefCell;
use std::rc::Rc;
use wasm_bindgen::prelude::*;

thread_local! {
    static FAILURE: RefCell<String> = RefCell::new(String::new());
}

/// Keep the message of a failure in this module, so the page can report more than "unreachable".
#[wasm_bindgen(start)]
fn start() {
    std::panic::set_hook(Box::new(|info| FAILURE.with(|slot| *slot.borrow_mut() = info.to_string())));
}

/// What went wrong the last time a call into this module failed; empty if nothing did.
#[wasm_bindgen]
pub fn failure() -> String {
    FAILURE.with(|slot| slot.borrow().clone())
}

/// The UTF-16 position of every code point of the text, and of its end.
fn utf16(chars: &[char]) -> Vec<u32> {
    let mut out = Vec::with_capacity(chars.len() + 1);
    let mut at = 0;
    for ch in chars {
        out.push(at);
        at += ch.len_utf16() as u32;
    }
    out.push(at);
    out
}

/// The identifiers the rules find, as JSON `[[start, end, label], ...]`. No model is needed.
#[wasm_bindgen]
pub fn find(text: &str) -> String {
    let chars: Vec<char> = text.chars().collect();
    let map = utf16(&chars);
    let found: Vec<(u32, u32, String)> =
        rules::find(text).into_iter().map(|(start, end, label)| (map[start], map[end], label)).collect();
    serde_json::to_string(&found).unwrap()
}

/// The tokenizer and labels of one model.
#[wasm_bindgen]
pub struct Rakshya {
    tagger: Rc<Tagger>,
}

#[wasm_bindgen]
impl Rakshya {
    /// `tokenizer_json` and `tagger_json` are the text of those two files in the model folder.
    #[wasm_bindgen(constructor)]
    pub fn new(tokenizer_json: &str, tagger_json: &str) -> Result<Rakshya, JsError> {
        let tagger = Tagger::new(tokenizer_json.as_bytes(), tagger_json).map_err(|e| JsError::new(&e))?;
        Ok(Rakshya { tagger: Rc::new(tagger) })
    }

    /// Begin work on one text: run the rules and cut the text into pieces for the model.
    pub fn start(&self, text: &str) -> Run {
        let chars: Vec<char> = text.chars().collect();
        let pieces = spans::segments(&chars, 320, 1200);
        Run {
            tagger: Rc::clone(&self.tagger),
            map: utf16(&chars),
            offsets: vec![Vec::new(); pieces.len()],
            pieces,
            rules: rules::find(text),
            tagged: Vec::new(),
            chars,
        }
    }
}

/// One text on its way through the model, piece by piece.
#[wasm_bindgen]
pub struct Run {
    tagger: Rc<Tagger>,
    chars: Vec<char>,
    map: Vec<u32>,
    pieces: Vec<(usize, usize)>,
    offsets: Vec<Vec<(usize, usize)>>,
    rules: Vec<Span>,
    tagged: Vec<Span>,
}

#[wasm_bindgen]
impl Run {
    /// How many pieces the model has to read.
    #[wasm_bindgen(getter)]
    pub fn count(&self) -> usize {
        self.pieces.len()
    }

    fn piece(&self, i: usize) -> String {
        let (start, end) = self.pieces[i];
        self.chars[start..end].iter().collect()
    }

    /// Token ids of piece `i`, the model's `input_ids`. The attention mask is all ones.
    pub fn encode(&mut self, i: usize) -> Result<Vec<i64>, JsError> {
        let (ids, offsets) = self.tagger.encode(&self.piece(i)).map_err(|e| JsError::new(&e))?;
        self.offsets[i] = offsets;
        Ok(ids.into_iter().map(i64::from).collect())
    }

    /// Give back the model's two outputs for piece `i`: `logits` and `trim_logits`.
    pub fn push(&mut self, i: usize, logits: &[f32], trim_logits: &[f32]) {
        let shift = self.pieces[i].0;
        let found = self.tagger.spans_from_logits(&self.piece(i), &self.offsets[i], logits, trim_logits);
        self.tagged.extend(found.into_iter().map(|(start, end, label)| (start + shift, end + shift, label)));
    }

    /// What is given out: every label of 1.0, or with "personal" personal data only, which leaves places,
    /// organisations, dates and web addresses, the phone number and the mailbox of an office, and a number that
    /// is already masked.
    fn given(&self, labels: &str) -> Vec<Span> {
        let mut tagged = self.tagged.clone();
        tagged.sort();
        let merged = spans::merge(&tagged, &self.rules);
        if labels == "personal" {
            kinds::personal(&self.chars, &merged)
        } else {
            kinds::all(&self.chars, &merged)
        }
    }

    fn listed(&self, found: Vec<Span>) -> String {
        let found: Vec<(u32, u32, String, &str)> = found
            .into_iter()
            .map(|span| {
                // The edges say where a span comes from; its label may be the finer one that the model gave.
                let source = if self.rules.iter().any(|rule| rule.0 == span.0 && rule.1 == span.1) { "rule" } else { "tagger" };
                (self.map[span.0], self.map[span.1], span.2, source)
            })
            .collect();
        serde_json::to_string(&found).unwrap()
    }

    /// Everything found, as JSON `[[start, end, label, source], ...]`; source is "rule" or "tagger".
    pub fn finish(&self) -> String {
        self.listed(self.given("all"))
    }

    /// What is found under a profile, "all" or "personal", in the form of `finish`.
    pub fn finish_as(&self, labels: &str) -> String {
        self.listed(self.given(labels))
    }

    /// The text with every found item replaced by a placeholder such as `[PERSON_1]`.
    pub fn redacted(&self) -> String {
        spans::redact(&self.chars, &self.given("all"))
    }

    /// The text with what a profile finds replaced, "all" or "personal".
    pub fn redacted_as(&self, labels: &str) -> String {
        spans::redact(&self.chars, &self.given(labels))
    }
}
