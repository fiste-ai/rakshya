The code in this repository is under the MIT License (`LICENSE`). The model weights are not in this repository: they are at https://huggingface.co/fiste-ai/rakshya under the Apache License, Version 2.0. The label files in `benchmark/labels/` are under the Creative Commons Attribution 4.0 International licence (CC BY 4.0). What follows are the notices of what these were made from.

# Third-party notices

## The model

Rakshya is fine-tuned from nreimers/mMiniLMv2-L12-H384-distilled-from-XLMR-Large (https://huggingface.co/nreimers/mMiniLMv2-L12-H384-distilled-from-XLMR-Large), a MiniLMv2 distillation of XLM-R Large built with microsoft/unilm (https://github.com/microsoft/unilm/tree/master/minilm), with its vocabulary cut to the 48,000 pieces that Nepali, Hindi and English text use most. XLM-R and MiniLMv2 are released under the MIT License, and the notice below stays with copies and substantial portions of the work.

MIT License

Copyright (c) Microsoft Corporation

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

## Training data

Rakshya 1.1 was trained on text written for this project, in which every person, number and address is invented,
on the training part of the practical corpus released as NepPIICorpus
(https://huggingface.co/datasets/fiste-ai/nepiicorpus), on public text labelled for this project, and on the public
sets below. The development part of that corpus was used to choose and check settings, and its test part, published
as NepPIIBench (https://huggingface.co/datasets/fiste-ai/nepiibench), was not read before the model was fixed. None
of the public sets is redistributed here.

| Set | Language | Terms |
|---|---|---|
| IndicPHI, https://huggingface.co/datasets/Sidharth1743/indicphi | Nepali, Hindi, English | MIT |
| HiNER (Murthy and others, 2022), https://huggingface.co/datasets/cfilt/HiNER-original | Hindi | CC BY-SA 4.0 |
| Few-NERD (Ding and others, 2021) | English | CC BY-SA 4.0 |
| WNUT-17 (Derczynski and others, 2017) | English | CC BY 4.0 |
| Broad Twitter Corpus (Derczynski and others, 2016) | English | CC BY 4.0 |
| Text Anonymization Benchmark (Pilán and others, 2022) | English | MIT |
| Nemotron-PII, https://huggingface.co/datasets/nvidia/Nemotron-PII | English | CC BY 4.0 |
| Maskara, https://huggingface.co/datasets/somukandula/maskara-indian-pii-200k | English, Hindi | MIT |

EverestNER, DanfeNER and CoNLL-2003, which release 1.0 learned from, are not among them: Rakshya 1.1 was trained
without them, with a teacher that was trained without them, and with a vocabulary that was chosen without them.
HiNER and Few-NERD are licensed CC BY-SA 4.0, which asks that what is adapted from them is shared under the same
terms. They are named here with those terms; the weights are trained on them and hold none of their text.

Sentences of HiNER were also used a second time with the names of foreign people and places put in, taken from
ParaNames (https://github.com/bltlab/paranames, built from Wikidata, MIT).

The practical corpus adds Nepali, Hindi and English paragraphs in institutional registers, with character-offset
labels for the 19 personal labels. Every person, number and address in it is invented, and no paragraph is taken
from a real person or a real document.

Place names come from nepali-canonical (https://github.com/ritushishir/nepali-canonical), licensed under CC BY 4.0.

The model also learned from public text of five kinds: comments on videos
(https://huggingface.co/datasets/Boredoom17/Nepali-Flow-Roman, CC BY 4.0), pages of Nepali government sites
(https://huggingface.co/datasets/voidash/previllage-nepal-gov-corpus, CC BY 4.0 for the compilation), Nepali and
English news (https://huggingface.co/datasets/thegauravgiri/nepali-news-dataset, MIT for the compilation), Hindi
sentences from IndicCorp v2 (https://huggingface.co/datasets/ai4bharat/IndicCorpV2, CC0), and pages of public websites of schools,
hospitals, cooperatives, associations and companies in Nepal. A part of this text was labelled for this project by
an AI assistant under a written guide (ANNOTATION.md at https://github.com/fiste-ai/rakshya); the rest was labelled
by a larger teacher model. The rights in the comments, pages and articles stay with their authors and publishers,
and the text is not redistributed.

Some training targets are the probability outputs of that teacher, a model fine-tuned by us from MuRIL
(https://huggingface.co/google/muril-base-cased, Apache-2.0) on the labelled text and the public sets above. The
teacher is not distributed.

## Code

The browser module is compiled from Rust crates under the MIT, Apache-2.0, BSD-2-Clause, Zlib, Boost, Unicode and Unlicense licences. The largest is `tokenizers` by Hugging Face (Apache-2.0, https://www.apache.org/licenses/LICENSE-2.0). All of them are listed with their versions in `rust/Cargo.lock` at https://github.com/fiste-ai/rakshya.

The Python package runs on ONNX Runtime (MIT), `tokenizers` (Apache-2.0), NumPy (BSD-3-Clause) and `huggingface_hub` (Apache-2.0), which you install yourself. The demo page loads ONNX Runtime Web (MIT) from jsDelivr.
