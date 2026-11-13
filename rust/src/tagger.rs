//! The tokenizer and the step from the model's output to spans. See `gopya/tagger.py`.

use crate::spans::{clean_offsets, decode, tidy, to_word_start};
use crate::Span;
use serde::Deserialize;
use tokenizers::{Tokenizer, TruncationParams};

#[derive(Deserialize)]
struct Meta {
    labels: Vec<String>,
    max_trim: usize,
}

pub struct Tagger {
    tokenizer: Tokenizer,
    /// "O", then "B-" and "I-" for each label, in the order of the model's outputs.
    pub tags: Vec<String>,
    pub max_trim: usize,
}

/// Index of the largest value; the first one where several are equal, as numpy does.
fn argmax(row: &[f32]) -> usize {
    let mut best = 0;
    for (i, value) in row.iter().enumerate() {
        if *value > row[best] {
            best = i;
        }
    }
    best
}

impl Tagger {
    /// `tokenizer_json` and `tagger_json` are the files of those names in the model folder.
    pub fn new(tokenizer_json: &[u8], tagger_json: &str) -> Result<Tagger, String> {
        let mut tokenizer = Tokenizer::from_bytes(tokenizer_json).map_err(|e| e.to_string())?;
        let truncation = TruncationParams { max_length: 512, ..Default::default() };
        tokenizer.with_truncation(Some(truncation)).map_err(|e| e.to_string())?;
        tokenizer.with_padding(None);
        let meta: Meta = serde_json::from_str(tagger_json).map_err(|e| e.to_string())?;
        let mut tags = vec!["O".to_string()];
        for label in &meta.labels {
            tags.push(format!("B-{label}"));
            tags.push(format!("I-{label}"));
        }
        Ok(Tagger { tokenizer, tags, max_trim: meta.max_trim })
    }

    /// Token ids and the character range of each token.
    pub fn encode(&self, text: &str) -> Result<(Vec<u32>, Vec<(usize, usize)>), String> {
        let encoding = self.tokenizer.encode_char_offsets(text, true).map_err(|e| e.to_string())?;
        Ok((encoding.get_ids().to_vec(), encoding.get_offsets().to_vec()))
    }

    /// Spans from the tag and trim chosen for every token.
    pub fn spans(&self, text: &str, offsets: &[(usize, usize)], tag_ids: &[usize], trims: &[usize]) -> Vec<Span> {
        let chars: Vec<char> = text.chars().collect();
        let offsets = clean_offsets(&chars, offsets);
        let names: Vec<&str> = tag_ids.iter().map(|&i| self.tags[i].as_str()).collect();
        tidy(&chars, &to_word_start(&chars, &decode(&names, &offsets, Some(trims))))
    }

    /// Spans from the model's two outputs for one text, each a flat row-by-row array.
    pub fn spans_from_logits(&self, text: &str, offsets: &[(usize, usize)], logits: &[f32], trim_logits: &[f32]) -> Vec<Span> {
        let tag_ids: Vec<usize> = logits.chunks(self.tags.len()).map(argmax).collect();
        let trims: Vec<usize> = trim_logits.chunks(self.max_trim + 1).map(argmax).collect();
        self.spans(text, offsets, &tag_ids, &trims)
    }
}
