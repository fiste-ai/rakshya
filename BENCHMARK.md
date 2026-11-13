# Gopya benchmark

Version 0.1, 13 November 2026. Every score of Gopya here was measured with the released files: the 8-bit model, run one piece of text at a time, together with the rules. The numbers are also in [`benchmark/results.json`](benchmark/results.json).

## How a system is scored

A system reads a text and returns spans: a start, an end and a label.

- **Exact** is the F1 of spans whose start, end and label are all right. One character too many, such as a case marker left on a name, makes a span wrong.
- **Whole words** is the same after every span, found and expected, is widened to the whole words it touches. It forgives the case marker.
- **Characters found** is the share of the expected characters that lie inside any found span, whatever its label. For a tool that takes personal data out of a text, this is the number that says how much is left in.

The systems do not share one set of labels. Each one's labels are mapped to ours, and the tables give two scores. **Names** counts the people, places and organisations, which nearly every system has. **All labels** counts everything in the test set, so a system with no label for dates or phone numbers loses those. The six kinds of identity number count as one label there.

A model that was not made for raw Nepali text can be read in two ways: every token by its own label, or every word by the label of its first token. Each published model is read both ways, and the reading with the better exact score for names is shown. Gopya is read one way.

The interval after a score is where 95% of the scores fall when the stories, or the snippets, are drawn again with replacement 1,000 times. The test sets are small and these intervals are wide.

## News

215 sentences from 43 stories of 15 Nepali news sites, collected on 13 November 2026, with 379 spans: 193 places, 99 people, 65 organisations and 22 dates. No system had been run on these sentences when they were labelled, and they are in no training data we used. This is the main test.

| Model | Maker | Weights | Exact | Second answers | Whole words | Characters found | Read |
|---|---|---|---|---|---|---|---|
| **[Gopya 0.1](https://huggingface.co/fiste-ai/gopya)** | Fiste AI | 34M | 0.807 (0.76 to 0.85) | 0.839 | 0.835 | 93.3% | per token |
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) | Davlan | 277M | 0.704 (0.63 to 0.77) | 0.746 | 0.808 | 89.2% | per token |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) | bards.ai | 278M | 0.665 (0.59 to 0.73) | 0.682 | 0.827 | 96.8% | per token |
| [WikiNEural multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) | Babelscape | 177M | 0.455 (0.37 to 0.54) | 0.484 | 0.564 | 64.9% | per token |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) | Saugatkafley | 177M | 0.340 (0.25 to 0.44) | 0.369 | 0.677 | 77.0% | per token |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) | meutsabdahal | 124M | 0.324 (0.28 to 0.37) | 0.340 | 0.784 | 83.5% | per token |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) | iiiorg | 278M | 0.268 (0.20 to 0.34) | 0.272 | 0.344 | 42.0% | per token |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) | Saugatkafley | 66M | 0.038 (0.01 to 0.06) | 0.038 | 0.276 | 61.3% | per token |

"Second answers" is the exact score when, for the 32 sentences where the labelling guide allows two answers, either one counts. Piiranha has no label for organisations, and they count as missed in its score for names. DistilBERT Nepali NER is built on `distilbert-base-uncased`, an English model.

Gopya is the most exact. Read as whole words the gap closes: Gopya 0.835, bards.ai 0.827, Davlan 0.808. The model of bards.ai finds more of the characters than Gopya does (96.8% against 93.3%) and is less careful: 11 in 100 characters it marks as a name are not part of one, against 5 for Gopya. The Nepali NER models were trained on text with the case markers split off. On text as it is written they keep the marker, so they score low on exact and much better as whole words.

Gopya on all four labels of this set: exact 0.814 (0.77 to 0.86), with second answers 0.844, whole words 0.840, characters found 93.6%. By label:

| Label | Spans | Exact | Characters found |
|---|---|---|---|
| People | 99 | 0.89 | 98% |
| Places | 193 | 0.79 | 90% |
| Organisations | 65 | 0.73 | 94% |
| Dates | 22 | 0.93 | 100% |

## Government pages

75 snippets of about 260 characters from 71 Nepali government sites, taken from the public crawl [voidash/previllage-nepal-gov-corpus](https://huggingface.co/datasets/voidash/previllage-nepal-gov-corpus) at places with a run of digits, an "@" or a word such as खाता. They hold 393 spans: 95 dates, 80 phone numbers, 63 places, 61 people, 47 organisations, 31 e-mail addresses, 11 bank accounts, 3 PAN numbers, 1 number plate and 1 citizenship number. The text is what a crawler took out of the pages, with table cells run together: a phone number can be followed at once by the number of the next row, and a name by the next heading.

This set was labelled before any system was run on it. Gopya then scored 0.61 exact (0.56 to 0.67) and found 95% of the characters. We read its errors and made three changes. An e-mail address no longer takes in a phone number in Devanagari digits written against it, and ends where the next heading begins. A name printed twice in a row is two names. A "number" of fewer than four digits, or a "date" that is only a time of day, is dropped. So for the released Gopya this is not an unseen test, and its scores below are after those changes. The news set was not looked at for them.

| Model | Weights | Names, exact | Names, whole words | Names, characters found | All labels, exact | All labels, characters found |
|---|---|---|---|---|---|---|
| [XLM-R base NER HRL](https://huggingface.co/Davlan/xlm-roberta-base-ner-hrl) | 277M | 0.619 (0.54 to 0.70) | 0.701 | 90.2% | 0.385 | 42.8% |
| [EU PII anonymisation](https://huggingface.co/bardsai/eu-pii-anonimization-multilang) | 278M | 0.534 (0.42 to 0.65) | 0.606 | 91.4% | 0.503 | 77.2% |
| [Nepali NER RoBERTa](https://huggingface.co/meutsabdahal/nepali-ner-roberta) | 124M | 0.529 (0.45 to 0.62) | 0.694 | 76.6% | 0.318 | 39.5% |
| **[Gopya 0.1](https://huggingface.co/fiste-ai/gopya)** | 34M | 0.510 (0.41 to 0.60) | 0.599 | 94.5% | 0.664 | 95.2% |
| [mBERT Nepali NER](https://huggingface.co/Saugatkafley/mbert-Nepali-NER) | 177M | 0.451 (0.36 to 0.56) | 0.617 | 78.8% | 0.275 | 40.6% |
| [WikiNEural multilingual NER](https://huggingface.co/Babelscape/wikineural-multilingual-ner) | 177M | 0.339 (0.23 to 0.45) | 0.539 | 61.4% | 0.203 | 29.2% |
| [Piiranha v1](https://huggingface.co/iiiorg/piiranha-v1-detect-personal-information) | 278M | 0.282 (0.17 to 0.38) | 0.349 | 34.7% | 0.155 | 16.9% |
| [DistilBERT Nepali NER](https://huggingface.co/Saugatkafley/distilbert-Nepali-NER) | 66M | 0.022 (0.00 to 0.05) | 0.129 | 55.3% | 0.040 | 30.0% |

For names alone, three larger models score higher than Gopya (XLM-R base NER HRL 0.619, EU PII anonymisation 0.534, Nepali NER RoBERTa 0.529, against 0.510) here. Gopya's names take in the word run on to them, and it marks job titles as people: 24 in 100 characters it marks as a name are not part of one. Over all labels Gopya is ahead, because its rules find the phone numbers, the e-mail addresses and the dates. By label:

| Label | Spans | Exact | Characters found |
|---|---|---|---|
| People | 61 | 0.58 | 98% |
| Places | 63 | 0.49 | 90% |
| Organisations | 47 | 0.45 | 94% |
| Dates | 95 | 0.76 | 93% |
| Phone numbers | 80 | 0.86 | 97% |
| E-mail addresses | 31 | 0.91 | 100% |
| Identity numbers | 4 | 0.47 | 100% |
| Bank accounts | 11 | 0.67 | 84% |
| Number plates | 1 | 0.67 | 100% |

Public pages print phone numbers, e-mail addresses, the bank accounts of offices and a few PAN numbers. They do not print citizenship, passport, licence or voter numbers: in 28,501 pages we found one citizenship number and one number plate, and both are in this set. Those kinds are tested on made-up text only.

## Other sets, Gopya only

| Set | Size | Exact | Whole words | Characters found |
|---|---|---|---|---|
| Older news | 154 sentences | 0.865 | 0.884 | 95.3% |
| Hand-written | 142 texts | 0.878 | 0.888 | 96.0% |
| EverestNER test | 1950 sentences | 0.874 | 0.891 | 93.3% |
| Made-up text | 3000 texts | 1.000 | 1.000 | 100.0% |

- Older news: 154 sentences from 28 stories, labelled the same way a day earlier. Its errors were used to improve the training data, so it is not an unseen test.
- Hand-written: 142 short texts written to be hard: forms, messages, Nepali in Latin letters, numbers without a keyword. A draft that has not been reviewed.
- EverestNER test: the 1,950 test sentences of [EverestNER](https://github.com/nowalab/everest-ner), with its labels brought to our guide (a province is a place, the short name of a party is an organisation, "today" is not a date). Gopya was trained on the training part of this corpus.
- Made-up text: 3,000 texts from the generator that made part of the training data, with other names and numbers. It shows that the forms it was taught were learned, and nothing about real text.

## In the browser

Chromium 155, headless, WASM, no GPU, on the same laptop. Exact, all labels:

| Set | Python package | Browser |
|---|---|---|
| News | 0.814 | 0.823 |
| News, second answers | 0.844 | 0.850 |
| Government pages | 0.664 | 0.676 |
| Older news | 0.865 | 0.868 |
| Hand-written | 0.875 | 0.876 |
| EverestNER test | 0.874 | 0.873 |

The page gives the same spans as the Python package on 209 of 215 news sentences and on 55 of 75 government snippets. The rules, the tokenizer and the reading of the model's output are the same code in both and agree on every text. The 8-bit model itself differs in the last bits between the two builds of ONNX Runtime, and a close call can then fall the other way. On government pages many calls are close.

Loading takes 0.4 to 0.7 s after the download, and the tab uses 370 to 440 MB against 152 MB for an empty page. With more than one thread a page must be cross-origin isolated. The demo page is not, and runs on one.

## Size and speed

| | |
|---|---|
| Model file, 8-bit | 34.8 MB |
| Weights | 34.4 million |
| Browser module (WASM) | 2.1 MB, 0.7 MB compressed |
| One sentence, Python, 1 thread | 12 ms |
| One sentence, Python, 4 threads | 6 ms |
| One news sentence, browser, 1 thread | 34 ms |
| One news sentence, browser, 4 threads | 15 ms |

Medians on an Intel Core i5-13420H, a laptop processor. A sentence is about 27 tokens.

The 8-bit model sets the scale of its numbers from what it is given, so its answer for a piece of text can change with the pieces run beside it. The package and the page therefore run one piece at a time, and a text always gets the same answer.

## Who wrote the labels

The labels of the news and the government sets were written by an AI assistant working for us, one sentence at a time, under a written guide, before any rule or model was run on the text. Where the guide allows a second answer, it was written down at the same time. A native speaker has not yet reviewed them. Until that is done, every score here is provisional.

The text and the labels are not published. The news belongs to its publishers, and the government snippets hold the names and phone numbers of real people.

## What these scores do not show

- The sets are small, and each is from one week and one kind of site. The intervals say how much a score would move with other stories. They say nothing about other kinds of text.
- Gopya was trained on Nepali news with labels. Most of the other systems never saw Nepali labels, and the Nepali ones saw them in another form. The tables say what works on Nepali text today, and not which method is better.
- The released model is one of three trainings with different random seeds. Before the 8-bit step the three scored 0.813 to 0.820 on the news set, all labels.
- Chat messages, social media, scanned documents and transcripts of speech were not tested.

## History

- 2026-11-13: version 0.1.
