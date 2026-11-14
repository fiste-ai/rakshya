//! Nepali PII detection outside Python: the rules, the tokenizer and the span decoding.
//!
//! Every function here mirrors one in the Python package (`rakshya/rules.py`, `rakshya/spans.py`,
//! `rakshya/tagger.py`), and `python -m rakshya.parity` checks that the two give the same output.
//! Offsets are counted in code points, as in Python; the WASM interface turns them into
//! UTF-16 units, which is what a JavaScript string is indexed by.

pub mod rules;
pub mod spans;
pub mod tagger;
#[cfg(target_arch = "wasm32")]
mod web;

/// A found item: start, end (code points) and label.
pub type Span = (usize, usize, String);
