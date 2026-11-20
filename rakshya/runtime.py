"""Find personal data in Nepali, romanised Nepali and English text with the released files. No PyTorch is needed.

    from rakshya import Rakshya            # in the development repository: from rakshya.runtime import Rakshya

    pii = Rakshya()                      # fetches the released model from the Hugging Face Hub, once
    pii = Rakshya(model="lite")          # the lighter model of the same version: 6 layers, smaller and faster
    pii = Rakshya("folder")              # or a folder with tokenizer.json, tagger.json and the ONNX file
    pii.find("मेरो नाम सीता थापा हो")    # [(start, end, label), ...] in characters of the text
    pii.redact("मेरो नाम सीता थापा हो")  # the text with a placeholder such as [PERSON_1] for each one
    pii.redact(text, labels="personal")  # personal data only: places, organisations, dates and web addresses stay,
                                         # and so do the phone number and mailbox of an office and a masked number
    pii.find(text, labels=["PERSON", "PHONE"])   # or the labels that are wanted, by name

Needs numpy, onnxruntime and tokenizers, and huggingface_hub when no folder is given. The rules find what has a fixed form: phone
numbers, e-mail addresses, dates, number plates and the numbers that a keyword names. The
tagger finds people, places and organisations, and the numbers the rules do not reach.
Where the two overlap, the rule is kept.

The two models share the rules and this code. Both are 8-bit files, of about 41 MB and about 30 MB.
Release 0.2 had a large model for servers (`fiste-ai/rakshya-server`, about 1.1 GB). It was not trained again
for the labels of 1.0, so `model="server"` is not offered here; that model runs with the code of release 0.2.
"""
import json
from pathlib import Path

import numpy
import onnxruntime
from tokenizers import Tokenizer

from .kinds import final, personal
from .labels import LABELS
from .rules import find as find_by_rule
from .spans import merge, predict_spans, redact, tag_names


# model -> (repository on the Hugging Face Hub, the ONNX file in it)
RELEASED = {"small": ("fiste-ai/rakshya", "onnx/model_quantized.onnx"), "lite": ("fiste-ai/rakshya-lite", "onnx/model_quantized.onnx")}
NO_SERVER = ("there is no server model of this version: the large model of release 0.2 (fiste-ai/rakshya-server) was not trained again "
             "for the labels of 1.0. Use the default model; the model of 0.2 runs with the code of release 0.2 "
             "(https://huggingface.co/fiste-ai/rakshya/tree/v0.2)")


def released(model="small"):
    """The folder of a released model: fetched from the Hub the first time and read from its cache after that.

    An installed release fetches the models it was released with: `__model__` of the package names their version,
    which is older than `__version__` where only the code changed. The development code fetches the newest.
    """
    from huggingface_hub import snapshot_download
    if model == "server":
        raise ValueError(NO_SERVER)
    if model not in RELEASED:
        raise ValueError(f"model is one of {sorted(RELEASED)}, not {model!r}")
    import importlib
    package = importlib.import_module(__package__)
    version = getattr(package, "__model__", None) or getattr(package, "__version__", None)
    repository, weights = RELEASED[model]
    return snapshot_download(repository, revision=f"v{version}" if version else None,
                             allow_patterns=["tokenizer.json", "tagger.json", weights])


class Rakshya:
    def __init__(self, folder=None, threads=0, model="small", providers=("CPUExecutionProvider",)):
        """Load the model in `folder`, or a released model when no folder is given: "small", the default, or "lite".

        `threads` is the number of CPU threads; 0 leaves the choice to ONNX Runtime. `providers` are
        those of ONNX Runtime, in order of preference.
        """
        folder = Path(folder if folder is not None else released(model))
        meta = json.loads((folder / "tagger.json").read_text(encoding="utf-8"))
        self.labels = meta["labels"]
        self.tags = tag_names(self.labels)
        self.fit = bool(meta.get("fit"))   # a model folder says whether its tags are read as a sequence that fits together
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
        return (logits if self.fit else logits.argmax(-1).tolist()), trims.argmax(-1).tolist()

    def find_all(self, texts, labels="all"):
        """For each text, its spans as sorted (start, end, label) with character offsets and the labels of 1.0 (`rakshya.labels.LABELS`).

        `labels` says what is given out. "all": every label. "personal": personal data only, which leaves places,
        organisations, dates and web addresses, the phone number and the mailbox of an office or a helpline, and
        a number that is already masked. Or the names of the labels that are wanted.

        A long text is read a few sentences at a time, and every piece is run on its own, so a text gets
        the same answer whatever is passed beside it.
        """
        texts = list(texts)
        if labels not in ("all", "personal"):
            wanted = set(labels)
            if isinstance(labels, str) or wanted - set(LABELS):
                raise ValueError(f"labels is \"all\", \"personal\" or names among {LABELS}, not {labels!r}")
        _, tagged = predict_spans(self._run, self.tags, self._encode, texts, batch=1, fit=self.fit)
        out = []
        for spans, text in zip(tagged, texts):
            found = merge(spans, find_by_rule(text))
            if labels == "personal":
                out.append(personal(text, found))
            else:
                out.append([span for span in final(text, found) if labels == "all" or span[2] in wanted])
        return out

    def find(self, text, labels="all"):
        return self.find_all([text], labels)[0]

    def redact(self, text, labels="all"):
        """The text with each span replaced by its label and a number; equal text gets the same number."""
        return redact(text, self.find(text, labels))
