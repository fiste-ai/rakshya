//! Command line for checking this build against the Python code.
//!
//!     gopya rules                       text lines in, spans out
//!     gopya segments                    text lines in, piece ranges out
//!     gopya encode TOKENIZER TAGGER     text lines in, token ids and character ranges out
//!     gopya spans TOKENIZER TAGGER      text with the tag and trim of every token in, spans out
//!
//! Every input line is a JSON object with "text"; `spans` also needs "tag_ids" and "trims".
//! Every output line is JSON. TOKENIZER and TAGGER are tokenizer.json and tagger.json of a model.

use gopya::tagger::Tagger;
use gopya::{rules, spans};
use serde::Deserialize;
use std::io::{self, BufRead, Write};

#[derive(Deserialize)]
struct Line {
    text: String,
    #[serde(default)]
    tag_ids: Vec<usize>,
    #[serde(default)]
    trims: Vec<usize>,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(String::as_str).unwrap_or("");
    let tagger = if matches!(mode, "encode" | "spans") {
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
            _ => panic!("usage: gopya rules | segments | encode TOKENIZER TAGGER | spans TOKENIZER TAGGER"),
        };
        writeln!(out, "{}", answer.unwrap()).unwrap();
    }
}
