# Rakshya benchmark

Version 0.2, 14 November 2026. Two models are scored here, each together with the rules: the small one for browsers (41 MB, 40 million weights) and the server model (1.1 GB, 278 million weights). Beside them are 25 published systems, each run the way its authors publish it. Every number is also in [`benchmark/results.json`](benchmark/results.json).

## How a system is scored

A system reads a text and returns spans: a start, an end and a label.

- **Exact** is the F1 of spans whose start, end and label are all right. One character too many, such as a case marker left on a name, makes a span wrong. Every table here shows this number.
- **Characters found** is the share of the expected characters that lie inside any found span, whatever its label. For a tool that takes personal data out of a text, this is the number that says how much is left in. It is in `results.json` for every system, with the score on whole words.

The systems do not share one set of labels, so each one's labels are mapped to a common set: people, places, organisations, dates, phone numbers, e-mail addresses, web addresses, user names, IP addresses, passwords and keys, and one label for every identifying number of whatever kind. A label of a system that has a counterpart in this set is mapped to it.

Three scores come out of that. **All labels** counts everything a test set marks, so a system with no label for dates loses the dates. This is what a user of the system gets on that text, and it is the score of the first table. **Names** counts people, places and organisations, which nearly every system has. **Own labels** counts only the labels a system has, which says how well it does what it was built for.

Some published models can be read in more than one way: every token by its own label, or every word by the label of its first token. Such a model is read each way and gets the reading that scores best on its own labels for that set. Rakshya is read one way.

Where the labelling guide allows two readings of a text, both are accepted and a system is scored against the one it matches best.

## The test sets

Seven sets of real text, 882 texts with 2,248 spans. None of these texts was in any training data we used, and no system had been run on them when they were labelled.

| Set | Language | Texts | Sources | Spans | Agreement of three passes | Texts with a second reading |
|---|---|---|---|---|---|---|
| News | Nepali | 175 | 35 | 286 | 0.997 | 1 |
| Web pages | Nepali | 88 | 88 | 653 | 0.964 | 27 |
| Government pages | Nepali | 71 | 71 | 315 | 0.996 | 3 |
| Comments | Nepali in Latin letters | 300 | 300 | 204 | 0.984 | 7 |
| News | English | 108 | 31 | 202 | 0.995 | 3 |
| Web pages | English | 80 | 80 | 495 | 0.913 | 27 |
| News | Hindi | 60 | 12 | 93 | 0.993 | 3 |

The news comes from news sites of Nepal and, for Hindi, of India; the web pages from sites of schools, hospitals, cooperatives, associations, news rooms and companies in Nepal that list people and how to reach them; the government pages from a public crawl of government sites; and the comments from a public collection of comments on videos. A text is a sentence of news, a comment, or a piece of a page of about 300 characters. Text from web pages is what a crawler took out of them, with table cells run together.

The labels follow a written guide, [ANNOTATION.md](ANNOTATION.md). Each set was labelled three times by an AI assistant (Claude), in separate runs that saw the guide and the texts and neither each other's labels nor the output of any system. The differences were settled against the guide, and the reason for each was written down. "Agreement of three passes" is the mean F1 between pairs of passes.

The text is not published: the news belongs to its publishers, and the pages and comments hold the names and phone numbers of real people. The labels are published, without the text.

## The test labels

[`benchmark/labels/`](benchmark/labels) has one file for each test set. For every text it gives where the text came from, its length, the SHA-256 of its UTF-8 bytes and the labelled spans as character ranges. Where the guide accepts a second reading of a text, that reading is there as well, under `also`. A range counts Unicode code points, and its end is exclusive.

[`benchmark/rebuild.py`](benchmark/rebuild.py) puts the labels back on texts that you have obtained. It keeps a text only when its hash matches, so a text that has changed is left out and named.

| Set | Label file | Texts | Where the texts are |
|---|---|---|---|
| News, Nepali | [`real-news-v2.json`](benchmark/labels/real-news-v2.json) | 175 | news articles, each named by its address |
| Web pages, Nepali | [`real-web-v0.json`](benchmark/labels/real-web-v0.json) | 88 | web pages, each named by its address, with the range of the piece |
| Government pages, Nepali | [`real-gov-v1.json`](benchmark/labels/real-gov-v1.json) | 71 | [voidash/previllage-nepal-gov-corpus](https://huggingface.co/datasets/voidash/previllage-nepal-gov-corpus), `data/documents.parquet` at revision `004ce5f` |
| Comments, Nepali in Latin letters | [`real-roman-v0.json`](benchmark/labels/real-roman-v0.json) | 300 | [Boredoom17/Nepali-Flow-Roman](https://huggingface.co/datasets/Boredoom17/Nepali-Flow-Roman), `nepali_corpus_roman.parquet` at revision `347cf23` |
| News, English | [`real-en-v0.json`](benchmark/labels/real-en-v0.json) | 108 | news articles, each named by its address |
| Web pages, English | [`real-enweb-v0.json`](benchmark/labels/real-enweb-v0.json) | 80 | web pages, each named by its address, with the range of the piece |
| News, Hindi | [`real-hi-v0.json`](benchmark/labels/real-hi-v0.json) | 60 | news articles, each named by its address |

The government pages and the comments were cut from public datasets, each fixed by its revision, so these two sets come back exactly: 371 of the 882 texts.

```
pip install pyarrow
curl -LO https://huggingface.co/datasets/voidash/previllage-nepal-gov-corpus/resolve/004ce5f80a21746c9d4788434b33896f97ecc860/data/documents.parquet
python benchmark/rebuild.py benchmark/labels/real-gov-v1.json --parquet documents.parquet
curl -LO https://huggingface.co/datasets/Boredoom17/Nepali-Flow-Roman/resolve/347cf23f7084f7991c93329a27f9d4df01ba6ba5/nepali_corpus_roman.parquet
python benchmark/rebuild.py benchmark/labels/real-roman-v0.json --parquet nepali_corpus_roman.parquet
```

Web pages and news articles change or go away, so the other five sets may not come back in full; the script says which texts it found. The label files are under CC BY 4.0.

## Results on all labels

| System | Weights | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|---|
| **[Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya)** | 40M | **0.878** | 0.802 | 0.731 | **0.529** | 0.803 | 0.703 | **0.804** | 0.750 |
| **[Rakshya 0.2 server](https://huggingface.co/fiste-ai/rakshya-server)** | 278M | 0.870 | **0.815** | **0.740** | 0.520 | **0.813** | **0.740** | 0.800 | **0.757** |
| The rules of Rakshya alone |  | 0.028 | 0.400 | 0.620 | 0.010 | 0.029 | 0.376 | 0.176 | 0.234 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 34M | 0.855 | 0.683 | 0.636 | 0.233 | 0.729 | 0.563 | 0.725 | 0.632 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 278M | 0.647 | 0.601 | 0.409 | 0.253 | 0.787 | 0.530 | 0.727 | 0.565 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 277M | 0.660 | 0.617 | 0.267 | 0.302 | 0.772 | 0.498 | 0.712 | 0.547 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 559M | 0.651 | 0.574 | 0.200 | 0.265 | 0.783 | 0.481 | 0.760 | 0.531 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 308M | 0.144 | 0.704 | 0.328 | 0.162 | 0.605 | 0.709 | 0.528 | 0.454 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 308M | 0.427 | 0.420 | 0.301 | 0.252 | 0.655 | 0.478 | 0.595 | 0.447 |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 177M | 0.327 | 0.489 | 0.230 | 0.200 | 0.701 | 0.435 | 0.684 | 0.438 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 57M | 0.518 | 0.513 | 0.182 | 0.185 | 0.608 | 0.445 | 0.595 | 0.435 |
| [WikiNEuRal multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 177M | 0.485 | 0.403 | 0.127 | 0.191 | 0.741 | 0.463 | 0.595 | 0.429 |
| [PII Redactor small](https://huggingface.co/Horizon-Labs/pii-redactor-small) (Horizon Labs) | 141M | 0.339 | 0.453 | 0.267 | 0.102 | 0.588 | 0.566 | 0.288 | 0.372 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector) (IIT Guwahati) | 505M | 0.283 | 0.527 | 0.228 | 0.229 | 0.529 | 0.323 | 0.435 | 0.365 |
| [Chitragupta](https://huggingface.co/LatentAILabs/chitragupta-pii-indic) (Latent AI Labs) | 559M | 0.260 | 0.593 | 0.284 | 0.182 | 0.367 | 0.423 | 0.281 | 0.342 |
| [CBX Indic PII 58M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-58M) (CobuildX) | 58M | 0.084 | 0.572 | 0.426 | 0.137 | 0.285 | 0.473 | 0.391 | 0.338 |
| [IndicPHI MuRIL](https://huggingface.co/sach3v/indicphi-muril-pii) (sach3v) | 238M | 0.200 | 0.372 | 0.322 | 0.238 | 0.436 | 0.328 | 0.101 | 0.285 |
| [CBX Indic PII 17M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-17M) (CobuildX) | 17M | 0.034 | 0.465 | 0.379 | 0.107 | 0.250 | 0.482 | 0.231 | 0.278 |
| [GLiNER multi PII](https://huggingface.co/urchade/gliner_multi_pii-v1) (urchade) | 289M | 0.006 | 0.178 | 0.231 | 0.143 | 0.522 | 0.397 | 0.222 | 0.243 |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) (iiiorg) | 278M | 0.234 | 0.213 | 0.193 | 0.024 | 0.501 | 0.358 | 0.144 | 0.238 |
| [Presidio](https://github.com/data-privacy-stack/presidio) (Microsoft) |  | 0.005 | 0.329 | 0.251 | 0.056 | 0.476 | 0.449 | 0.071 | 0.234 |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 124M | 0.285 | 0.519 | 0.281 | 0.000 | 0.000 | 0.004 | 0.548 | 0.234 |
| [Privacy Filter](https://huggingface.co/openai/privacy-filter) (OpenAI) | 1399M | 0.061 | 0.331 | 0.250 | 0.040 | 0.231 | 0.331 | 0.040 | 0.183 |
| [GLiNER PII edge](https://huggingface.co/knowledgator/gliner-pii-edge-v1.0) (Knowledgator) | 45M | 0.000 | 0.128 | 0.123 | 0.045 | 0.447 | 0.344 | 0.019 | 0.158 |
| [Smart PII Redactor](https://huggingface.co/Mozilla/smart-pii-redactor-v1-onnx) (Mozilla) | 74 MB | 0.000 | 0.040 | 0.165 | 0.109 | 0.507 | 0.231 | 0.020 | 0.153 |
| [BERT-small PII detection](https://huggingface.co/gravitee-io/bert-small-pii-detection) (Gravitee) | 29M | 0.003 | 0.080 | 0.053 | 0.064 | 0.503 | 0.324 | 0.005 | 0.148 |
| [Rampart](https://huggingface.co/nationaldesignstudio/rampart) (National Design Studio) | 15 MB | 0.000 | 0.095 | 0.053 | 0.065 | 0.425 | 0.386 | 0.000 | 0.146 |
| [mmBERT-small PII redaction](https://huggingface.co/balticml/mmbert-small-pii-redaction) (BalticML) | 36 MB | 0.000 | 0.074 | 0.019 | 0.028 | 0.103 | 0.291 | 0.019 | 0.076 |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) (Saugatkafley) | 66M | 0.022 | 0.042 | 0.036 | 0.029 | 0.065 | 0.063 | 0.092 | 0.050 |

The best number of a column is in bold. Of the 25 published systems we ran, none scores higher than Rakshya 0.2 on Nepali news, Nepali web pages, government pages, romanised comments, English news and Hindi news. Ahead of it is EU PII anonymisation v3 on English web pages (0.709 against 0.703).

The sets are small, so a score would move with other texts. For the two models of Rakshya, the range in which 95% of the scores fall when the sources of a set are drawn again with replacement:

| System | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) |
|---|---|---|---|---|---|---|---|
| **[Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya)** | 0.878 (0.80 to 0.94) | 0.802 (0.76 to 0.84) | 0.731 (0.65 to 0.81) | 0.529 (0.47 to 0.58) | 0.803 (0.73 to 0.87) | 0.703 (0.63 to 0.79) | 0.804 (0.73 to 0.86) |
| **[Rakshya 0.2 server](https://huggingface.co/fiste-ai/rakshya-server)** | 0.870 (0.80 to 0.93) | 0.815 (0.77 to 0.86) | 0.740 (0.66 to 0.81) | 0.520 (0.45 to 0.58) | 0.813 (0.75 to 0.87) | 0.740 (0.64 to 0.83) | 0.800 (0.72 to 0.86) |

## Names only

People, places and organisations.

| System | Weights | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|---|
| **[Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya)** | 40M | **0.881** | 0.770 | 0.637 | **0.491** | 0.801 | 0.668 | 0.776 | 0.718 |
| **[Rakshya 0.2 server](https://huggingface.co/fiste-ai/rakshya-server)** | 278M | 0.871 | **0.789** | **0.667** | 0.490 | **0.812** | **0.690** | 0.767 | **0.726** |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 34M | 0.862 | 0.623 | 0.565 | 0.213 | 0.724 | 0.433 | 0.709 | 0.590 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 278M | 0.654 | 0.647 | 0.532 | 0.264 | 0.801 | 0.495 | 0.783 | 0.597 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 277M | 0.671 | 0.746 | 0.454 | 0.317 | 0.785 | 0.602 | 0.773 | 0.621 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 559M | 0.663 | 0.692 | 0.332 | 0.276 | 0.796 | 0.579 | **0.828** | 0.595 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 308M | 0.143 | 0.644 | 0.246 | 0.165 | 0.618 | 0.642 | 0.504 | 0.423 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 308M | 0.459 | 0.436 | 0.159 | 0.206 | 0.665 | 0.504 | 0.651 | 0.440 |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 177M | 0.340 | 0.605 | 0.407 | 0.186 | 0.763 | 0.556 | 0.667 | 0.503 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 57M | 0.530 | 0.585 | 0.209 | 0.191 | 0.618 | 0.434 | 0.657 | 0.460 |
| [WikiNEuRal multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 177M | 0.494 | 0.499 | 0.223 | 0.199 | 0.753 | 0.572 | 0.649 | 0.484 |
| [PII Redactor small](https://huggingface.co/Horizon-Labs/pii-redactor-small) (Horizon Labs) | 141M | 0.349 | 0.499 | 0.170 | 0.090 | 0.604 | 0.568 | 0.269 | 0.364 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector) (IIT Guwahati) | 505M | 0.289 | 0.417 | 0.252 | 0.243 | 0.538 | 0.048 | 0.481 | 0.324 |
| [Chitragupta](https://huggingface.co/LatentAILabs/chitragupta-pii-indic) (Latent AI Labs) | 559M | 0.248 | 0.588 | 0.479 | 0.191 | 0.374 | 0.434 | 0.302 | 0.374 |
| [CBX Indic PII 58M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-58M) (CobuildX) | 58M | 0.088 | 0.464 | 0.152 | 0.119 | 0.281 | 0.412 | 0.305 | 0.260 |
| [IndicPHI MuRIL](https://huggingface.co/sach3v/indicphi-muril-pii) (sach3v) | 238M | 0.206 | 0.350 | 0.314 | 0.256 | 0.450 | 0.224 | 0.118 | 0.274 |
| [CBX Indic PII 17M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-17M) (CobuildX) | 17M | 0.037 | 0.307 | 0.092 | 0.109 | 0.263 | 0.377 | 0.202 | 0.198 |
| [GLiNER multi PII](https://huggingface.co/urchade/gliner_multi_pii-v1) (urchade) | 289M | 0.007 | 0.074 | 0.082 | 0.142 | 0.538 | 0.299 | 0.067 | 0.173 |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) (iiiorg) | 278M | 0.242 | 0.189 | 0.117 | 0.040 | 0.510 | 0.343 | 0.167 | 0.230 |
| [Presidio](https://github.com/data-privacy-stack/presidio) (Microsoft) |  | 0.000 | 0.041 | 0.050 | 0.047 | 0.548 | 0.441 | 0.019 | 0.164 |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 124M | 0.309 | 0.645 | 0.508 | 0.000 | 0.000 | 0.006 | 0.617 | 0.298 |
| [Privacy Filter](https://huggingface.co/openai/privacy-filter) (OpenAI) | 1399M | 0.041 | 0.297 | 0.072 | 0.042 | 0.239 | 0.267 | 0.046 | 0.144 |
| [GLiNER PII edge](https://huggingface.co/knowledgator/gliner-pii-edge-v1.0) (Knowledgator) | 45M | 0.000 | 0.069 | 0.019 | 0.071 | 0.491 | 0.301 | 0.024 | 0.139 |
| [Smart PII Redactor](https://huggingface.co/Mozilla/smart-pii-redactor-v1-onnx) (Mozilla) | 74 MB | 0.000 | 0.029 | 0.000 | 0.095 | 0.519 | 0.310 | 0.024 | 0.140 |
| [BERT-small PII detection](https://huggingface.co/gravitee-io/bert-small-pii-detection) (Gravitee) | 29M | 0.003 | 0.026 | 0.000 | 0.060 | 0.538 | 0.227 | 0.000 | 0.122 |
| [Rampart](https://huggingface.co/nationaldesignstudio/rampart) (National Design Studio) | 15 MB | 0.000 | 0.042 | 0.014 | 0.067 | 0.434 | 0.366 | 0.000 | 0.132 |
| [mmBERT-small PII redaction](https://huggingface.co/balticml/mmbert-small-pii-redaction) (BalticML) | 36 MB | 0.000 | 0.019 | 0.000 | 0.030 | 0.118 | 0.303 | 0.000 | 0.067 |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) (Saugatkafley) | 66M | 0.022 | 0.048 | 0.030 | 0.031 | 0.067 | 0.083 | 0.105 | 0.055 |

## Each published system on its own labels

Only the labels a system has are counted, so a model for names is not marked down for the phone numbers it was never meant to find.

| System | Weights | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|---|
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 34M | **0.855** | 0.687 | **0.646** | 0.234 | 0.729 | 0.564 | 0.725 | **0.634** |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 559M | 0.663 | 0.692 | 0.332 | 0.276 | **0.796** | 0.579 | 0.828 | 0.595 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 277M | 0.660 | **0.718** | 0.329 | **0.302** | 0.778 | 0.590 | 0.712 | 0.584 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 278M | 0.647 | 0.601 | 0.409 | 0.253 | 0.787 | 0.530 | 0.727 | 0.565 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 57M | 0.650 | 0.576 | 0.234 | 0.194 | 0.668 | 0.479 | **0.830** | 0.519 |
| [WikiNEuRal multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 177M | 0.494 | 0.499 | 0.223 | 0.199 | 0.753 | 0.572 | 0.649 | 0.484 |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 177M | 0.327 | 0.571 | 0.286 | 0.201 | 0.706 | 0.537 | 0.684 | 0.473 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 308M | 0.144 | 0.704 | 0.328 | 0.162 | 0.605 | **0.709** | 0.528 | 0.454 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 308M | 0.427 | 0.420 | 0.301 | 0.252 | 0.655 | 0.478 | 0.595 | 0.447 |
| [Chitragupta](https://huggingface.co/LatentAILabs/chitragupta-pii-indic) (Latent AI Labs) | 559M | 0.351 | 0.660 | 0.317 | 0.187 | 0.419 | 0.456 | 0.366 | 0.394 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector) (IIT Guwahati) | 505M | 0.289 | 0.548 | 0.298 | 0.243 | 0.534 | 0.330 | 0.481 | 0.389 |
| [CBX Indic PII 58M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-58M) (CobuildX) | 58M | 0.117 | 0.628 | 0.462 | 0.140 | 0.317 | 0.505 | 0.495 | 0.380 |
| [PII Redactor small](https://huggingface.co/Horizon-Labs/pii-redactor-small) (Horizon Labs) | 141M | 0.339 | 0.453 | 0.267 | 0.102 | 0.588 | 0.566 | 0.288 | 0.372 |
| [CBX Indic PII 17M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-17M) (CobuildX) | 17M | 0.046 | 0.513 | 0.409 | 0.110 | 0.277 | 0.509 | 0.301 | 0.310 |
| [IndicPHI MuRIL](https://huggingface.co/sach3v/indicphi-muril-pii) (sach3v) | 238M | 0.200 | 0.372 | 0.322 | 0.239 | 0.436 | 0.328 | 0.101 | 0.285 |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) (iiiorg) | 278M | 0.306 | 0.243 | 0.218 | 0.024 | 0.558 | 0.383 | 0.193 | 0.275 |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 124M | 0.285 | 0.612 | 0.350 | 0.000 | 0.000 | 0.005 | 0.548 | 0.257 |
| [Presidio](https://github.com/data-privacy-stack/presidio) (Microsoft) |  | 0.007 | 0.368 | 0.273 | 0.057 | 0.519 | 0.475 | 0.089 | 0.256 |
| [GLiNER multi PII](https://huggingface.co/urchade/gliner_multi_pii-v1) (urchade) | 289M | 0.006 | 0.178 | 0.231 | 0.143 | 0.522 | 0.397 | 0.222 | 0.243 |
| [Privacy Filter](https://huggingface.co/openai/privacy-filter) (OpenAI) | 1399M | 0.082 | 0.364 | 0.270 | 0.041 | 0.269 | 0.355 | 0.055 | 0.205 |
| [Smart PII Redactor](https://huggingface.co/Mozilla/smart-pii-redactor-v1-onnx) (Mozilla) | 74 MB | 0.000 | 0.051 | 0.204 | 0.109 | 0.507 | 0.276 | 0.020 | 0.167 |
| [Rampart](https://huggingface.co/nationaldesignstudio/rampart) (National Design Studio) | 15 MB | 0.000 | 0.115 | 0.082 | 0.068 | 0.474 | 0.422 | 0.000 | 0.166 |
| [GLiNER PII edge](https://huggingface.co/knowledgator/gliner-pii-edge-v1.0) (Knowledgator) | 45M | 0.000 | 0.128 | 0.123 | 0.045 | 0.447 | 0.344 | 0.019 | 0.158 |
| [BERT-small PII detection](https://huggingface.co/gravitee-io/bert-small-pii-detection) (Gravitee) | 29M | 0.003 | 0.080 | 0.053 | 0.064 | 0.503 | 0.324 | 0.005 | 0.148 |
| [mmBERT-small PII redaction](https://huggingface.co/balticml/mmbert-small-pii-redaction) (BalticML) | 36 MB | 0.000 | 0.085 | 0.022 | 0.029 | 0.111 | 0.306 | 0.026 | 0.082 |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) (Saugatkafley) | 66M | 0.022 | 0.047 | 0.043 | 0.029 | 0.066 | 0.081 | 0.092 | 0.054 |

## By kind of personal data

The small model, exact F1 with the number of spans in brackets.

| Kind | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) |
|---|---|---|---|---|---|---|---|
| People | 0.991 (57) | 0.869 (240) | 0.773 (58) | 0.439 (119) | 0.948 (56) | 0.751 (153) | 0.850 (19) |
| Places | 0.881 (125) | 0.764 (121) | 0.449 (24) | 0.643 (60) | 0.878 (104) | 0.633 (131) | 0.873 (32) |
| Organisations | 0.815 (94) | 0.528 (98) | 0.554 (42) | 0.333 (9) | 0.440 (35) | 0.532 (56) | 0.610 (28) |
| Phone numbers |  | 0.948 (127) | 1.000 (51) |  |  | 0.892 (105) |  |
| Dates | 0.800 (10) | 0.564 (37) | 0.643 (104) | 0.941 (16) | 0.750 (4) | 0.432 (77) | 0.966 (14) |
| E-mail addresses |  | 1.000 (26) | 1.000 (26) |  |  | 0.962 (40) |  |
| Web addresses |  | 0.933 (8) | 1.000 (10) |  |  | 0.667 (1) |  |
| Identifying numbers |  | 1.000 (2) |  |  | 1.000 (3) |  |  |
| User names |  |  |  | 1.000 (1) |  |  |  |

The server model:

| Kind | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) |
|---|---|---|---|---|---|---|---|
| People | 0.974 (57) | 0.873 (240) | 0.807 (58) | 0.434 (119) | 0.957 (56) | 0.777 (153) | 0.791 (19) |
| Places | 0.897 (125) | 0.808 (119) | 0.528 (24) | 0.683 (60) | 0.879 (104) | 0.667 (130) | 0.899 (32) |
| Organisations | 0.774 (94) | 0.562 (99) | 0.562 (42) | 0.143 (9) | 0.460 (35) | 0.533 (60) | 0.600 (28) |
| Dates | 0.842 (10) | 0.605 (37) | 0.640 (106) | 0.848 (16) | 0.857 (4) | 0.742 (99) | 1.000 (14) |
| Phone numbers |  | 0.948 (127) | 0.990 (51) |  |  | 0.878 (105) |  |
| E-mail addresses |  | 0.963 (26) | 1.000 (26) |  |  | 0.894 (40) |  |
| Web addresses |  | 0.750 (8) | 1.000 (10) |  |  | 0.667 (1) |  |
| Identifying numbers |  | 1.000 (3) |  |  | 1.000 (3) |  |  |
| User names |  |  |  | 1.000 (1) |  |  |  |

Where a text has two accepted readings, each model is held against the one it matches best, so the number of spans of a kind can differ between the two tables.

Public pages print phone numbers, e-mail addresses, the bank accounts of offices and a few tax numbers. They do not print citizenship, passport, licence or voter numbers, so those kinds are tested on made-up text only: the traps below, and the test part of our generator.

## False alarms

On the texts of a set that have nothing to mark, the spans a system marks for every 1,000 words. Lower is better.

| System | News (ne), 48 texts | Web (ne), 4 texts | Government (ne), 4 texts | Comments (ne, Latin), 148 texts | News (en), 26 texts | Web (en), 7 texts | News (hi), 20 texts |
|---|---|---|---|---|---|---|---|
| **[Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya)** | 5.73 | 0.0 | 37.74 | 30.69 | 8.55 | 7.87 | 9.2 |
| **[Rakshya 0.2 server](https://huggingface.co/fiste-ai/rakshya-server)** | 2.87 | 0.0 | 37.74 | 28.95 | 0.0 | 7.87 | 9.2 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 4.3 | 14.71 | 56.6 | 108.28 | 29.91 | 43.31 | 15.34 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 12.89 | 0.0 | 150.94 | 34.74 | 10.68 | 55.12 | 6.13 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 5.73 | 0.0 | 66.04 | 23.74 | 8.55 | 47.24 | 0.0 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 4.3 | 7.35 | 47.17 | 37.06 | 6.41 | 43.31 | 0.0 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 0.0 | 0.0 | 0.0 | 33.01 | 21.37 | 39.37 | 0.0 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 10.03 | 22.06 | 169.81 | 17.95 | 0.0 | 11.81 | 3.07 |

## Against the first release

The first release, Gopya 0.1, was tested on three sets of Nepali text. Their errors were read while this release was built, so they are no longer unseen and are kept out of the tables above. They show that the new model did not get worse at what the old one did. The scores are against the labels as they were first written, at the labels release 0.1 had.

| Set | Rakshya 0.2 | Rakshya 0.2 server | Gopya 0.1 |
|---|---|---|---|
| News of release 0.1 | 0.861 | 0.883 | 0.814 |
| Government pages of release 0.1 | 0.805 | 0.815 | 0.664 |
| Older news | 0.921 | 0.915 | 0.865 |

## Traps

Short texts written by hand to be hard: forms, messages, numbers without a keyword, the kinds that are new in this release, Nepali in Latin letters and English.

| System | Weights | Traps of release 0.1 (Nepali) | New traps (Nepali, English, mixed) |
|---|---|---|---|
| **[Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya)** | 40M | 0.913 | 0.912 |
| **[Rakshya 0.2 server](https://huggingface.co/fiste-ai/rakshya-server)** | 278M | **0.933** | **0.935** |
| The rules of Rakshya alone |  | 0.297 | 0.707 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 34M | 0.878 | 0.537 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 278M | 0.654 | 0.500 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 277M | 0.612 | 0.380 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 559M | 0.637 | 0.330 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 308M | 0.374 | 0.546 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 308M | 0.560 | 0.509 |

## Public test sets

The test parts of public sets. Rakshya was trained on the training parts of these sets, or on samples of them, so they say that what was taught was learned. Each is scored on the labels it marks.

| Test set | Language | Texts | Rakshya 0.2 | Rakshya 0.2 server | Best published system we ran |
|---|---|---|---|---|---|
| `everestner, names` | ne | 1,950 | 0.867 | 0.872 | XLM-R large, CoNLL-2003 0.647 |
| `everestner, our labels` | ne | 1,950 | 0.883 | 0.889 | XLM-R large, CoNLL-2003 0.646 |
| `danfe` | ne | 2,299 | 0.767 | 0.783 | XLM-R large, CoNLL-2003 0.582 |
| `indicphi-ne` | ne | 787 | 0.983 | 0.989 | IndicPHI MuRIL 0.854 |
| `conll03` | en | 3,453 | 0.908 | 0.918 | XLM-R base NER HRL 0.903 |
| `wnut17` | en | 1,293 | 0.544 | 0.575 | WikiNEuRal multilingual NER 0.459 |
| `btc` | en | 2,000 | 0.796 | 0.813 | GLiNER multi PII 0.597 |
| `fewnerd` | en | 3,000 | 0.777 | 0.790 | XLM-R large, CoNLL-2003 0.741 |
| `tab` | en | 1,806 | 0.960 | 0.962 | CBX Indic PII 58M 0.784 |
| `nemotron` | en | 6,875 | 0.960 | 0.967 | PII Redactor small 0.915 |
| `indicphi-en` | en | 697 | 0.961 | 0.967 | IndicPHI MuRIL 0.812 |
| `maskara-real` | en | 2,600 | 0.949 | 0.955 | Chitragupta 0.822 |
| `hiner` | hi | 3,999 | 0.906 | 0.912 | XLM-R large, CoNLL-2003 0.780 |
| `indicphi-hi` | hi | 752 | 0.982 | 0.986 | IndicPHI MuRIL 0.848 |

Public sets of which nothing was used for training:

| Test set | Language | Texts | Rakshya 0.2 | Rakshya 0.2 server | Best published system we ran |
|---|---|---|---|---|---|
| `classer-ne` | ne | 1,000 | 0.547 | 0.572 | AWED-PII-Protector 0.889 |
| `spy-legal` | en | 1,000 | 0.446 | 0.451 | EU PII anonymisation v3 0.508 |
| `spy-medical` | en | 1,000 | 0.450 | 0.455 | EU PII anonymisation v3 0.518 |
| `gretel` | en | 5,000 | 0.778 | 0.800 | PII Redactor small 0.874 |
| `ai4privacy-en` | en | 3,000 | 0.798 | 0.797 | PII Redactor small 0.905 |
| `indicpiidetx-en` | en | 897 | 0.897 | 0.909 | CBX Indic PII 58M 0.934 |
| `ylemis-en` | en | 5,269 | 0.953 | 0.950 | CBX Indic PII 58M 0.894 |
| `redactionbench` | en | 200 | masks 76%, 57% of it rightly | masks 80%, 57% of it rightly | Chitragupta masks 84%, 73% of it rightly |
| `ai4privacy-hi` | hi | 2,000 | 0.798 | 0.783 | EU PII anonymisation v3 0.913 |
| `indicpiidetx-hi` | hi | 304 | 0.845 | 0.872 | CBX Indic PII 58M 0.891 |
| `indicpiidetx-hi-latn` | hi-latn | 303 | 0.814 | 0.843 | CBX Indic PII 58M 0.903 |
| `ylemis-hi` | hi | 1,621 | 0.928 | 0.979 | CBX Indic PII 58M 0.900 |
| `ylemis-mixed` | hi-en | 946 | 0.949 | 0.919 | EU PII anonymisation v3 0.882 |
| `naamapadam-hi` | hi | 864 | 0.794 | 0.795 | XLM-R large, CoNLL-2003 0.800 |

A published system may have been trained on a set of these tables. Most of them are made by a generator, and a model does well on the generator it was trained on.

## In the browser

Chromium 155, headless, WASM, no GPU, on the same laptop as the other timings. Exact F1 on all labels with our own 21 labels kept apart, which is why the numbers differ from the first table.

| Set | Texts | Python package | Browser, 1 thread | Same spans as Python | One text, 1 thread | One text, 4 threads | Tab |
|---|---|---|---|---|---|---|---|
| News (Nepali) | 175 | 0.878 | 0.878 | 175 of 175 | 39 ms | 14 ms | 548 MB |
| Web pages (Nepali) | 88 | 0.802 | 0.802 | 88 of 88 | 112 ms | 35 ms | 571 MB |
| Comments (Nepali in Latin letters) | 300 | 0.529 | 0.529 | 300 of 300 | 25 ms | 10 ms | 565 MB |
| News (English) | 108 | 0.803 | 0.803 | 108 of 108 | 50 ms | 17 ms | 568 MB |

The rules, the tokenizer and the reading of the model's output are the same code in Python and in the browser, written once in Python and once in Rust. On 6,915 texts the two give the same rules, the same pieces and the same spans. With more than one thread a page must be cross-origin isolated. The demo page is not, and runs on one.

## Size and speed

| | Small model | Server model |
|---|---|---|
| Model file | 40.8 MB, 8-bit weights | 1,110 MB, 32-bit weights |
| Weights | 40 million | 278 million |
| Built on | `microsoft/Multilingual-MiniLM-L12-H384`, vocabulary cut to 48,000 pieces | `FacebookAI/xlm-roberta-base` |
| One sentence, Python, 1 thread | 11 ms | 40 ms |
| One sentence, Python, 4 threads | 5 ms | 15 ms |
| Browser module (WASM) | 2.2 MB, 0.7 MB compressed | |

Medians on a laptop processor (Intel Core i5-13420H). A sentence is about 21 tokens.

The small model keeps its large tables of weights in 8 bits and does its arithmetic in 32-bit floats, so a text gets the same answer alone and beside other texts. Its scores were measured with the weights of that file on a graphics card; the file itself gives the same tag on 10,260 of 10,260 tokens of a check. The scores of the server model were measured with its weights on a graphics card; its ONNX file gives the same tag on 10,259 of 10,259 tokens. The Python package was run from its packaged files alone on 6,541 texts and gave the same spans as the code the scores come from.

## What these scores do not show

- The sets are small, and each is from one kind of source. The ranges say how much a score would move with other texts of the same kind. They say nothing about other kinds of text.
- Rakshya was trained on Nepali text with labels and on text like that of the test sets. Most of the other systems never saw Nepali. The tables say what works on this text today, and not which method is better.
- All the labels come from one AI model working under one guide. A system that reads a text the way the guide does scores higher than one that reads it another way, and the training data of Rakshya was prepared under the same guide.
- Chat messages, scanned documents and transcripts of speech were not tested.

## History

- 2026-11-14: version 0.2, as Rakshya. Seven new test sets, 25 published systems.
- 2026-11-13: version 0.1, as Gopya. Two test sets of Nepali text, seven published systems.
