# Benchmark

Every number here was measured with the released files of Rakshya 1.1 (2026-11-20). The test sets are those of release 1.0. They were fixed and locked before any model of 1.0 read them: the texts, their labels and the sha256 of both were written down. The models of 1.0 were chosen without reading them and were then scored on them once. Rakshya 1.1 was trained and chosen without reading them either, by a rule written down before its training, and was then scored on them once. Nothing was chosen after either reading.

## What changed since 1.0

The training, and with it the licence. Release 1.0 learned from EverestNER and DanfeNER, which are for non-commercial use, and from CoNLL-2003, which is for research use. Version 1.1 was trained without the three: they are in none of its training rows, its teacher was trained without them, that teacher labelled the unlabelled text again, the rows that decide when training stops hold none of them, and the vocabulary was chosen by a count without them. The labels, the rules, the code after the model and the size are those of 1.0, and the recipe was not tuned again.

| Test | Rakshya 1.1 | Rakshya 1.0 | 1.1 ahead by, with its 95 percent interval |
|---|---:|---:|---|
| The seven test sets, mean exact F1 | 0.913 | 0.906 | 0.0072 (-0.0049 to 0.0202) |
| The practical test, exact F1 with label | 0.956 | 0.952 | 0.0042 (-0.0005 to 0.0093) |
| The 180 cases, exact F1 with label | 0.960 | 0.948 | 0.0122 (-0.0056 to 0.0362) |

The interval comes from drawing the test texts again, the same ones for both versions. Each of the three reaches below zero, so these tests do not tell the two versions apart: 1.1 is not behind 1.0, and it is not shown to be better. The two also differ in more than the three sets, because the teacher of 1.1 was trained later and labelled more of the unlabelled text, so the table does not say what the three sets were worth.

## What is measured

A span is a start, an end and a label. **Exact F1** counts a span only when all three are right. A model that marks सीता थापा but not the case marker in सीताले gets no credit for that span; one that marks the whole sentence loses precision.

Systems mark different things, so one table needs one level of labels: `PERSON`, `LOCATION`, `ORGANIZATION`, `DATE`, `PHONE`, `EMAIL`, `URL`, `DIGITAL_SECRET` and `NUMBER`, where `NUMBER` is every identifying number of a person whatever kind it is: citizenship, PAN, passport, licence, account, card, patient, employee or plot. A model that lacks a label loses what the set has of that label. The per-label table uses the same level.

The **character recall** below is the share of the characters of the gold personal data that the model marked, so a boundary that is a little short costs little. It is reported beside the F1 of exact spans, not instead of it.

## The seven test sets

| Set | Language | Texts | Spans | Agreement of two passes | Texts with a second accepted reading |
|---|---|---|---|---|---|
| News | Nepali | 178 | 289 | 0.998 | 18 |
| Web pages | Nepali | 126 | 838 | 0.999 | 47 |
| Government pages | Nepali | 53 | 314 | 0.997 | 21 |
| Comments | Nepali in Latin letters | 300 | 208 | 0.995 | 6 |
| News | English | 144 | 301 | 0.987 | 22 |
| Web pages | English | 129 | 770 | 0.987 | 34 |
| News | Hindi | 104 | 132 | 0.989 | 9 |

None of these texts is in any training data we used: each set was held against the training files, and a text close to a training row was left out. The labels follow a written guide, [ANNOTATION.md](ANNOTATION.md). Each set was labelled twice by an AI assistant, in separate runs that saw the guide and the texts and neither each other's labels nor the output of any system. A third run settled what differed against the guide. "Agreement of two passes" is the F1 of exact spans between the two; they gave the same labels on 1,014 of the 1,034 texts.

A second reading is accepted where the guide accepts two cuts of one text, such as a list marked whole against each item in it; a system is scored against the reading it matches best. All labels come from one model, so the agreement shows that the guide is applied the same way twice. It does not show that it is applied rightly.

## Results

The released model, its rules alone, the three releases before it and the 25 published systems we ran, on the seven sets. Best in each column in bold.

| System | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | **0.930** | **0.937** | **0.944** | **0.864** | **0.934** | **0.933** | 0.851 | **0.913** |
| the rules of Rakshya alone | 0.105 | 0.484 | 0.662 | 0.047 | 0.089 | 0.501 | 0.087 | 0.282 |
| [Rakshya 1.0](https://huggingface.co/fiste-ai/rakshya/tree/v1.0) | 0.914 | 0.933 | 0.943 | 0.858 | 0.924 | 0.915 | **0.855** | 0.906 |
| [Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya/tree/v0.2) | 0.889 | 0.816 | 0.863 | 0.524 | 0.892 | 0.790 | 0.797 | 0.796 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 0.849 | 0.727 | 0.704 | 0.218 | 0.724 | 0.638 | 0.789 | 0.664 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 0.718 | 0.597 | 0.506 | 0.264 | 0.817 | 0.460 | 0.757 | 0.588 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 0.775 | 0.566 | 0.353 | 0.269 | 0.855 | 0.499 | 0.762 | 0.583 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 0.764 | 0.552 | 0.302 | 0.280 | 0.852 | 0.498 | 0.802 | 0.578 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 0.601 | 0.494 | 0.272 | 0.203 | 0.635 | 0.430 | 0.631 | 0.467 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 0.390 | 0.452 | 0.336 | 0.274 | 0.672 | 0.519 | 0.578 | 0.460 |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 0.419 | 0.435 | 0.272 | 0.249 | 0.713 | 0.381 | 0.599 | 0.438 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 0.157 | 0.626 | 0.304 | 0.217 | 0.621 | 0.621 | 0.465 | 0.430 |
| [WikiNEuRal multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 0.496 | 0.368 | 0.158 | 0.179 | 0.767 | 0.445 | 0.594 | 0.430 |
| [PII Redactor small](https://huggingface.co/Horizon-Labs/pii-redactor-small) (Horizon Labs) | 0.432 | 0.447 | 0.276 | 0.142 | 0.582 | 0.514 | 0.318 | 0.387 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector) (IIT Guwahati) | 0.262 | 0.511 | 0.242 | 0.198 | 0.551 | 0.333 | 0.506 | 0.372 |
| [Chitragupta](https://huggingface.co/LatentAILabs/chitragupta-pii-indic) (Latent AI Labs) | 0.295 | 0.514 | 0.309 | 0.269 | 0.319 | 0.343 | 0.284 | 0.333 |
| [CBX Indic PII 58M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-58M) (CobuildX) | 0.107 | 0.497 | 0.438 | 0.182 | 0.256 | 0.400 | 0.298 | 0.311 |
| [IndicPHI MuRIL](https://huggingface.co/sach3v/indicphi-muril-pii) (sach3v) | 0.213 | 0.384 | 0.404 | 0.200 | 0.374 | 0.330 | 0.149 | 0.293 |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) (iiiorg) | 0.239 | 0.279 | 0.233 | 0.027 | 0.441 | 0.381 | 0.291 | 0.270 |
| [GLiNER multi PII](https://huggingface.co/urchade/gliner_multi_pii-v1) (urchade) | 0.013 | 0.219 | 0.249 | 0.159 | 0.580 | 0.475 | 0.148 | 0.263 |
| [Presidio](https://github.com/data-privacy-stack/presidio) (Microsoft) | 0.000 | 0.358 | 0.270 | 0.074 | 0.534 | 0.546 | 0.042 | 0.261 |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 0.370 | 0.466 | 0.387 | 0.006 | 0.000 | 0.008 | 0.496 | 0.247 |
| [CBX Indic PII 17M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-17M) (CobuildX) | 0.040 | 0.424 | 0.399 | 0.114 | 0.224 | 0.375 | 0.126 | 0.243 |
| [GLiNER PII edge](https://huggingface.co/knowledgator/gliner-pii-edge-v1.0) (Knowledgator) | 0.000 | 0.154 | 0.134 | 0.052 | 0.554 | 0.424 | 0.016 | 0.191 |
| [Privacy Filter](https://huggingface.co/openai/privacy-filter) (OpenAI) | 0.034 | 0.268 | 0.341 | 0.050 | 0.110 | 0.297 | 0.085 | 0.169 |
| [Smart PII Redactor](https://huggingface.co/Mozilla/smart-pii-redactor-v1-onnx) (Mozilla) | 0.000 | 0.056 | 0.183 | 0.107 | 0.528 | 0.231 | 0.014 | 0.160 |
| [BERT-small PII detection](https://huggingface.co/gravitee-io/bert-small-pii-detection) (Gravitee) | 0.008 | 0.096 | 0.067 | 0.074 | 0.499 | 0.357 | 0.007 | 0.158 |
| [Rampart](https://huggingface.co/nationaldesignstudio/rampart) (National Design Studio) | 0.000 | 0.127 | 0.031 | 0.061 | 0.407 | 0.318 | 0.000 | 0.135 |
| [mmBERT-small PII redaction](https://huggingface.co/balticml/mmbert-small-pii-redaction) (BalticML) | 0.000 | 0.102 | 0.021 | 0.053 | 0.131 | 0.195 | 0.015 | 0.074 |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) (Saugatkafley) | 0.059 | 0.036 | 0.030 | 0.028 | 0.092 | 0.042 | 0.104 | 0.056 |

None of the 25 published systems we ran scores higher than Rakshya 1.1 on any of the seven sets.

The published systems include general named-entity models that mark no identity numbers; the score counts that against them. Sizes and links are in `benchmark/results.json`.

Names only (people, places and organisations):

| System | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | **0.927** | **0.927** | 0.903 | **0.857** | **0.931** | **0.916** | 0.843 | **0.900** |
| [Rakshya 1.0](https://huggingface.co/fiste-ai/rakshya/tree/v1.0) | 0.912 | 0.920 | **0.903** | 0.851 | 0.922 | 0.896 | **0.855** | 0.894 |
| [Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya/tree/v0.2) | 0.887 | 0.794 | 0.838 | 0.496 | 0.902 | 0.744 | 0.795 | 0.779 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 0.847 | 0.672 | 0.662 | 0.189 | 0.739 | 0.537 | 0.800 | 0.635 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 0.740 | 0.605 | 0.671 | 0.275 | 0.859 | 0.502 | 0.797 | 0.636 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 0.802 | 0.716 | 0.563 | 0.283 | 0.899 | 0.627 | 0.805 | 0.671 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 0.790 | 0.697 | 0.473 | 0.290 | 0.896 | 0.620 | 0.844 | 0.659 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 0.622 | 0.564 | 0.340 | 0.209 | 0.669 | 0.419 | 0.670 | 0.499 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 0.421 | 0.425 | 0.188 | 0.235 | 0.711 | 0.530 | 0.615 | 0.446 |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 0.435 | 0.562 | 0.441 | 0.222 | 0.804 | 0.513 | 0.633 | 0.516 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 0.146 | 0.542 | 0.211 | 0.204 | 0.637 | 0.526 | 0.475 | 0.392 |
| [WikiNEuRal multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 0.512 | 0.483 | 0.265 | 0.188 | 0.806 | 0.572 | 0.625 | 0.493 |
| [PII Redactor small](https://huggingface.co/Horizon-Labs/pii-redactor-small) (Horizon Labs) | 0.456 | 0.450 | 0.147 | 0.140 | 0.607 | 0.520 | 0.346 | 0.381 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector) (IIT Guwahati) | 0.269 | 0.354 | 0.223 | 0.210 | 0.580 | 0.111 | 0.536 | 0.326 |
| [Chitragupta](https://huggingface.co/LatentAILabs/chitragupta-pii-indic) (Latent AI Labs) | 0.306 | 0.437 | 0.521 | 0.269 | 0.347 | 0.253 | 0.308 | 0.349 |
| [CBX Indic PII 58M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-58M) (CobuildX) | 0.098 | 0.310 | 0.160 | 0.161 | 0.240 | 0.231 | 0.268 | 0.210 |
| [IndicPHI MuRIL](https://huggingface.co/sach3v/indicphi-muril-pii) (sach3v) | 0.227 | 0.314 | 0.410 | 0.217 | 0.403 | 0.249 | 0.164 | 0.283 |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) (iiiorg) | 0.246 | 0.243 | 0.199 | 0.045 | 0.472 | 0.403 | 0.317 | 0.275 |
| [GLiNER multi PII](https://huggingface.co/urchade/gliner_multi_pii-v1) (urchade) | 0.014 | 0.093 | 0.166 | 0.161 | 0.601 | 0.388 | 0.086 | 0.215 |
| [Presidio](https://github.com/data-privacy-stack/presidio) (Microsoft) | 0.000 | 0.050 | 0.000 | 0.060 | 0.609 | 0.462 | 0.000 | 0.169 |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 0.387 | 0.612 | 0.639 | 0.006 | 0.000 | 0.008 | 0.545 | 0.314 |
| [CBX Indic PII 17M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-17M) (CobuildX) | 0.037 | 0.198 | 0.070 | 0.123 | 0.229 | 0.219 | 0.142 | 0.145 |
| [GLiNER PII edge](https://huggingface.co/knowledgator/gliner-pii-edge-v1.0) (Knowledgator) | 0.000 | 0.090 | 0.015 | 0.078 | 0.633 | 0.433 | 0.021 | 0.181 |
| [Privacy Filter](https://huggingface.co/openai/privacy-filter) (OpenAI) | 0.024 | 0.124 | 0.123 | 0.053 | 0.120 | 0.160 | 0.094 | 0.100 |
| [Smart PII Redactor](https://huggingface.co/Mozilla/smart-pii-redactor-v1-onnx) (Mozilla) | 0.000 | 0.056 | 0.000 | 0.097 | 0.555 | 0.297 | 0.000 | 0.144 |
| [BERT-small PII detection](https://huggingface.co/gravitee-io/bert-small-pii-detection) (Gravitee) | 0.008 | 0.026 | 0.013 | 0.068 | 0.549 | 0.284 | 0.007 | 0.137 |
| [Rampart](https://huggingface.co/nationaldesignstudio/rampart) (National Design Studio) | 0.000 | 0.014 | 0.000 | 0.063 | 0.433 | 0.297 | 0.000 | 0.115 |
| [mmBERT-small PII redaction](https://huggingface.co/balticml/mmbert-small-pii-redaction) (BalticML) | 0.000 | 0.013 | 0.000 | 0.059 | 0.152 | 0.154 | 0.000 | 0.054 |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) (Saugatkafley) | 0.051 | 0.039 | 0.038 | 0.031 | 0.096 | 0.056 | 0.112 | 0.060 |

### By kind

Exact F1, with the number of gold spans in the set in brackets. A blank cell means the set has nothing of that kind.

| Kind | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) |
|---|---|---|---|---|---|---|---|
| Places | 0.951 (130) | 0.932 (206) | 0.755 (23) | 0.852 (52) | 0.936 (129) | 0.933 (252) | 0.912 (58) |
| People | 0.951 (72) | 0.978 (200) | 0.974 (76) | 0.868 (129) | 0.966 (73) | 0.960 (98) | 0.915 (29) |
| Organisations | 0.855 (68) | 0.848 (138) | 0.867 (40) | 0.737 (11) | 0.881 (70) | 0.855 (146) | 0.645 (31) |
| Phone numbers | 1.000 (1) | 0.979 (168) | 0.977 (67) |  |  | 0.983 (152) |  |
| Dates | 0.971 (18) | 0.909 (66) | 0.986 (70) | 0.968 (16) | 0.963 (28) | 0.980 (50) | 0.917 (12) |
| E-mail addresses |  | 1.000 (59) | 0.962 (40) |  |  | 0.986 (69) |  |
| Web addresses |  | 1.000 (6) | 1.000 (2) |  | 1.000 (1) | 1.000 (12) |  |
| Identifying numbers |  | 0.400 (8) |  |  |  | 0.545 (3) |  |
| Passwords, keys and device identifiers |  |  | 1.000 (1) | 0.667 (1) |  | 0.222 (1) | 1.000 (1) |

### Confidence

A 95 percent interval from drawing the articles of each set again, for the released model. It says how much the number would move on another draw of texts from the same sources.

| System | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) |
|---|---|---|---|---|---|---|---|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | 0.930 (0.89 to 0.96) | 0.937 (0.92 to 0.95) | 0.944 (0.91 to 0.97) | 0.864 (0.82 to 0.91) | 0.934 (0.89 to 0.97) | 0.933 (0.90 to 0.96) | 0.851 (0.78 to 0.92) |

### False alarms

Texts that hold no personal data are the test of over-redaction. The table counts the spans a system marks on them, per 1,000 words.

| System | News (ne), 55 | Web (ne), 10 | Government (ne), 4 | Comments (ne, Latin), 153 | News (en), 41 | Web (en), 14 | News (hi), 44 |
|---|---|---|---|---|---|---|---|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | 4.52 | 5.19 | 8.26 | 2.34 | 0.0 | 36.59 | 5.13 |
| [Rakshya 1.0](https://huggingface.co/fiste-ai/rakshya/tree/v1.0) | 3.39 | 5.19 | 0.0 | 6.45 | 1.36 | 31.36 | 6.41 |
| [Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya/tree/v0.2) | 3.39 | 7.79 | 0.0 | 34.0 | 1.36 | 24.39 | 8.97 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 5.66 | 36.36 | 8.26 | 104.34 | 4.09 | 33.1 | 2.56 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 13.57 | 20.78 | 0.0 | 36.34 | 0.0 | 101.05 | 2.56 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 5.66 | 18.18 | 0.0 | 21.69 | 0.0 | 19.16 | 0.0 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 10.18 | 7.79 | 0.0 | 49.24 | 0.0 | 13.94 | 0.0 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 2.26 | 10.39 | 0.0 | 95.55 | 8.17 | 34.84 | 7.69 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 13.57 | 23.38 | 0.0 | 20.52 | 4.09 | 24.39 | 2.56 |

## The older test sets

Seven older sets of the same kinds, 939 texts, labelled under the same guide. Their scores were read while 1.0 and 1.1 were built, so they are not a held-out test; the seven sets above are. They are a second draw of texts of the same kinds.

| System | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | 0.921 | 0.924 | 0.925 | 0.773 | 0.920 | 0.910 | 0.899 | 0.896 |
| [Rakshya 1.0](https://huggingface.co/fiste-ai/rakshya/tree/v1.0) | 0.930 | 0.891 | 0.904 | 0.778 | 0.925 | 0.878 | 0.892 | 0.886 |
| [Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya/tree/v0.2) | 0.894 | 0.743 | 0.847 | 0.467 | 0.847 | 0.767 | 0.817 | 0.769 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 0.846 | 0.661 | 0.589 | 0.199 | 0.737 | 0.561 | 0.836 | 0.633 |

## The practical test

578 short institutional texts in Nepali, Hindi and English, such as letters of ward and land offices, bank and payment records, complaints, court papers, hospital summaries and support tickets, with 3,572 marked items of personal data. The people, addresses and numbers in them are fictional. They were kept back while the models of 1.0 and 1.1 were built, and each release was scored on them once, under `labels="personal"`, the profile a redaction uses. NepPIIBench publishes 380 of them; the scores here are over all of them.

Rakshya 1.1 and 1.0 learned from the training part of the same collection: 2,087 other paragraphs, of which 1,394 are published in [NepPIICorpus](https://huggingface.co/datasets/fiste-ai/nepiicorpus). No other system in the table did. So the table says what each system does on records of this kind, and the lead of Rakshya in it is that of a model on the kind of text it was trained for. The 180 cases below are a set apart.

Every system at the level of seven kinds, where all of them can stand: a person, an address, a date of birth, a phone number, an e-mail address, an identifying number, a secret. Each published system is read in the way that scores best for it on this set.

| System | Exact F1 with kind | Precision | Recall | Characters found | Nepali | Hindi | English |
|---|---:|---:|---:|---:|---:|---:|---:|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | **0.968** | 0.963 | 0.973 | 0.984 | 0.973 | 0.968 | 0.961 |
| [Rakshya 1.0](https://huggingface.co/fiste-ai/rakshya/tree/v1.0) | 0.967 | 0.961 | 0.973 | 0.983 | 0.967 | 0.972 | 0.963 |
| [Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya/tree/v0.2) | 0.816 | 0.817 | 0.816 | 0.701 | 0.816 | 0.815 | 0.817 |
| [Chitragupta](https://huggingface.co/LatentAILabs/chitragupta-pii-indic) (Latent AI Labs) | 0.733 | 0.744 | 0.721 | 0.830 | 0.681 | 0.804 | 0.710 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 0.674 | 0.597 | 0.773 | 0.923 | 0.688 | 0.679 | 0.654 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 0.670 | 0.733 | 0.618 | 0.592 | 0.737 | 0.644 | 0.631 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 0.669 | 0.665 | 0.673 | 0.836 | 0.495 | 0.693 | 0.814 |
| [CBX Indic PII 58M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-58M) (CobuildX) | 0.658 | 0.655 | 0.661 | 0.773 | 0.547 | 0.728 | 0.695 |
| [Privacy Filter](https://huggingface.co/openai/privacy-filter) (OpenAI) | 0.535 | 0.567 | 0.507 | 0.718 | 0.408 | 0.470 | 0.711 |
| [CBX Indic PII 17M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-17M) (CobuildX) | 0.530 | 0.568 | 0.497 | 0.601 | 0.426 | 0.643 | 0.514 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 0.454 | 0.882 | 0.306 | 0.240 | 0.436 | 0.450 | 0.476 |
| [PII Redactor small](https://huggingface.co/Horizon-Labs/pii-redactor-small) (Horizon Labs) | 0.434 | 0.360 | 0.546 | 0.807 | 0.399 | 0.358 | 0.547 |
| [GLiNER multi PII](https://huggingface.co/urchade/gliner_multi_pii-v1) (urchade) | 0.430 | 0.652 | 0.321 | 0.397 | 0.185 | 0.283 | 0.701 |
| [IndicPHI MuRIL](https://huggingface.co/sach3v/indicphi-muril-pii) (sach3v) | 0.416 | 0.424 | 0.409 | 0.638 | 0.408 | 0.513 | 0.324 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 0.406 | 0.634 | 0.299 | 0.279 | 0.384 | 0.399 | 0.436 |
| [Smart PII Redactor](https://huggingface.co/Mozilla/smart-pii-redactor-v1-onnx) (Mozilla) | 0.381 | 0.488 | 0.312 | 0.411 | 0.134 | 0.306 | 0.583 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector), its Nepali tagger (IIT Guwahati) | 0.371 | 0.423 | 0.330 | 0.651 | 0.352 | 0.363 | 0.396 |
| [Presidio](https://github.com/data-privacy-stack/presidio) (Microsoft) | 0.368 | 0.455 | 0.309 | 0.377 | 0.237 | 0.255 | 0.585 |
| [GLiNER PII edge](https://huggingface.co/knowledgator/gliner-pii-edge-v1.0) (Knowledgator) | 0.343 | 0.322 | 0.368 | 0.499 | 0.107 | 0.254 | 0.589 |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 0.332 | 0.632 | 0.225 | 0.223 | 0.197 | 0.355 | 0.444 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector), its Hindi tagger (IIT Guwahati) | 0.309 | 0.350 | 0.277 | 0.530 | 0.256 | 0.312 | 0.358 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector), its English tagger (IIT Guwahati) | 0.309 | 0.349 | 0.277 | 0.527 | 0.245 | 0.307 | 0.376 |
| [WikiNEuRal multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 0.308 | 0.620 | 0.205 | 0.213 | 0.201 | 0.251 | 0.471 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 0.298 | 0.240 | 0.393 | 0.796 | 0.348 | 0.262 | 0.286 |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) (iiiorg) | 0.290 | 0.287 | 0.293 | 0.587 | 0.349 | 0.258 | 0.264 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 0.234 | 0.183 | 0.323 | 0.787 | 0.229 | 0.235 | 0.237 |
| [BERT-small PII detection](https://huggingface.co/gravitee-io/bert-small-pii-detection) (Gravitee) | 0.224 | 0.226 | 0.223 | 0.331 | 0.040 | 0.060 | 0.580 |
| [Rampart](https://huggingface.co/nationaldesignstudio/rampart) (National Design Studio) | 0.209 | 0.264 | 0.174 | 0.366 | 0.083 | 0.184 | 0.296 |
| [mmBERT-small PII redaction](https://huggingface.co/balticml/mmbert-small-pii-redaction) (BalticML) | 0.160 | 0.162 | 0.158 | 0.467 | 0.129 | 0.192 | 0.154 |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 0.132 | 0.370 | 0.080 | 0.135 | 0.170 | 0.193 | 0.000 |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) (Saugatkafley) | 0.043 | 0.052 | 0.037 | 0.142 | 0.014 | 0.025 | 0.095 |

Rakshya on its own 19 labels of personal data. `with label` requires the label to be right; `without label` counts a span whose start and end are right whatever the label; `touching` counts a span that overlaps the gold one.

| System | With label | Without label | Touching | Characters found | Keep-out strings covered | Rows without personal data that got a mark |
|---|---:|---:|---:|---:|---:|---:|
| Rakshya 1.1 | 0.956 | 0.972 | 0.983 | 0.984 | 0.055 | 2 of 36 |
| Rakshya 1.0 | 0.952 | 0.970 | 0.981 | 0.983 | 0.060 | 3 of 36 |
| Rakshya 0.2, its weights with the code of 1.0 | 0.799 | 0.857 | 0.887 | 0.666 | 0.197 | 8 of 36 |

## The 180 cases

180 further cases of our own, 60 in each of the three languages, with 365 marked items of 12 kinds. They are a separate set, made apart from the practical paragraphs and in another format, and no version of Rakshya learned from them. Each release was scored on them once.

Every system at the level of seven kinds, each published system read in the way that scores best for it on this set:

| System | Exact F1 with kind | Precision | Recall | Characters found | Nepali | Hindi | English |
|---|---:|---:|---:|---:|---:|---:|---:|
| **[Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya)** | **0.963** | 0.964 | 0.962 | 0.968 | 0.962 | 0.956 | 0.971 |
| [Rakshya 1.0](https://huggingface.co/fiste-ai/rakshya/tree/v1.0) | 0.951 | 0.948 | 0.953 | 0.980 | 0.954 | 0.936 | 0.963 |
| [Rakshya 0.2](https://huggingface.co/fiste-ai/rakshya/tree/v0.2) | 0.921 | 0.930 | 0.912 | 0.894 | 0.864 | 0.943 | 0.958 |
| [Gopya 0.1](https://huggingface.co/fiste-ai/rakshya/tree/v0.1) | 0.753 | 0.836 | 0.685 | 0.639 | 0.786 | 0.746 | 0.727 |
| [EU PII anonymisation v3](https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3) (bards.ai) | 0.727 | 0.809 | 0.660 | 0.723 | 0.660 | 0.700 | 0.816 |
| [Chitragupta](https://huggingface.co/LatentAILabs/chitragupta-pii-indic) (Latent AI Labs) | 0.724 | 0.761 | 0.690 | 0.776 | 0.751 | 0.788 | 0.632 |
| [CBX Indic PII 58M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-58M) (CobuildX) | 0.694 | 0.722 | 0.668 | 0.812 | 0.661 | 0.729 | 0.693 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector), its Nepali tagger (IIT Guwahati) | 0.613 | 0.713 | 0.537 | 0.673 | 0.606 | 0.629 | 0.604 |
| [Privacy Filter](https://huggingface.co/openai/privacy-filter) (OpenAI) | 0.609 | 0.681 | 0.551 | 0.744 | 0.446 | 0.510 | 0.853 |
| [CBX Indic PII 17M](https://huggingface.co/CobuildX-AI/cbx-indic-pii-extractor-17M) (CobuildX) | 0.596 | 0.678 | 0.531 | 0.632 | 0.556 | 0.754 | 0.460 |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) (bards.ai) | 0.574 | 0.516 | 0.647 | 0.860 | 0.546 | 0.632 | 0.545 |
| [IndicPHI MuRIL](https://huggingface.co/sach3v/indicphi-muril-pii) (sach3v) | 0.551 | 0.549 | 0.553 | 0.777 | 0.556 | 0.658 | 0.446 |
| [PII Redactor small](https://huggingface.co/Horizon-Labs/pii-redactor-small) (Horizon Labs) | 0.547 | 0.485 | 0.627 | 0.788 | 0.479 | 0.471 | 0.699 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector), its Hindi tagger (IIT Guwahati) | 0.546 | 0.625 | 0.485 | 0.667 | 0.536 | 0.578 | 0.524 |
| [Presidio](https://github.com/data-privacy-stack/presidio) (Microsoft) | 0.531 | 0.668 | 0.441 | 0.488 | 0.476 | 0.412 | 0.688 |
| [GLiNER multi PII](https://huggingface.co/urchade/gliner_multi_pii-v1) (urchade) | 0.526 | 0.677 | 0.430 | 0.552 | 0.292 | 0.328 | 0.856 |
| [AWED-PII-Protector](https://huggingface.co/spaces/prachuryyaIITG/AWED_PII_Protector), its English tagger (IIT Guwahati) | 0.501 | 0.577 | 0.444 | 0.672 | 0.507 | 0.500 | 0.498 |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) (Davlan) | 0.489 | 0.975 | 0.326 | 0.241 | 0.488 | 0.491 | 0.487 |
| [XLM-R large, CoNLL-2003](https://huggingface.co/FacebookAI/xlm-roberta-large-finetuned-conll03-english) (FacebookAI) | 0.485 | 0.967 | 0.323 | 0.241 | 0.478 | 0.491 | 0.484 |
| [Smart PII Redactor](https://huggingface.co/Mozilla/smart-pii-redactor-v1-onnx) (Mozilla) | 0.431 | 0.588 | 0.340 | 0.424 | 0.255 | 0.307 | 0.647 |
| [WikiNEuRal multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) (Babelscape) | 0.404 | 0.844 | 0.266 | 0.206 | 0.335 | 0.390 | 0.487 |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) (Saugatkafley) | 0.403 | 0.803 | 0.269 | 0.224 | 0.402 | 0.361 | 0.446 |
| [Nym PII multilingual](https://huggingface.co/Wismut/nym-pii-multilingual) (Wismut) | 0.306 | 0.262 | 0.370 | 0.745 | 0.277 | 0.272 | 0.377 |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) (meutsabdahal) | 0.292 | 0.759 | 0.181 | 0.155 | 0.410 | 0.388 | 0.000 |
| [GLiNER PII edge](https://huggingface.co/knowledgator/gliner-pii-edge-v1.0) (Knowledgator) | 0.276 | 0.196 | 0.463 | 0.556 | 0.136 | 0.166 | 0.759 |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) (iiiorg) | 0.238 | 0.315 | 0.192 | 0.387 | 0.240 | 0.258 | 0.219 |
| [Rampart](https://huggingface.co/nationaldesignstudio/rampart) (National Design Studio) | 0.229 | 0.303 | 0.184 | 0.342 | 0.203 | 0.228 | 0.244 |
| [MeridianPII Hindi v2](https://huggingface.co/plingampally/meridianpii-hi-v2) (plingampally) | 0.195 | 0.162 | 0.247 | 0.731 | 0.155 | 0.215 | 0.216 |
| [mmBERT-small PII redaction](https://huggingface.co/balticml/mmbert-small-pii-redaction) (BalticML) | 0.181 | 0.239 | 0.145 | 0.394 | 0.128 | 0.084 | 0.281 |
| [BERT-small PII detection](https://huggingface.co/gravitee-io/bert-small-pii-detection) (Gravitee) | 0.166 | 0.130 | 0.230 | 0.541 | 0.089 | 0.069 | 0.439 |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) (Saugatkafley) | 0.078 | 0.102 | 0.063 | 0.141 | 0.096 | 0.072 | 0.057 |

Rakshya on the 12 labels the cases mark. Characters found is the share of gold characters marked.

| System | With label | Without label | Touching | Characters found |
|---|---:|---:|---:|---:|
| Rakshya 1.1 | 0.960 | 0.963 | 0.977 | 0.963 |
| Rakshya 1.0 | 0.948 | 0.951 | 0.970 | 0.976 |
| Rakshya 0.2, its weights with the code of 1.0 | 0.913 | 0.922 | 0.925 | 0.731 |

## NepPIIBench

[NepPIIBench](https://huggingface.co/datasets/fiste-ai/nepiibench) is the public benchmark released beside this model: 380 paragraphs in Nepali, Hindi and English, with character offsets for 19 kinds of personal data and 837 strings that look like personal data and must be left alone. Rakshya 1.1 learned from the training part of the collection these rows are cut from, most of which is published as [NepPIICorpus](https://huggingface.co/datasets/fiste-ai/nepiicorpus); the rows themselves were not used in training or in model selection. The score below was made with the scorer that ships in the package, over every label it marks.

| Language | Rows | Character precision | Character recall | Character F1 | Exact F1 | Keep-out strings touched |
|---|---:|---:|---:|---:|---:|---:|
| Nepali | 130 | 0.988 | 0.989 | 0.989 | 0.966 | 3.1 percent |
| Hindi | 127 | 0.976 | 0.993 | 0.984 | 0.958 | 6.1 percent |
| English | 123 | 0.976 | 0.972 | 0.974 | 0.942 | 6.4 percent |
| **All** | **380** | **0.980** | **0.985** | **0.982** | **0.956** | **5.3 percent** |

Character F1 counts overlapping characters; exact F1 counts spans with the same start, end and label. On the whole set, 5.3 percent of the 837 keep-out strings were covered.

## Rakshya 1.1 Lite

[Rakshya 1.1 Lite](https://huggingface.co/fiste-ai/rakshya-lite) is a second, lighter model. Its network has 6 layers instead of 12, and its 8-bit file 29.8 MB instead of 40.8. It has the labels, the rules and the code of Rakshya 1.1, it learned from the same rows, and it followed the tag probabilities of Rakshya 1.1 as its teacher. It was fixed by a rule on development data and then scored once on the test sets of this page. For those sets that was the third scoring, after the models of 1.0 and Rakshya 1.1. Nothing was chosen after it.

| System | News (ne) | Web (ne) | Government (ne) | Comments (ne, Latin) | News (en) | Web (en) | News (hi) | Mean |
|---|---|---|---|---|---|---|---|---|
| [Rakshya 1.1 Lite](https://huggingface.co/fiste-ai/rakshya-lite) | 0.928 | 0.923 | 0.937 | 0.841 | 0.920 | 0.932 | 0.841 | 0.903 |
| [Rakshya 1.1](https://huggingface.co/fiste-ai/rakshya) | 0.930 | 0.937 | 0.944 | 0.864 | 0.934 | 0.933 | 0.851 | 0.913 |

| Test | Lite | Rakshya 1.1 | Rakshya 1.1 ahead by, with its 95 percent interval |
|---|---:|---:|---|
| The seven test sets, mean exact F1 | 0.903 | 0.913 | 0.0102 (0.0005 to 0.0207) |
| The practical test, exact F1 with label | 0.948 | 0.956 | 0.0073 (0.0020 to 0.0119) |
| The 180 cases, exact F1 with label | 0.919 | 0.960 | 0.0412 (0.0168 to 0.0705) |
| NepPIIBench, exact F1 | 0.9468 | 0.9555 | |

The interval comes from drawing the test texts again, the same ones for both models. At the level of seven kinds the Lite model has 0.965 on the practical test and 0.922 on the 180 cases.

The two models were timed one after the other, twice each. In headless Chromium on one thread the Lite model takes 23 ms for a text of news where Rakshya 1.1 takes 50 ms, which is 46 percent of the time. Its 8-bit file gave the tag of its 32-bit file on 5,579 of 5,589 tokens of the two sets of hard cases, and the same output alone and in a batch. The packaged model files gave the same spans as the repository code on 9,546 texts under both profiles, the Rust build gave what Python gives on 9,681 texts, and in a browser the file gave the spans of Python on each of the 1,792 texts of the 9 test files.

## How the systems were run

The published systems were run the way their authors publish them: the weights and the tokenizer from the Hub, at the revision named in `benchmark/results.json`, on a processor where that is how they are published, otherwise on the graphics card. Where the tags of a model can be read in more than one way, the reading that scores best on its own labels is used. Their makers did not tune them on these sets. They were run once, when release 1.0 was measured. What they and the earlier releases of Rakshya marked then was kept, and it is scored here again beside 1.1; none of them was run a second time.

Rakshya 1.1 is one set of weights with the rules of this repository, scored as the 8-bit file that is released. The same weights with the rounding of that file, read in full precision, give one tag on 10,260 of 10,260 tokens and the same scores. The rules alone have a mean of 0.282 on the seven sets.

## Size, speed and the browser

| | Value |
|---|---|
| 8-bit ONNX file | 40.8 MB |
| 32-bit weights | 40 million parameters |
| Vocabulary | 48,000 pieces, cut from the base model |
| Browser module | 2.3 MB, 0.8 MB compressed |
| Median per sentence, 4 threads | 5 ms |
| Median per sentence, 1 thread | 11 ms |
| Median per sentence in a browser, 1 thread | 50 ms |
| Tokens per sentence | 21 |

Measured on Intel Core i5-13420H with ONNX Runtime. The 8-bit file gave the tag of the 32-bit file on 5,582 of 5,589 tokens of two sets of hard cases, with the same exact F1 on both sets, and the same output alone and in a batch. The packaged Python files gave the same spans as the repository code on 9,546 texts under both profiles, and the Rust build gave what Python gives on 9,681 texts. In a browser the 8-bit file gave the spans of Python on each of the 1,792 texts of the 9 test files, with one thread and with four.

## The label files

The labels of the seven test sets are published without the text, as character ranges and the sha256 of each text. `benchmark/rebuild.py` puts them back on the sources named in each file; 353 of the texts come back exactly from the public datasets below.

| Set | Label file | Texts | Where the texts are |
|---|---|---|---|
| News, Nepali | [`real-news-v4.json`](benchmark/labels/real-news-v4.json) | 178 | news articles, each named by its address |
| Web pages, Nepali | [`real-web-v2.json`](benchmark/labels/real-web-v2.json) | 126 | web pages, each named by its address, with the range of the piece |
| Government pages, Nepali | [`real-gov-v3.json`](benchmark/labels/real-gov-v3.json) | 53 | [voidash/previllage-nepal-gov-corpus](https://huggingface.co/datasets/voidash/previllage-nepal-gov-corpus), `data/documents.parquet` at revision `004ce5f` |
| Comments, Nepali in Latin letters | [`real-roman-v2.json`](benchmark/labels/real-roman-v2.json) | 300 | [Boredoom17/Nepali-Flow-Roman](https://huggingface.co/datasets/Boredoom17/Nepali-Flow-Roman), `nepali_corpus_roman.parquet` at revision `347cf23` |
| News, English | [`real-en-v2.json`](benchmark/labels/real-en-v2.json) | 144 | news articles, each named by its address |
| Web pages, English | [`real-enweb-v2.json`](benchmark/labels/real-enweb-v2.json) | 129 | web pages, each named by its address, with the range of the piece |
| News, Hindi | [`real-hi-v2.json`](benchmark/labels/real-hi-v2.json) | 104 | news articles, each named by its address |

curl -LO https://huggingface.co/datasets/voidash/previllage-nepal-gov-corpus/resolve/004ce5f80a21746c9d4788434b33896f97ecc860/data/documents.parquet
python benchmark/rebuild.py benchmark/labels/real-gov-v3.json --parquet documents.parquet
curl -LO https://huggingface.co/datasets/Boredoom17/Nepali-Flow-Roman/resolve/347cf23f7084f7991c93329a27f9d4df01ba6ba5/nepali_corpus_roman.parquet
python benchmark/rebuild.py benchmark/labels/real-roman-v2.json --parquet nepali_corpus_roman.parquet

## Limits

- Seven sets of 1,034 texts. Each comes from one kind of source, and the 380 paragraphs of NepPIIBench are a further kind. Small sets make wide intervals on rare labels.
- Identity numbers are tested mostly on paragraphs of fictional records. Public pages print phone numbers, e-mail addresses and the bank accounts of offices; they do not print citizenship, passport or licence numbers.
- The label set is this model's own. A system that marks a slightly different thing, such as the parts of an address instead of the address, loses on the boundary and not necessarily on the task.
- The 180 cases are few, 60 in each language, and mark 12 kinds of personal data. A score on them moves by a few points with another draw of cases.
- The test sets have now been scored three times: for release 1.0, for Rakshya 1.1 and for Rakshya 1.1 Lite. Nothing was chosen on them at any time, but a version after this one needs test sets of its own.
- A score is not a promise. Read the output before relying on a redaction.
