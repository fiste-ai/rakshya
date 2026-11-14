"""Convert between character spans and per-token tags.

A span is (start, end, label) with code-point offsets. A token is a (start, end) character
range. Nepali case markers attach to the word, so a span often ends inside a token; the
"trim" of a token is the number of characters at its end that lie past the end of its span.
"""

import unicodedata

from .labels import NAMES, NUMBERS, canonical

STARTS = "BSU"
MAX_TRIM = 8
SENTENCE_END = "।?!"
SPACE = " \t\r\n\u00a0"


def is_digit(ch):
    """A Latin or a Devanagari digit."""
    return "0" <= ch <= "9" or "०" <= ch <= "९"


def in_word(ch):
    """True for letters and the vowel signs that attach to them; false for digits and the danda."""
    return ch.isalpha() or unicodedata.category(ch) in ("Mn", "Mc")


def clean_offsets(text, offsets):
    """Drop leading whitespace from each token's character range."""
    out = []
    for a, b in offsets:
        while a < b and text[a].isspace():
            a += 1
        out.append((a, b))
    return out


def split_tag(tag):
    """Return (prefix, label) for a tag such as "B-PERSON"; (None, None) for "O"."""
    if tag == "O":
        return None, None
    if len(tag) > 2 and tag[1] == "-":
        return tag[0], tag[2:]
    return "I", tag


def encode(spans, offsets, max_trim=MAX_TRIM):
    """Tag every token with the span it overlaps.

    `spans` must be sorted and must not overlap. Returns (tags, trims): tags[i] is "O",
    "B-X" or "I-X"; trims[i] is the trim of token i, or None when the token is "O".
    """
    tags = ["O"] * len(offsets)
    trims = [None] * len(offsets)
    k = 0
    opened = -1
    for i, (a, b) in enumerate(offsets):
        if b <= a:
            continue
        while k < len(spans) and spans[k][1] <= a:
            k += 1
        if k == len(spans):
            break
        start, end, label = spans[k]
        if start < b:
            tags[i] = ("I-" if opened == k else "B-") + label
            trims[i] = min(max(0, b - end), max_trim)
            opened = k
    return tags, trims


def decode(tags, offsets, trims=None):
    """Merge token tags into character spans.

    A B, S or U prefix starts a span. Any other prefix continues the open span when the
    label matches and starts one otherwise. With `trims`, the end of each span is pulled
    back by the trim of its last token.

    A token that starts where the next token starts adds no characters. That is the word
    marker "▁" standing as a token of its own: the tokenizer gives it the first letter of
    the word that follows, which the next token covers again. It opens or continues a span
    like any other token, but a span that ends on it must not take that letter.
    """
    found = []
    cur = None
    for i, tag in enumerate(tags):
        a, b = offsets[i]
        prefix, label = split_tag(tag)
        if b <= a or label is None:
            cur = None
            continue
        marker = i + 1 < len(offsets) and offsets[i + 1][0] == a < offsets[i + 1][1]
        if cur is not None and prefix not in STARTS and cur[2] == label:
            if not marker:
                cur[1], cur[3] = b, i
        else:
            cur = [a, a if marker else b, label, i]
            found.append(cur)
    spans = []
    for a, b, label, last in found:
        if b <= a:
            continue
        if trims is not None and trims[last]:
            b = max(offsets[last][0] + 1, b - trims[last])
        spans.append((a, b, label))
    return spans


def first_token_tags(tags, offsets):
    """Give every token of a whitespace word the label of the word's first token.

    This is how token-level NER scores are usually computed: one label per word.
    """
    out = []
    label = None
    last_end = None
    for tag, (a, b) in zip(tags, offsets):
        if b <= a:
            out.append("O")
            last_end = None
        elif last_end is None or a > last_end:
            label = split_tag(tag)[1]
            out.append(tag)
            last_end = b
        else:
            out.append("O" if label is None else "I-" + label)
            last_end = b
    return out


def glue(tags, offsets):
    """Turn B- into I- where a token touches the token before it and has the same label.

    Some models put B- on every piece of a word. Read as written, one name or e-mail address
    would come out as several spans.
    """
    out = list(tags)
    for i in range(1, len(tags)):
        prefix, label = split_tag(tags[i])
        touches = offsets[i][1] > offsets[i][0] == offsets[i - 1][1] > offsets[i - 1][0]
        if label and prefix in STARTS and touches and label == split_tag(tags[i - 1])[1]:
            out[i] = "I-" + label
    return out


def merge_adjacent(text, spans):
    """Join neighbouring spans of one label that are separated only by whitespace."""
    out = []
    for start, end, label in sorted(spans):
        if out and out[-1][2] == label and not text[out[-1][1]:start].strip():
            out[-1] = (out[-1][0], end, label)
        else:
            out.append((start, end, label))
    return out


def strip_markers(text, spans, markers):
    """Cut a known case marker off every span that runs to the end of its word."""
    ordered = sorted(markers, key=len, reverse=True)
    out = []
    for start, end, label in spans:
        if end == len(text) or not in_word(text[end]):
            for marker in ordered:
                if text[start:end].endswith(marker) and end - start - len(marker) >= 2:
                    end -= len(marker)
                    break
        out.append((start, end, label))
    return out


def to_word_start(text, spans):
    """Move a span that starts inside a word back to the start of that word.

    Names do not start inside a word: 28 of the 138,681 spans in the training data do. A
    predicted span that does has lost its first pieces. The start moves back no further
    than the end of the span before it, and a span that starts with a digit is left alone,
    because a keyword may be written against a number without a space.
    """
    out = []
    for start, end, label in sorted(spans):
        floor = out[-1][1] if out else 0
        if in_word(text[start]):
            while start > floor and in_word(text[start - 1]):
                start -= 1
        out.append((start, end, label))
    return out


def split_repeats(text, spans):
    """Cut a name that is the same two or more words said twice into one span for each copy.

    A web page prints a name in its heading and again above the details, and with only a
    space between the two the tagger reads one long name. No name in the training or test
    files repeats like this. A single word may (अब्दुल्लाह अब्दुल्लाह is one person), so one
    word twice is left alone.
    """
    out = []
    for start, end, label in spans:
        words, at = [], start
        while at < end:
            if text[at] in SPACE:
                at += 1
                continue
            stop = at
            while stop < end and text[stop] not in SPACE:
                stop += 1
            words.append((at, stop))
            at = stop
        n = len(words)
        unit = 0
        if label in NAMES:
            for size in range(2, n // 2 + 1):
                if n % size == 0 and all(text[slice(*words[k])] == text[slice(*words[k % size])]
                                         for k in range(size, n)):
                    unit = size
                    break
        if unit:
            out.extend((words[k][0], words[k + unit - 1][1], label) for k in range(0, n, unit))
        else:
            out.append((start, end, label))
    return out


def plausible(value, label):
    """False for a span that cannot be personal data of the kind its label names, nor of another kind.

    The tagger sometimes labels a piece of a year or a time as an identifier or a date. No
    number in `NUMBERS` has fewer than four digits; a number plate has two or more and
    a letter; a date has a digit and is more than a time of day. A number with the wrong
    count of digits for its label is kept, because it may be an identifier of another kind
    and dropping it would leave it in the text. The other checks are as loose: an identity
    number of another kind has two digits, an address of a machine has a digit and a dot or
    a colon, a payment address has an "@", and a secret or a user name is not a single letter.
    """
    digits = sum(is_digit(ch) for ch in value)
    if label in NUMBERS:
        return digits >= 4
    if label == "VEHICLE_PLATE":
        return digits >= 2 and any(in_word(ch) for ch in value)
    if label == "DATE":
        return digits > 0 and not (":" in value and all(is_digit(ch) or ch == ":" for ch in value))
    if label == "ID_NUMBER":
        return digits >= 2
    if label == "IP_ADDRESS":
        return digits > 0 and ("." in value or ":" in value)
    if label == "UPI_ID":
        return "@" in value
    if label in ("SECRET", "USERNAME"):
        return len(value) >= 3
    return True


def tidy(text, spans):
    """The spans of the tagger with repeated names cut apart and impossible ones dropped."""
    return [span for span in split_repeats(text, spans) if plausible(text[span[0]:span[1]], span[2])]


def segments(text, limit=320, hard=1200):
    """Cut a text into the pieces the tagger reads one at a time, as (start, end) ranges.

    The tagger was trained on short texts: 99 in 100 have under 300 characters. A piece ends
    after a line break, or after a sentence end (। ? !) that a space follows. Neighbouring
    pieces are joined while together they stay within `limit` characters, so a form of
    short lines stays whole and a long article is read a sentence or two at a time. One
    sentence longer than `hard` characters is cut at a space. The ranges cover the text.
    """
    n = len(text)
    cuts = [0]
    for i, ch in enumerate(text):
        if ch == "\n" or (ch in SENTENCE_END and i + 1 < n and text[i + 1] in SPACE and text[i + 1] != "\n"):
            if i + 1 < n:
                cuts.append(i + 1)
    cuts.append(n)
    atoms = []
    for start, end in zip(cuts, cuts[1:]):
        while end - start > hard:
            cut = start + hard
            while cut > start + hard // 2 and text[cut] not in SPACE:
                cut -= 1
            if text[cut] not in SPACE:
                cut = start + hard
            atoms.append((start, cut))
            start = cut
        atoms.append((start, end))
    out = []
    start = end = 0
    for a, b in atoms:
        if end > start and b - start > limit:
            out.append((start, end))
            start = a
        end = b
    if end > start:
        out.append((start, end))
    return out


def merge(tagger_spans, rule_spans):
    """Rule matches, plus every tagger span that touches none of them."""
    kept = [t for t in tagger_spans if all(t[1] <= r[0] or r[1] <= t[0] for r in rule_spans)]
    return sorted(list(rule_spans) + kept)


def redact(text, spans):
    """Replace each span with a numbered placeholder; equal text gets the same number."""
    seen = {}
    out, last = [], 0
    for start, end, label in sorted(spans):
        if start < last:
            continue
        numbers = seen.setdefault(label, {})
        number = numbers.setdefault(text[start:end], len(numbers) + 1)
        out.append(text[last:start] + f"[{label}_{number}]")
        last = end
    return "".join(out) + text[last:]


def tag_names(labels):
    """The tags of a model with these labels. A label under an old name is read under its current one."""
    return ["O"] + [f"{prefix}-{canonical(label)}" for label in labels for prefix in "BI"]


def predict_spans(run, tags, tokenizer, texts, max_tokens=6000, max_length=512, batch=64):
    """Cut `texts` into pieces, tokenize them in batches of similar length and read the spans off the model.

    With `batch=1` every piece is run on its own, as the browser runs it. The 8-bit file of
    release 0.1 set the scale of its activations from the whole batch, so what it found in a
    piece could change with the pieces beside it. The file of 0.2 rounds only the weights and
    has no such dependence, but the released runtime still runs the pieces one by one.

    `run(input_ids, attention_mask)` takes two integer arrays and returns, for every token,
    the index of its tag and its trim, as nested lists. Returns (plain, trimmed): the spans
    per text as the tokens give them, and after the trim, the move to the word start and the
    checks of `tidy`.
    """
    pieces = [(i, start, text[start:end]) for i, text in enumerate(texts) for start, end in segments(text)]
    order = sorted(range(len(pieces)), key=lambda k: len(pieces[k][2]))
    plain = [[] for _ in texts]
    trimmed = [[] for _ in texts]
    k = 0
    while k < len(order):
        longest = len(pieces[order[min(k + batch - 1, len(order) - 1)]][2])
        size = max(1, min(batch, max_tokens // max(1, longest // 2)))
        idx = order[k:k + size]
        k += size
        enc = tokenizer([pieces[j][2] for j in idx], return_offsets_mapping=True, truncation=True,
                        max_length=max_length, padding=True, return_tensors="np")
        offsets = enc["offset_mapping"].tolist()
        mask = enc["attention_mask"].tolist()
        tag_ids, trims = run(enc["input_ids"], enc["attention_mask"])
        for row, j in enumerate(idx):
            i, shift, piece = pieces[j]
            offs = [(a, b) if m else (0, 0) for (a, b), m in zip(offsets[row], mask[row])]
            offs = clean_offsets(piece, offs)
            names = [tags[t] for t in tag_ids[row]]
            plain[i] += [(a + shift, b + shift, label) for a, b, label in decode(names, offs)]
            trimmed[i] += [(a + shift, b + shift, label)
                           for a, b, label in tidy(piece, to_word_start(piece, decode(names, offs, trims[row])))]
    return [sorted(spans) for spans in plain], [sorted(spans) for spans in trimmed]
