"""Convert between character spans and per-token tags.

A span is (start, end, label) with code-point offsets. A token is a (start, end) character
range. Nepali case markers attach to the word, so a span often ends inside a token; the
"trim" of a token is the number of characters at its end that lie past the end of its span.
"""

import unicodedata

from .labels import EARLY, NAMES, NUMBERS
from .rules import MOBILE_PREFIX, fold

STARTS = "BSU"
MAX_TRIM = 8
SENTENCE_END = "।?!"
SPACE = " \t\r\n\u00a0"
HYPHENS = "-\u2010\u2011\u2012\u2013\u2014\u2015\u2212"


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


def follows(tags):
    """For each tag, the tags that may stand before it: a tag that continues a span follows only a tag of its label."""
    parts = [split_tag(tag) for tag in tags]
    return [[i for i, (_, before) in enumerate(parts) if prefix is None or prefix in STARTS or before == label]
            for prefix, label in parts]


def fit_tags(scores, offsets, tags):
    """The tags of a piece that fit together: the best sequence in which I-X follows only B-X or I-X.

    `scores` holds for every token the model's score of every tag, as the model gives them.
    The highest tag of each token, taken alone, can break a name in the middle: B-ORG, I-LOC,
    I-ORG reads as three spans. Here the sequence with the largest sum of scores is taken among
    those that `encode` could have written.

    A token without characters gets "O" and ends a stretch, as `decode` ends a span there. The
    first token of a stretch may take any tag, since `decode` opens a span on an I-X that
    follows nothing. Where two tags give one sum, the one earlier in `tags` is taken. The sums
    are made in 64-bit floats, token after token, so that the Rust code makes the same ones.
    """
    import numpy

    scores = numpy.asarray(scores, dtype=numpy.float64)
    before = follows(tags)
    gate = numpy.full((len(tags), len(tags)), -numpy.inf)
    for j, allowed in enumerate(before):
        gate[allowed, j] = 0.0
    out = [tags.index("O")] * len(offsets)
    t = 0
    while t < len(offsets):
        if offsets[t][1] <= offsets[t][0]:
            t += 1
            continue
        start = t
        while t < len(offsets) and offsets[t][1] > offsets[t][0]:
            t += 1
        best = scores[start]
        back = []
        for s in range(start + 1, t):
            reached = best[:, None] + gate
            back.append(reached.argmax(0))
            best = reached.max(0) + scores[s]
        k = int(best.argmax())
        for s in range(t - 1, start, -1):
            out[s] = k
            k = int(back[s - start - 1][k])
        out[start] = k
    return out


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


LOST = 4


def to_word_start(text, spans):
    """Move a span that starts inside a word back to the start of that word.

    Names do not start inside a word: 28 of the 138,681 spans in the training data do. A
    predicted span that does has lost its first pieces. The start moves back no further
    than the end of the span before it, and a span that starts with a digit is left alone,
    because a keyword may be written against a number without a space.

    A lost piece is short. Where more than `LOST` characters stand before the span in its
    word, they are a word of their own that a page ran against the name, a post before a
    person in a table (सदस्यराम थापा), and the span stays where the tagger put it. On the
    real sets and the traps the small model starts 29 spans that far inside a word: 13 of
    them where an expected span starts, 3 where the word start would have been right.
    """
    out = []
    for start, end, label in sorted(spans):
        floor = out[-1][1] if out else 0
        if in_word(text[start]):
            first = start
            while first > floor and in_word(text[first - 1]):
                first -= 1
            if start - first <= LOST:
                start = first
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


def split_lines(text, spans):
    """Cut a name or a date that runs over a line break into one span for each line.

    A page lists names one under the other, or prints a given name on one line and the family
    name on the next, and the tagger reads the lines as one name. Of the 300,000 names and
    dates in the training rows, four hold a line break, and no label of a test set can hold
    one. A value of another kind may run over lines, as a private key does, and is left whole.
    """
    out = []
    for start, end, label in spans:
        if (label in NAMES or label == "DATE") and "\n" in text[start:end]:
            at = start
            for line in text[start:end].split("\n"):
                a, b = at, at + len(line)
                while a < b and text[a] in SPACE:
                    a += 1
                while b > a and text[b - 1] in SPACE:
                    b -= 1
                if b > a:
                    out.append((a, b, label))
                at += len(line) + 1
        else:
            out.append((start, end, label))
    return out


def is_year(value):
    """Four digits that begin with 19 or 20, in Latin or Devanagari digits."""
    return len(value) == 4 and all(is_digit(ch) for ch in value) and value[0] in "1१2२" and value[1] in "9९0०" \
        and (value[0] in "1१") == (value[1] in "9९")


def split_ranges(text, spans):
    """Cut a date that is two years joined by a hyphen into the two years: "२०५३-२०५६", "2015 \u2013 2017".

    The tagger marks the term of a committee or the years of a course as one date. Each of the years is a date;
    the two together are a stretch of time, which is not marked.
    """
    out = []
    for start, end, label in spans:
        value = text[start:end]
        middle = value[4:-4].strip(SPACE)
        if label == "DATE" and len(value) >= 9 and is_year(value[:4]) and is_year(value[-4:]) and len(middle) == 1 and middle in HYPHENS:
            out += [(start, start + 4, label), (end - 4, end, label)]
        else:
            out.append((start, end, label))
    return out


BLANK = " \t\u00a0"
# Before a hyphen these are the first half of one name, not a place of their own: a rank of a local level
# ("Sub-Metropolitan City", "उप-महानगरपालिका") and the countries and states that are written with a hyphen.
HALVES = ("sub", "उप", "जम्मू", "jammu", "टिमोर", "timor", "गिनी", "guinea", "बोस्निया", "bosnia", "अंडमान", "andaman",
          "दमन", "daman", "दादरा", "dadra")
ROADS = ("राजमार्ग", "सडक", "सडकखण्ड", "लोकमार्ग", "द्रुतमार्ग", "रेलमार्ग", "कोरिडोर", "expressway", "highway", "road", "corridor",
         "railway")


def last_word(text, start, end):
    """Where the last word of text[start:end] begins."""
    at = end
    while at > start and text[at - 1] not in SPACE:
        at -= 1
    return at


def split_places(text, spans):
    """Cut a place span at the hyphens that join places: "नेपाल-भारत", "Kathmandu - Dhangadhi", "रणवाङ-दरुङ-हिदी".

    The guide marks places joined by a hyphen one by one, and the readers did so for 86 pairs in the development
    sets and the text labelled by hand; the tagger learned from rows that make one span of such a pair and often
    gives one. A span is cut only where each part can be a place of its own: three characters or more, no
    figure and no small Latin letter at its start (a ward number, "Hakha-baha"), and no first half of a name
    that is written with a hyphen before the cut (`HALVES`). Of the 18 places that the readers left whole with
    a hyphen inside, 17 stay whole by these checks. Where places are cut apart and the last one ends in the
    word for a road, the road is named by its ends and the word stays outside ("गल्छी-त्रिशूली राजमार्ग").
    """
    out = []
    for start, end, label in spans:
        parts, at, i = [], start, start
        while label == "LOCATION" and i < end:
            if text[i] in HYPHENS:
                a, b = i, i + 1
                while a > at and text[a - 1] in BLANK:
                    a -= 1
                while b < end and text[b] in BLANK:
                    b += 1
                parts.append((at, a))
                at = i = b
            else:
                i += 1
        parts.append((at, end))
        alone = all(b - a >= 3 and not is_digit(text[a]) and not "a" <= text[a] <= "z" for a, b in parts)
        if len(parts) == 1 or not alone or any(text[last_word(text, a, b):b].lower() in HALVES for a, b in parts[:-1]):
            out.append((start, end, label))
            continue
        a, b = parts[-1]
        word = last_word(text, a, b)
        if word > a and text[word:b].lower() in ROADS:
            b = word
            while b > a and text[b - 1] in SPACE:
                b -= 1
            word = last_word(text, a, b)
            if word > a and text[word:b].lower() in ("राष्ट्रीय", "national"):
                b = word
                while b > a and text[b - 1] in SPACE:
                    b -= 1
            parts[-1] = (a, b)
        out += [(a, b, label) for a, b in parts]
    return out


def four_numbers(value):
    """True when four numbers stand joined by dots in `value`, the two inner ones of at most three digits.

    That is the form of an address of a machine, with whatever is written against it: a port, a bracket. The
    figures of a table ("26264.8770.026%") and the number of a version ("126.0.6478.127") do not have it.
    """
    lengths, digits = [], 0
    for ch in value + " ":
        if is_digit(ch):
            digits += 1
        elif ch == "." and digits:
            lengths.append(digits)
            digits = 0
        else:
            if digits:
                lengths.append(digits)
            if any(lengths[k + 1] <= 3 and lengths[k + 2] <= 3 for k in range(len(lengths) - 3)):
                return True
            lengths, digits = [], 0
    return False


# The version of the checks that the spans of a tagger pass before they are kept (`plausible`, in `tidy`). It goes up
# when a check lets through what it dropped before: what was kept under an older version lacks those spans, so a
# file kept under another version is read again (`baselines.keep`, `practical.tags_of`).
CHECKS = 3


def words(value):
    """How many words a value has: its stretches without white space."""
    count, inside = 0, False
    for ch in value:
        if ch in SPACE:
            inside = False
        elif not inside:
            count, inside = count + 1, True
    return count


def plausible(value, label):
    """False for a span that cannot be personal data of the kind its label names, nor of another kind.

    The tagger sometimes labels a piece of a year or a time as an identifier or a date. No
    number in `NUMBERS` has fewer than four digits; a number plate has two or more and
    a letter; a date has a digit and is more than a time of day. The labels are known under
    their final names and under those of 0.2 and 0.3, which a model of those releases still gives. A number with the wrong
    count of digits for its label is kept, because it may be an identifier of another kind
    and dropping it would leave it in the text. The other checks are as loose: an identity
    number of another kind has two digits, a payment address has an "@", and a secret or a
    user name is not a single letter. An address of a machine has four numbers joined by dots,
    or two colons: the tagger takes the figures of a table for addresses, and no kind of
    personal data is written as two or three numbers with dots between them.

    Three things pass that have no figure, or nothing but figures. A number said in words ("नौ आठ चार एक ...",
    "four four oh one, seven seven two") is four words or more and is not the piece of a year that the count of
    digits is there to stop. A date of two words or more is one without a figure ("असोज मसान्त", "August ninth,
    nineteen sixty-four"); a month alone is not. A secret in figures alone is a PIN, a code sent to a phone, the
    figures on the back of a card or the number of a handset, which the guide of 1.0 has under the one label with
    the address of a machine. On the development data of 2026-11-18 the model of 1.0 gave 27 secrets in figures
    alone, 23 of them answers, and 4 phone numbers in words, all answers; of 6 dates of two words 4 were.
    """
    digits = sum(is_digit(ch) for ch in value)
    worded = digits == 0 and words(value) >= 4
    if label in NUMBERS:
        return digits >= 4 or worded
    if label in ("VEHICLE_PLATE", "VEHICLE_ID"):
        return digits >= 2 and any(in_word(ch) for ch in value)
    if label in ("DATE", "DOB"):
        if digits == 0:
            return words(value) >= 2
        return not (":" in value and all(is_digit(ch) or ch == ":" for ch in value))
    if label in ("ID_NUMBER", "MEDICAL_ID", "EMPLOYEE_STUDENT_ID", "PROPERTY_UTILITY_ID"):
        return digits >= 2 or worded
    if label == "IP_ADDRESS":
        return digits > 0 and (four_numbers(value) or value.count(":") >= 2)
    if label == "UPI_ID":
        return "@" in value
    if label in ("SECRET", "USERNAME", "PAYMENT_ID"):
        return len(value) >= 3
    if label == "DIGITAL_SECRET":
        # One label of 1.0 for what was three. Figures alone are a code or the number of a device. Figures with dots
        # or colons are held to the form of an address of a machine, as before; anything else to the length of a
        # password or a user name.
        if digits == len(value):
            return digits >= 3
        if all(is_digit(ch) or ch in ".:" for ch in value):
            return digits > 0 and (four_numbers(value) or value.count(":") >= 2)
        return len(value) >= 3
    return True


VISARGA = "\u0903"


def is_mark(ch):
    """A vowel sign, a virama, a nukta or another sign that is written on the letter before it."""
    return unicodedata.category(ch) in ("Mn", "Mc")


def whole_letters(text, spans):
    """Move an edge that cuts a letter in two.

    The tagger reads pieces of words, and a piece may end between a consonant and its vowel sign: "टर्क" and
    "ीले". A span that ends there takes the signs that complete its last letter, and one that starts on a sign
    gives it up. The visarga stays outside, since pages write it for a colon ("फोनः"). Of the 440,000 spans of
    the labelled rows and of the text labelled by hand, none ends before another sign.
    """
    out = []
    for start, end, label in spans:
        while end < len(text) and is_mark(text[end]) and text[end] != VISARGA:
            end += 1
        while start < end and is_mark(text[start]):
            start += 1
        if start < end:
            out.append((start, end, label))
    return out


def join_short_forms(text, spans):
    """Make one span of an organisation and its short form in brackets: "Rastriya Swatantra Party (RSP)".

    The guide takes the short form into the span of the name. The Nepali rows the tagger learned from are
    written so, and it reads Nepali so. The English and Hindi rows mark the two apart, and so does the tagger
    in those languages. The two are joined when both are marked as organisations, nothing but spaces and the
    opening bracket stands between them on one line, the short form is one word, and the bracket closes after it.
    """
    out = []
    for start, end, label in sorted(spans):
        if out and label == "ORGANIZATION" == out[-1][2]:
            gap, close = text[out[-1][1]:start], end
            while close < len(text) and text[close] in " \u00a0":
                close += 1
            if gap.strip(" \u00a0") == "(" and text[close:close + 1] == ")" and not any(ch in SPACE for ch in text[start:end]):
                out[-1] = (out[-1][0], close + 1, label)
                continue
        out.append((start, end, label))
    return out


# What stands before the name of a person and is no part of it, and the particle of respect after it. The readers
# left these titles outside 422 times in 423, and a word of respect after a name 385 times in 386 (development
# sets and text labelled by hand).
TITLES = ("श्रीमती", "सुश्री", "श्री", "डा.", "डा", "डॉ.", "डॉ", "प्रा.", "प्रो.", "Dr.", "Dr", "Prof.", "Er.", "Mr.", "Mrs.", "Ms.")
RESPECT = ("जी", "ज्यू")


def without_titles(text, start, end):
    """Where the name of a person begins after the titles that stand before it. Two characters of the name are left."""
    while True:
        for title in TITLES:
            stop = start + len(title)
            if text[start:stop] == title and stop < end and (text[stop] in SPACE or title[-1] == "."):
                while stop < end and text[stop] in SPACE:
                    stop += 1
                if end - stop >= 2:
                    break
        else:
            return start
        start = stop


# The labels of numbers that are written in figures and letters and never begin or end with half a pair of brackets.
OF_NUMBERS = (*NUMBERS, "ID_NUMBER", "MEDICAL_ID", "EMPLOYEE_STUDENT_ID", "PROPERTY_UTILITY_ID", "VEHICLE_ID", "VEHICLE_PLATE")


def without_stray_bracket(text, start, end):
    """A span without the round bracket at its edge that does not close inside it, or was not opened inside it.

    A number given in brackets after a name, "फूलमती देवी (9931284076)", is the number. The model of 1.0 took the
    opening bracket into six such spans on the development data, and each was an answer without it. The area code
    of a phone number in brackets stays: "(061) 520123" closes its bracket.
    """
    value = text[start:end]
    if value[:1] == "(" and ")" not in value:
        return start + 1, end
    if value[-1:] == ")" and "(" not in value:
        return start, end - 1
    return start, end


def trim_edges(text, spans):
    """Leave out what stands at the edge of a span and is never part of it.

    A mobile number of Nepal has ten figures. Eleven or twelve figures in a row that begin as one does are the
    number with the next cell of a table against it, most often the number of the next row in a list of staff
    ("9841234567" and then "2. श्री ..."). Of eight such spans on the development files seven are the number
    in their first ten figures, and six of seven on hand-labelled text that the model had not read. A phone
    number does not begin with the slash that joins it to the number before it. A bracket that does not close
    inside a name, a date or a number, or does not open inside it, stands outside: "(२०२३" is the year. A title before the
    name of a person and the particle of respect after it are not part of the name: "डा. राम थापा", "मोदी जी".
    """
    out = []
    for start, end, label in spans:
        if label in ("PHONE", "OFFICE_PHONE"):
            figures = fold(text[start:end])
            if len(figures) in (11, 12) and all("0" <= ch <= "9" for ch in figures) and MOBILE_PREFIX.match(figures):
                end = start + 10
            while start < end and text[start] in "/ \u00a0":
                start += 1
            start, end = without_stray_bracket(text, start, end)
        elif label in OF_NUMBERS:
            start, end = without_stray_bracket(text, start, end)
        elif label in NAMES or label == "DATE":
            if label == "PERSON":
                start = without_titles(text, start, end)
                for word in RESPECT:
                    cut = end - len(word) - 1
                    if cut - start >= 2 and text[cut + 1:end] == word and text[cut] in " \u00a0":
                        end = cut
                        break
            value = text[start:end]
            if value.startswith("(") and ")" not in value:
                start += 1
            elif value.endswith(")") and "(" not in value:
                end -= 1
            while start < end and text[start] in SPACE:
                start += 1
            while end > start and text[end - 1] in SPACE:
                end -= 1
        if start < end:
            out.append((start, end, label))
    return out


def tidy(text, spans):
    """The spans of the tagger as they are given out.

    Repeated names, names over a line break, two years and places joined by a hyphen are cut apart, an edge that
    cuts a letter is moved, impossible spans are dropped, what stands at an edge and is never part of a span is
    left out, and the short form of an organisation in brackets is joined to it.
    """
    cut = whole_letters(text, split_places(text, split_ranges(text, split_lines(text, split_repeats(text, spans)))))
    return join_short_forms(text, trim_edges(text, [span for span in cut if plausible(text[span[0]:span[1]], span[2])]))


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


# What a model of 1.0 can tell and a rule cannot: the label of the model, and the labels of the rules that it refines.
# A rule knows a date, a number after a keyword, a phone number, a mailbox and a web address by their form; whether the
# date is a date of birth, whose the phone number is, and whether a link carries a token or leads to a person's own
# page is in the words around them.
FINER = {"DOB": ("DATE",), "MEDICAL_ID": ("ID_NUMBER",), "EMPLOYEE_STUDENT_ID": ("ID_NUMBER",), "PROPERTY_UTILITY_ID": ("ID_NUMBER",),
         "OFFICE_PHONE": ("PHONE",), "OFFICE_EMAIL": ("EMAIL",), "DIGITAL_SECRET": ("URL",), "PAYMENT_ID": ("PHONE", "EMAIL", "URL")}
# Where the span of the model stands whole and what the rules find inside it goes: a house number that looks like a
# date and a plot number after its keyword inside an address; the part of a private link or of an e-mail address
# that a rule takes for a web address; the phone number or the address that is a wallet's identity.
WHOLE = {"ADDRESS": ("DATE", "ID_NUMBER"), "DIGITAL_SECRET": ("URL",), "EMAIL": ("URL",), "PAYMENT_ID": ("PHONE", "EMAIL", "URL")}


def merge(tagger_spans, rule_spans):
    """Rule matches, plus every tagger span that touches none of them.

    A model of 1.0 knows more than the rules in two ways (`WHOLE`, `FINER`). Where its span holds everything that
    the rules find there, and what they find is what such a span may hold, its span stands and theirs go. Else,
    where it gives the finer label for what the rules have by its form, the match of the rules keeps its edges
    and takes the label of the model. A model of 0.2 or 0.3 marks none of the labels for which this holds but
    for an e-mail address around a web address, where its span was dropped before.
    """
    rules = [list(r) for r in rule_spans]
    kept, gone = [], set()
    for t in tagger_spans:
        touching = [k for k, r in enumerate(rules) if not (t[1] <= r[0] or r[1] <= t[0])]
        if not touching:
            kept.append(t)
        elif all(t[0] <= rules[k][0] and rules[k][1] <= t[1] and rules[k][2] in WHOLE.get(t[2], ()) for k in touching):
            kept.append(t)
            gone.update(touching)
        elif all(rules[k][2] in FINER.get(t[2], ()) for k in touching):
            for k in touching:
                rules[k][2] = t[2]
    return sorted([tuple(r) for k, r in enumerate(rules) if k not in gone] + kept)


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
    """The tags of a model with these labels, as the checks on its spans know them.

    A model of 0.2 or 0.3 keeps its own names here (the name of release 0.1 for the tax number apart): `plausible` asks
    other things of an address of a machine than of a password. `labels.rename` gives the final names where spans leave the code.
    """
    return ["O"] + [f"{prefix}-{EARLY.get(label, label)}" for label in labels for prefix in "BI"]


def predict_spans(run, tags, tokenizer, texts, max_tokens=6000, max_length=512, batch=64, fit=False):
    """Cut `texts` into pieces, tokenize them in batches of similar length and read the spans off the model.

    With `fit` the tags of a piece are those that fit together (`fit_tags`), and `run` returns
    the scores of every tag for every token in place of the index of the highest.

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
            names = [tags[t] for t in (fit_tags(tag_ids[row], offs, tags) if fit else tag_ids[row])]
            plain[i] += [(a + shift, b + shift, label) for a, b, label in decode(names, offs)]
            trimmed[i] += [(a + shift, b + shift, label)
                           for a, b, label in tidy(piece, to_word_start(piece, decode(names, offs, trims[row])))]
    return [sorted(spans) for spans in plain], [sorted(spans) for spans in trimmed]
