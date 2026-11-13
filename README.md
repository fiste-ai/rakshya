# Gopya (गोप्य)

**Nepali PII detection that runs in the browser, by [Fiste AI](https://fiste-ai.github.io/gopya/).** Text in; names, places, phone numbers and identity numbers marked, or taken out. गोप्य means confidential.

- **Small.** 35 MB. It loads in a web page and reads a sentence in about 30 ms there, so the text can stay on the device. [Try it in your browser](https://fiste-ai.github.io/gopya/).
- **Exact.** Nepali writes case markers against a name, as in सीतालाई. Gopya ends each span inside the word, so it takes out the name and leaves the grammar.
- **Made for Nepal.** Citizenship, national identity, PAN, passport, licence and voter numbers, bank accounts, number plates, phone numbers, and dates in both calendars and both scripts.

The model is at [huggingface.co/fiste-ai/gopya](https://huggingface.co/fiste-ai/gopya). This repository holds the code that runs it, the demo page and the benchmark.

## Benchmark

Names of people, places and organisations in 215 sentences of Nepali news that no system had seen. Higher is better.

| Model | Weights | Exact | Whole words | Characters found |
|---|---|---|---|---|
| **[Gopya 0.1](https://huggingface.co/fiste-ai/gopya)** | 34M | **0.81** | **0.83** | 93% |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 277M | 0.70 | 0.81 | 89% |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 278M | 0.66 | **0.83** | **97%** |
| [WikiNEural multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 177M | 0.45 | 0.56 | 65% |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 177M | 0.34 | 0.68 | 77% |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 124M | 0.32 | 0.78 | 83% |

Exact: start, end and label all right. Whole words: the same after every span is widened to whole words, which forgives a case marker left on a name. Characters found: the share of the characters of names inside any span found. Over all four labels of this set, dates included, Gopya scores 0.81 exact and finds 94% of the characters.

The labels were written with the help of an AI assistant before any system was run, and are waiting for review by a native speaker, so the scores may move. The second test set, every system and the method are in [BENCHMARK.md](BENCHMARK.md).

## Use it

```python
# pip install onnxruntime tokenizers numpy huggingface_hub
import sys
from huggingface_hub import snapshot_download

folder = snapshot_download("fiste-ai/gopya")
sys.path.insert(0, folder)
from gopya import Gopya

pii = Gopya(folder)
text = "मेरो नाम सीता थापा हो, फोन ९८४१२३४५६७।"
pii.find(text)     # [(9, 18, 'PERSON'), (27, 37, 'PHONE')]
pii.redact(text)   # मेरो नाम [PERSON_1] हो, फोन [PHONE_1]।
```

In a web page, `docs/gopya.js` runs the same model with ONNX Runtime Web; `docs/index.html` is the example and is live at [fiste-ai.github.io/gopya](https://fiste-ai.github.io/gopya/).

## What is here

| Path | Holds |
|---|---|
| `gopya/` | The Python package: the rules (`rules.py`), the reading of the model's output (`spans.py`) and the class that runs both (`runtime.py`). Needs `onnxruntime`, `tokenizers` and `numpy` |
| `rust/` | The same rules and reading in Rust, with the tokenizer. It is compiled to the WASM module in `docs/pkg/` |
| `docs/` | The demo page and the browser module `gopya.js` |
| `benchmark/results.json` | Every score of `BENCHMARK.md` |

To build the browser module again: `cd rust && cargo build --release --target wasm32-unknown-unknown --lib`, then `wasm-bindgen --target web --out-dir ../docs/pkg target/wasm32-unknown-unknown/release/gopya.wasm` with wasm-bindgen 0.2.130.

## Limits

- It is a helper and not a guarantee. On news it misses about 6 in 100 characters of personal data. Read the result before you rely on it.
- It learned from news and from made-up forms and messages. On text copied from web pages, where table cells run together, it is weaker: 0.66 exact on 75 snippets from government sites, and for names alone three larger models do better there.
- The identity numbers are tested on made-up text, apart from a few real PAN and bank account numbers. Public pages do not print the others.
- Larger models find a little more. The best of them finds 97% of the characters of names in the news set, against 93% for Gopya, with spans that are less exact and 8 times the weights.

Code MIT, weights CC BY-NC 4.0; see `LICENSE` and `NOTICE.md`. The model learned from the EverestNER corpus, which is for non-commercial use, so there is no commercial licence for this version. Questions: [contact us](https://fiste-ai.github.io/contact/) or open an issue.
