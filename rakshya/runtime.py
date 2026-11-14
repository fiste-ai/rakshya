"""Find personal data in Nepali, romanised Nepali and English text with the released files. No PyTorch is needed.

    from rakshya import Rakshya            # in the development repository: from rakshya.runtime import Rakshya

    pii = Rakshya()                      # fetches the released model from the Hugging Face Hub, once
    pii = Rakshya(model="server")        # the large model for servers instead of the small one for browsers
    pii = Rakshya("folder")              # or a folder with tokenizer.json, tagger.json and the ONNX file
    pii.find("मेरो नाम सीता थापा हो")    # [(start, end, label), ...] in characters of the text
    pii.redact("मेरो नाम सीता थापा हो")  # the text with a placeholder such as [PERSON_1] for each one

Needs numpy, onnxruntime and tokenizers, and huggingface_hub when no folder is given. The rules find what has a fixed form: phone
numbers, e-mail addresses, dates, number plates and the numbers that a keyword names. The
tagger finds people, places and organisations, and the numbers the rules do not reach.
Where the two overlap, the rule is kept.

The two models share the rules and this code. The small one is an 8-bit file of about 35 MB; the
server model is about 1.1 GB and reads a sentence on a processor in a few tens of milliseconds.
With `onnxruntime-gpu` installed, `Rakshya(model="server", providers=["CUDAExecutionProvider"])`
runs it on a graphics card.
"""
import json
from pathlib import Path

import numpy
import onnxruntime
from tokenizers import Tokenizer

from .rules import find as find_by_rule
from .spans import merge, predict_spans, redact, tag_names


# model -> (repository on the Hugging Face Hub, the ONNX file in it)
RELEASED = {"small": ("fiste-ai/rakshya", "onnx/model_quantized.onnx"), "server": ("fiste-ai/rakshya-server", "onnx/model.onnx")}


def released(model="small"):
    """The folder of a released model: fetched from the Hub the first time and read from its cache after that.

    An installed release fetches the model of its own version; the development code fetches the newest.
    """
    from huggingface_hub import snapshot_download
    if model not in RELEASED:
        raise ValueError(f"model is one of {sorted(RELEASED)}, not {model!r}")
    try:
        from . import __version__ as version
    except ImportError:
        version = None
    repository, weights = RELEASED[model]
    return snapshot_download(repository, revision=f"v{version}" if version else None,
                             allow_patterns=["tokenizer.json", "tagger.json", weights])


class Rakshya:
    def __init__(self, folder=None, threads=0, model="small", providers=("CPUExecutionProvider",)):
        """Load the model in `folder`, or a released model when no folder is given: "small" or "server".

        `threads` is the number of CPU threads; 0 leaves the choice to ONNX Runtime. `providers` are
        those of ONNX Runtime, in order of preference.
        """
        folder = Path(folder if folder is not None else released(model))
        meta = json.loads((folder / "tagger.json").read_text(encoding="utf-8"))
        self.labels = meta["labels"]
        self.tags = tag_names(self.labels)
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = threads
        # A released folder names its ONNX file; a folder of the development code holds the 8-bit file under this name.
        self.session = onnxruntime.InferenceSession(str(folder / meta.get("weights", "onnx/model_quantized.onnx")), options,
                                                    providers=list(providers))
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
