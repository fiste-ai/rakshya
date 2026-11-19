//! Command line for checking this build against the Python code.
//!
//!     rakshya rules                       text lines in, spans out
//!     rakshya segments                    text lines in, piece ranges out
//!     rakshya encode TOKENIZER TAGGER     text lines in, token ids and character ranges out
//!     rakshya spans TOKENIZER TAGGER      text with the tag and trim of every token in, spans out
//!     rakshya logits TOKENIZER TAGGER     text with the model's two outputs in, spans out, as the web page gets them
//!     rakshya given                       text with the spans of a tagger in, what is given out under each profile out
//!
//! Every input line is a JSON object with "text"; `spans` also needs "tag_ids" and "trims", `logits` needs
//! "logits" and "trim_logits", each a flat row-by-row array, and `given` needs "tagged", a list of [start, end, label].
//! Every output line is JSON. TOKENIZER and TAGGER are tokenizer.json and tagger.json of a model.

use rakshya::tagger::Tagger;
use rakshya::{kinds, rules, spans};
use serde::Deserialize;
use std::io::{self, BufRead, Write};

#[derive(Deserialize)]
struct Line {
    text: String,
    #[serde(default)]
    tag_ids: Vec<usize>,
    #[serde(default)]
    trims: Vec<usize>,
    #[serde(default)]
    logits: Vec<f32>,
    #[serde(default)]
    trim_logits: Vec<f32>,
    #[serde(default)]
    tagged: Vec<(usize, usize, String)>,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(String::as_str).unwrap_or("");
    let tagger = if matches!(mode, "encode" | "spans" | "logits") {
        let tokenizer = std::fs::read(&args[2]).expect("tokenizer.json");
        let meta = std::fs::read_to_string(&args[3]).expect("tagger.json");
        Some(Tagger::new(&tokenizer, &meta).expect("tokenizer"))
    } else {
        None
    };
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for line in io::stdin().lock().lines() {
        let line: Line = serde_json::from_str(&line.expect("input")).expect("a JSON object with \"text\"");
        let answer = match mode {
            "rules" => serde_json::to_string(&rules::find(&line.text)),
            "segments" => {
                let chars: Vec<char> = line.text.chars().collect();
                serde_json::to_string(&spans::segments(&chars, 320, 1200))
            }
            "encode" => {
                let (ids, offsets) = tagger.as_ref().unwrap().encode(&line.text).expect("encode");
                serde_json::to_string(&serde_json::json!({"ids": ids, "offsets": offsets}))
            }
            "spans" => {
                let tagger = tagger.as_ref().unwrap();
                let (_, offsets) = tagger.encode(&line.text).expect("encode");
                serde_json::to_string(&tagger.spans(&line.text, &offsets, &line.tag_ids, &line.trims))
            }
            "logits" => {
                let tagger = tagger.as_ref().unwrap();
                let (_, offsets) = tagger.encode(&line.text).expect("encode");
                serde_json::to_string(&tagger.spans_from_logits(&line.text, &offsets, &line.logits, &line.trim_logits))
            }
            "given" => {
                let chars: Vec<char> = line.text.chars().collect();
                let merged = spans::merge(&line.tagged, &rules::find(&line.text));
                serde_json::to_string(&serde_json::json!({"all": kinds::all(&chars, &merged), "personal": kinds::personal(&chars, &merged)}))
            }
            _ => panic!("usage: rakshya rules | segments | given | encode TOKENIZER TAGGER | spans TOKENIZER TAGGER | logits TOKENIZER TAGGER"),
        };
        writeln!(out, "{}", answer.unwrap()).unwrap();
    }
}
