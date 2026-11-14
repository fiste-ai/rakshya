# Third-party notices

## The model

Rakshya is fine-tuned from Multilingual-MiniLM-L12-H384 by Microsoft (https://huggingface.co/microsoft/Multilingual-MiniLM-L12-H384), with its vocabulary cut to the 48,000 pieces that Nepali, Hindi and English text use most. That model is released under the MIT License, and the notice below stays with copies and substantial portions of it.

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

The server model of Rakshya is fine-tuned from XLM-RoBERTa base by Facebook AI (https://huggingface.co/FacebookAI/xlm-roberta-base). That model is released under the MIT License, and the notice below stays with copies and substantial portions of it.

MIT License

Copyright (c) Facebook, Inc. and its affiliates.

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

Rakshya was trained on text made up by a generator of ours, in which every person, number and address is invented,
and on the public sets below. None of them is redistributed here. Two are for non-commercial use and one is for
research use, which is why the Rakshya weights are non-commercial.

| Set | Language | Terms |
|---|---|---|
| EverestNER (Niraula and Chapagain, 2022), https://github.com/nowalab/everest-ner | Nepali | non-commercial; commercial use needs the permission of its authors |
| DanfeNER (Niraula and Chapagain, 2023) | Nepali | non-commercial |
| IndicPHI, https://huggingface.co/datasets/Sidharth1743/indicphi | Nepali, Hindi, English | MIT |
| HiNER (Murthy and others, 2022), https://huggingface.co/datasets/cfilt/HiNER-original | Hindi | CC BY-SA 4.0 |
| CoNLL-2003 (Tjong Kim Sang and De Meulder, 2003) | English | Reuters text, for research use |
| Few-NERD (Ding and others, 2021) | English | CC BY-SA 4.0 |
| WNUT-17 (Derczynski and others, 2017) | English | CC BY 4.0 |
| Broad Twitter Corpus (Derczynski and others, 2016) | English | CC BY 4.0 |
| Text Anonymization Benchmark (Pilán and others, 2022) | English | MIT |
| Nemotron-PII, https://huggingface.co/datasets/nvidia/Nemotron-PII | English | CC BY 4.0 |
| Maskara, https://huggingface.co/datasets/somukandula/maskara-indian-pii-200k | English, Hindi | MIT |

Sentences of EverestNER, DanfeNER and HiNER were also used a second time with the names of foreign people and
places put in, taken from ParaNames (https://github.com/bltlab/paranames, built from Wikidata), and sentences of
EverestNER and DanfeNER a third time rewritten in Latin letters.

The generator takes the names of provinces, districts and local levels from nepali-canonical
(https://github.com/ritushishir/nepali-canonical), licensed under CC BY 4.0.

The small model also learned from real text without labels, which the server model labelled first: comments on videos (https://huggingface.co/datasets/Boredoom17/Nepali-Flow-Roman, CC BY 4.0), pages of Nepali government sites
(https://huggingface.co/datasets/voidash/previllage-nepal-gov-corpus, CC BY 4.0 for the compilation) and news
(https://huggingface.co/datasets/thegauravgiri/nepali-news-dataset, MIT for the compilation). The rights in the comments, pages and articles stay with their authors and publishers, and the text is not redistributed.

## Code

The browser module is compiled from Rust crates under the MIT, Apache-2.0, BSD-2-Clause, Zlib, Boost, Unicode and Unlicense licences. The largest is `tokenizers` by Hugging Face (Apache-2.0, https://www.apache.org/licenses/LICENSE-2.0). All of them are listed with their versions in `rust/Cargo.lock` at https://github.com/fiste-ai/rakshya.

The Python package runs on ONNX Runtime (MIT), `tokenizers` (Apache-2.0), NumPy (BSD-3-Clause) and `huggingface_hub` (Apache-2.0), which you install yourself. The demo page loads ONNX Runtime Web (MIT) from jsDelivr.
