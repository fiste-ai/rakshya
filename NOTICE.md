# Third-party notices

## The model

Gopya is fine-tuned from Multilingual-MiniLM-L12-H384 by Microsoft, with its vocabulary cut to the pieces that
Nepali and English text use. That model is released under the MIT License, and the notice below stays with copies
and substantial portions of it.

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

Gopya was trained on text made up by a generator, in which every person, number and address is invented, and on
the EverestNER corpus:

    Nobal B. Niraula and Jeevan Chapagain. Named Entity Recognition for Nepali: Data Sets and Algorithms.
    FLAIRS-35, 2022. https://github.com/nowalab/everest-ner

EverestNER is for non-commercial purposes only; commercial use needs the permission of its authors. The corpus
is not redistributed here. This is why the Gopya weights are non-commercial.

The generator takes the names of provinces, districts and local levels from nepali-canonical
(https://github.com/ritushishir/nepali-canonical), licensed under CC BY 4.0.

## Code

The browser module is compiled from Rust crates under the MIT, Apache-2.0, BSD-2-Clause, Zlib, Boost, Unicode
and Unlicense licences. The largest is `tokenizers` by Hugging Face (Apache-2.0,
https://www.apache.org/licenses/LICENSE-2.0). All of them are listed with their versions in `rust/Cargo.lock` at
https://github.com/fiste-ai/gopya.

The Python package runs on ONNX Runtime (MIT), `tokenizers` (Apache-2.0) and NumPy (BSD-3-Clause), which you
install yourself. The demo page loads ONNX Runtime Web (MIT) from jsDelivr.
