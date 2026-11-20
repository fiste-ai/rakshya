# Rakshya (रक्षा)

**Finds personal data in Nepali, Hindi and English text, inside the browser. By [Fiste AI](https://fiste-ai.github.io/rakshya/).** Text in; names, places, phone numbers and identity numbers marked, or taken out. रक्षा means protection. The first release of this model was called Gopya.

- **Small.** 41 MB. It loads in a web page and reads a sentence in about 50 ms there, so the text can stay on the device. [Try it in your browser](https://fiste-ai.github.io/rakshya/).
- **Three languages in four kinds of writing.** Nepali in Devanagari and in Latin letters, Hindi in Devanagari, and English as it is written in Nepal.
- **Exact.** Nepali writes case markers against a name, as in सीतालाई. Rakshya ends each span inside the word, so it takes out the name and leaves the grammar.
- **Made for Nepal.** Citizenship, national identity, PAN, passport, licence and voter numbers, bank accounts, number plates and phone numbers, with dates in both calendars and both scripts. Beside them the kinds that are standard everywhere: cards, IP addresses, web addresses, user names, passwords and keys. 25 labels in all.

The model is at [fiste-ai/rakshya](https://huggingface.co/fiste-ai/rakshya) under the tag `v1.1`. This repository holds the code that runs it, the demo page and the labels of the test sets.

**New in 1.1: the weights are under Apache-2.0.** Release 1.0 was for non-commercial use, because three of its training sets were. Version 1.1 has the same labels, rules, code and size, and was trained again without those three sets: EverestNER, DanfeNER and CoNLL-2003. It scores as 1.0 does or a little higher on every test, within what another draw of test texts would move ([BENCHMARK.md](BENCHMARK.md)). Release 1.0 stays at the tag `v1.0`.

## Benchmark

1,034 real texts in seven test sets: news, web pages, government pages and comments. None of them is in any training data we used, and their labels were fixed before any system was run on them. The number is the F1 of exact spans over every kind of personal data in a set. Higher is better.

| System | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | **0.930** | **0.937** | **0.944** | **0.864** | **0.934** | **0.933** | 0.851 | **0.913** |
| [Rakshya 1.0](https://huggingface.co/fiste-ai/rakshya/tree/v1.0) | 0.914 | 0.933 | 0.943 | 0.858 | 0.924 | 0.915 | **0.855** | 0.906 |
| [Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya/tree/v0.2) | 0.889 | 0.816 | 0.863 | 0.524 | 0.892 | 0.790 | 0.797 | 0.796 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 0.849 | 0.727 | 0.704 | 0.218 | 0.724 | 0.638 | 0.789 | 0.664 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 0.718 | 0.597 | 0.506 | 0.264 | 0.817 | 0.460 | 0.757 | 0.588 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 0.775 | 0.566 | 0.353 | 0.269 | 0.855 | 0.499 | 0.762 | 0.583 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 0.764 | 0.552 | 0.302 | 0.280 | 0.852 | 0.498 | 0.802 | 0.578 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 0.601 | 0.494 | 0.272 | 0.203 | 0.635 | 0.430 | 0.631 | 0.467 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 0.390 | 0.452 | 0.336 | 0.274 | 0.672 | 0.519 | 0.578 | 0.460 |

None of the 25 published systems we ran scores higher than Rakshya 1.1 on any of the seven sets.

Exact means that start, end and label are all right. The table has Rakshya, the three releases before it and the 5 published systems with the highest mean. The sets were scored once for release 1.0, once more for this one after its model was fixed, and a third time for the lighter model below. All 25 published systems, the scores by kind, the false alarms and the method are in [BENCHMARK.md](BENCHMARK.md).

On [NepPIIBench](https://huggingface.co/datasets/fiste-ai/nepiibench), 380 held-out paragraphs with character offsets for 19 kinds of personal data, Rakshya 1.1 has a character F1 of 0.982 and an F1 of exact spans of 0.956. It learned from the training part of the same collection, most of which is published as [NepPIICorpus](https://huggingface.co/datasets/fiste-ai/nepiicorpus), as release 1.0 did and no system of others did, so this is a score on the kind of text it was trained for.

On 180 further cases of our own, a separate set that no version of Rakshya learned from, it gets 0.963 at the level of seven kinds that every system can be scored on. Rakshya 1.0 gets 0.951 there, Rakshya 0.2 0.921, and the best of the other published systems, EU PII anonymisation v3 of bards.ai, 0.727.

## A lighter model

[Rakshya 1.1 Lite](https://huggingface.co/fiste-ai/rakshya-lite) is the same detector with a network of 6 layers instead of 12: 30 MB instead of 41, and 46 percent of the time per text in a browser. It has the labels, the rules and the code of Rakshya 1.1, and its weights are under Apache-2.0 too. On the seven test sets it has a mean of 0.903 where Rakshya 1.1 has 0.913, on the practical test 0.948 against 0.956, and on the 180 cases 0.919 against 0.960. The table is in [BENCHMARK.md](BENCHMARK.md#rakshya-11-lite).

```python
from huggingface_hub import snapshot_download
from rakshya import Rakshya

pii = Rakshya(snapshot_download("fiste-ai/rakshya-lite", revision="v1.1"))
```

In a web page, give `load` the address `https://huggingface.co/fiste-ai/rakshya-lite/resolve/v1.1` as its `model`.

## Use it

```python
# pip install git+https://github.com/fiste-ai/rakshya
from rakshya import Rakshya

pii = Rakshya()        # fetches the model once, 41 MB
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
const { load } = await import("https://cdn.jsdelivr.net/gh/fiste-ai/rakshya@v1.1/docs/rakshya.js");
const rakshya = await load({ ort, model: "https://huggingface.co/fiste-ai/rakshya/resolve/v1.1", runtime: dist });
const { spans, redacted } = await rakshya.detect("मेरो नाम सीता थापा हो, फोन ९८४१२३४५६७।");
```

`docs/index.html` is a whole page that does this, live at [fiste-ai.github.io/rakshya](https://fiste-ai.github.io/rakshya/).

Two profiles decide what is returned. `labels="all"` returns every label; `labels="personal"` leaves places, organisations, dates and web addresses in the text, and also leaves the phone number and mailbox of an office and a number that is already masked. It finds `PERSON`, `LOCATION`, `ORGANIZATION`, `DATE`, `ADDRESS`, `DOB`, `PHONE`, `EMAIL`, `URL`, `DIGITAL_SECRET`, `NATIONAL_ID`, `TAX_ID`, `PASSPORT`, `DRIVER_LICENSE`, `VOTER_ID`, `BANK_ACCOUNT`, `CREDIT_CARD`, `PAYMENT_ID`, `MEDICAL_ID`, `EMPLOYEE_STUDENT_ID`, `PROPERTY_UTILITY_ID`, `VEHICLE_ID`, `ID_NUMBER`, `OFFICE_PHONE`, `OFFICE_EMAIL`.

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

- It is a helper and not a guarantee. The model finds 98 in 100 characters of personal data in Nepali news it had not seen, 97 on web pages, 98 in English news and 89 in comments written in Latin letters. Read the result before you rely on it.
- Nepali in Latin letters is the hardest of the four: 0.864 exact on real comments. People spell as they like there.
- Text copied out of tables is cut badly. Where one cell runs into the next, a date or a name is marked with the wrong start or end, and a row of figures can be taken for an address.
- On 104 texts of Hindi news the model scores 0.851. Hindi is the newest of the languages and has the fewest test texts.
- Identity numbers are tested mostly on paragraphs of fictional records. Public pages print phone numbers, e-mail addresses and the bank accounts of offices; they do not print citizenship, passport or licence numbers.
- The test sets are small, and each comes from one kind of source.

Code MIT, weights Apache-2.0, test labels CC BY 4.0; see `LICENSE` and `NOTICE.md`, which names the training sets and their terms. Release 1.0, at the tag `v1.0`, stays under CC BY-NC 4.0. Questions: [contact us](https://fiste-ai.github.io/contact/) or open an issue.
