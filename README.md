# Rakshya (रक्षा)

**Finds personal data in Nepali and English text, inside the browser. By [Fiste AI](https://fiste-ai.github.io/rakshya/).** Text in; names, places, phone numbers and identity numbers marked, or taken out. रक्षा means protection. The first release of this model was called Gopya.

- **Small.** 41 MB. It loads in a web page and reads a sentence in about 40 ms there, so the text can stay on the device. [Try it in your browser](https://fiste-ai.github.io/rakshya/).
- **Three ways of writing.** Nepali in Devanagari, Nepali in Latin letters, and English as it is written in Nepal. Hindi is experimental.
- **Exact.** Nepali writes case markers against a name, as in सीतालाई. Rakshya ends each span inside the word, so it takes out the name and leaves the grammar.
- **Made for Nepal.** Citizenship, national identity, PAN, passport, licence and voter numbers, bank accounts, number plates and phone numbers, with dates in both calendars and both scripts. Beside them the kinds that are standard everywhere: cards, IP addresses, web addresses, user names, passwords and keys. 21 labels in all.

There are two models with the same rules and labels: [fiste-ai/rakshya](https://huggingface.co/fiste-ai/rakshya), 41 MB, for browsers and phones, and [fiste-ai/rakshya-server](https://huggingface.co/fiste-ai/rakshya-server), 1.1 GB, for servers. This repository holds the code that runs them, the demo page and the benchmark.

## Benchmark

882 real texts in seven test sets that no system had seen: news, web pages, government pages and comments. The number is the F1 of exact spans over every kind of personal data in a set. Higher is better.

| System | Weights | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|---|
| **[Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya)** | 40M | **0.878** | 0.802 | 0.731 | **0.529** | 0.803 | 0.703 | **0.804** | 0.750 |
| **[Rakshya 0.2 server](https://huggingface.co/fiste-ai/rakshya-server)** | 278M | 0.870 | **0.815** | **0.740** | 0.520 | **0.813** | **0.740** | 0.800 | **0.757** |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 34M | 0.855 | 0.683 | 0.636 | 0.233 | 0.729 | 0.563 | 0.725 | 0.632 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 278M | 0.647 | 0.601 | 0.409 | 0.253 | 0.787 | 0.530 | 0.727 | 0.565 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 277M | 0.660 | 0.617 | 0.267 | 0.302 | 0.772 | 0.498 | 0.712 | 0.547 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 559M | 0.651 | 0.574 | 0.200 | 0.265 | 0.783 | 0.481 | 0.760 | 0.531 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 308M | 0.144 | 0.704 | 0.328 | 0.162 | 0.605 | 0.709 | 0.528 | 0.454 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 308M | 0.427 | 0.420 | 0.301 | 0.252 | 0.655 | 0.478 | 0.595 | 0.447 |

Of the 25 published systems we ran, none scores higher than Rakshya 0.2 on Nepali news, Nepali web pages, government pages, romanised comments, English news and Hindi news. Ahead of it is EU PII anonymisation v3 on English web pages (0.709 against 0.703).

Exact means that start, end and label are all right. The table has Rakshya, its first release and the 5 published systems with the highest mean. All 25 systems, the scores by kind, the false alarms and the method are in [BENCHMARK.md](BENCHMARK.md).

## Use it

```python
# pip install git+https://github.com/fiste-ai/rakshya
from rakshya import Rakshya

pii = Rakshya()        # fetches the small model once, 41 MB; Rakshya(model="server") for the large one
text = "मेरो नाम सीता थापा हो, फोन ९८४१२३४५६७।"
pii.find(text)         # [(9, 18, 'PERSON'), (27, 37, 'PHONE')]
pii.redact(text)       # मेरो नाम [PERSON_1] हो, फोन [PHONE_1]।
pii.redact("Mero naam Ramesh Adhikari ho, mobile 9801234567 ma call garnu.")
# Mero naam [PERSON_1] ho, mobile [PHONE_1] ma call garnu.
```

From a shell, `rakshya "some text"` prints the text with the personal data taken out, and `rakshya --spans` prints what was found. No PyTorch is needed: the package runs on ONNX Runtime.

In a web page:

```js
const dist = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.31.1/dist/";
const ort = await import(dist + "ort.wasm.min.mjs");
const { load } = await import("https://cdn.jsdelivr.net/gh/fiste-ai/rakshya@v0.2/docs/rakshya.js");
const rakshya = await load({ ort, model: "https://huggingface.co/fiste-ai/rakshya/resolve/v0.2", runtime: dist });
const { spans, redacted } = await rakshya.detect("मेरो नाम सीता थापा हो, फोन ९८४१२३४५६७।");
```

`docs/index.html` is a whole page that does this, live at [fiste-ai.github.io/rakshya](https://fiste-ai.github.io/rakshya/).

It finds `PERSON`, `LOCATION`, `ORGANIZATION`, `DATE`, `PHONE`, `EMAIL`, `URL`, `USERNAME`, `IP_ADDRESS`, `CITIZENSHIP_NO`, `NATIONAL_ID`, `TAX_ID`, `PASSPORT_NO`, `LICENSE_NO`, `VOTER_ID`, `ID_NUMBER`, `BANK_ACCOUNT`, `CARD_NUMBER`, `UPI_ID`, `VEHICLE_PLATE`, `SECRET`.

## What is here

| Path | Holds |
|---|---|
| `rakshya/` | The Python package: the rules (`rules.py`), the reading of the model's output (`spans.py`), the class that runs both (`runtime.py`) and the command line (`cli.py`). Needs `onnxruntime`, `tokenizers`, `numpy` and `huggingface_hub` |
| `rust/` | The same rules and reading in Rust, with the tokenizer. It is compiled to the WASM module in `docs/pkg/` |
| `docs/` | The demo page and the browser module `rakshya.js` |
| `BENCHMARK.md`, `benchmark/results.json` | Every score, and what it means |
| `ANNOTATION.md` | The guide the test labels follow: what is marked, and where a span starts and ends |
| `benchmark/labels/`, `benchmark/rebuild.py` | The labels of the seven test sets as character ranges, without the text, and a script that puts them back on texts you have obtained. Two of the sets come back exactly from public datasets |

To build the browser module again: `cd rust && cargo build --release --target wasm32-unknown-unknown --lib`, then `wasm-bindgen --target web --out-dir ../docs/pkg target/wasm32-unknown-unknown/release/rakshya.wasm` with wasm-bindgen 0.2.130.

## Limits

- It is a helper and not a guarantee. The small model misses about 4 in 100 characters of personal data in Nepali news, 6 on web pages, 7 in English news and 31 in comments written in Latin letters. Read the result before you rely on it.
- Nepali in Latin letters is the hardest of the three: 0.529 exact on real comments. People spell as they like there.
- Text copied out of tables is cut badly. Where one cell runs into the next, a date or a name is marked with the wrong start or end, and a row of figures can be taken for an address.
- Hindi is experimental. On 60 texts of Hindi news the small model scores 0.804.
- Identity numbers are tested mostly on made-up text. Public pages print phone numbers, e-mail addresses and the bank accounts of offices; they do not print citizenship, passport or licence numbers.
- The test sets are small, and each comes from one kind of source.

Code MIT, weights CC BY-NC 4.0, test labels CC BY 4.0; see `LICENSE` and `NOTICE.md`. Part of the training data is for non-commercial use, so there is no commercial licence for this version. Questions: [contact us](https://fiste-ai.github.io/contact/) or open an issue.
