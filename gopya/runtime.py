"""Find personal data in Nepali text with the released files. No PyTorch is needed.

    from gopya import Gopya            # in the development repository: from gopya.runtime import Gopya

    pii = Gopya("folder")              # holds onnx/model_quantized.onnx, tokenizer.json and tagger.json
    pii.find("मेरो नाम सीता थापा हो")    # [(start, end, label), ...] in characters of the text
    pii.redact("मेरो नाम सीता थापा हो")  # the text with a placeholder such as [PERSON_1] for each one

Needs numpy, onnxruntime and tokenizers. The rules find what has a fixed form: phone
numbers, e-mail addresses, dates, number plates and the numbers that a keyword names. The
tagger finds people, places and organisations, and the numbers the rules do not reach.
Where the two overlap, the rule is kept.
"""
import json
from pathlib import Path

import numpy
import onnxruntime
from tokenizers import Tokenizer

from .rules import find as find_by_rule
from .spans import merge, predict_spans, redact, tag_names


class Gopya:
    def __init__(self, folder, threads=0):
        """Load the model in `folder`. `threads` is the number of CPU threads; 0 leaves the choice to ONNX Runtime."""
        folder = Path(folder)
        meta = json.loads((folder / "tagger.json").read_text(encoding="utf-8"))
        self.labels = meta["labels"]
        self.tags = tag_names(self.labels)
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = threads
        self.session = onnxruntime.InferenceSession(str(folder / "onnx" / "model_quantized.onnx"), options,
                                                    providers=["CPUExecutionProvider"])
        self.tokenizer = Tokenizer.from_file(str(folder / "tokenizer.json"))
        pad = next(token for token in ("<pad>", "[PAD]") if self.tokenizer.token_to_id(token) is not None)
        self.tokenizer.enable_padding(pad_id=self.tokenizer.token_to_id(pad), pad_token=pad)

    def _encode(self, texts, max_length=512, **_):
        self.tokenizer.enable_truncation(max_length=max_length)
        rows = self.tokenizer.encode_batch(list(texts))
        return {"input_ids": numpy.array([row.ids for row in rows], dtype=numpy.int64),
                "attention_mask": numpy.array([row.attention_mask for row in rows], dtype=numpy.int64),
                "offset_mapping": numpy.array([row.offsets for row in rows], dtype=numpy.int64)}

    def _run(self, input_ids, attention_mask):
        logits, trims = self.session.run(["logits", "trim_logits"],
                                         {"input_ids": input_ids, "attention_mask": attention_mask})
        return logits.argmax(-1).tolist(), trims.argmax(-1).tolist()

    def find_all(self, texts):
        """For each text, its spans as sorted (start, end, label) with character offsets.

        A long text is read a few sentences at a time, and every piece is run on its own, so a text gets
        the same answer whatever is passed beside it.
        """
        texts = list(texts)
        _, tagged = predict_spans(self._run, self.tags, self._encode, texts, batch=1)
        return [merge(spans, find_by_rule(text)) for spans, text in zip(tagged, texts)]

    def find(self, text):
        return self.find_all([text])[0]

    def redact(self, text):
        """The text with each span replaced by its label and a number; equal text gets the same number."""
        return redact(text, self.find(text))
