"""What 1.0 split off from older labels, told by the words beside a span.

Text labelled before 1.0 has every number that a body gives one person under `ID_NUMBER`, a
date of birth among its dates, and the place where a person lives as places one by one.
Before a model of 1.0 learns from such a row, three things are done with it (`retype`):

  * a number named by a word of one of three kinds (`CUES`) takes that kind, and the number
    of a device (`DEVICE`) becomes a `DIGITAL_SECRET`;
  * a date with a word for birth directly before or after it, and at least two of day,
    month and year, becomes a `DOB`;
  * places that the row gives as where a person lives, with a part below the city (a ward,
    or two places in a row), become one stretch labelled "?", which the loss does not look
    at. 1.0 has them as one `ADDRESS` and the row has them one by one; where the address
    begins and ends is for a reader to say, not for a rule.

Nothing else changes: a row keeps every other span as it is. The test sets are not changed
at all; a score on them counts the new labels with the old ones (`rakshya.release`).

The first two also hold for what the rules and a model mark in a text (`final`): the rules
give every number after a keyword one label and every date the label `DATE`.

The same words decide the kind of a number in a batch of practical paragraphs whose labels
are coarser than the final ones (`rakshya.practical`).

    python -m rakshya.kinds --export wasm/kinds.json

writes the tables and patterns of `final` and `personal` for the Rust build (`wasm/src/kinds.rs`),
which gives the same answers (`python -m rakshya.parity`). So those patterns use nothing that
only one of the two engines has: no look-ahead, no look-behind, no word boundary. What must
or must not stand beside a match is checked in code, the same way on both sides.
"""
import re

from .labels import ALIASES, OFFICE, PERSONAL, canonical, said
from .rules import ENGLISH_MONTH, MONTH

# The word that names a number tells its kind. Looked for in the 48 characters before the span, the nearest first.
CUES = {
    "EMPLOYEE_STUDENT_ID": ("employee", "emp id", "emp. id", "emp code", "staff id", "staff no", "payroll", "badge", "uan", "epf", "pf no",
                            "pf number", "ppo", "provident", "student", "roll no", "roll number", "symbol no", "symbol number",
                            "admission no", "कर्मचारी", "विद्यार्थी", "छात्र", "रोल नं", "सिम्बोल", "अनुक्रमांक", "भविष्य निधि", "संचय कोष",
                            "सञ्चय कोष", "श्रम स्वीकृति", "यूएएन", "पीएफ", "पीपीओ"),
    "PROPERTY_UTILITY_ID": ("ration", "consumer", "meter no", "meter number", "kitta", "khasra", "khatauni", "lalpurja", "sheet no",
                            "उपभोक्ता", "मिटर", "मीटर", "कित्ता", "खसरा", "राशन", "लालपुर्जा", "सिट नं"),
    "MEDICAL_ID": ("health insurance", "patient", "mrn", "uhid", "abha", "स्वास्थ्य बीमा", "स्वास्थ्य बिमा", "बिरामी", "मरीज", "रोगी"),
}
# The words before the number of a person's device.
DEVICE = ("imei", "mac address", "device id", "आईएमईआई")
MAC = re.compile(r"(?i)[0-9a-f]{2}(?:[:-][0-9a-f]{2}){5}")
SENTENCE_END = "।?!"
FIGURES = re.compile(r"[0-9०-९]+")
MONTH_NAME = re.compile(rf"(?i){MONTH}|{ENGLISH_MONTH}")
DEVA = "\u0900-\u097f"
# White space, written out so that it is the same set in Python and in Rust.
SP = r"[ \t\n\r\u00a0]"
# The words for birth before a date, of three kinds by what may stand around them. The first are words enough. The
# second are Latin words that must stand alone ("born", not "stubborn"; "dob", not "adobe"): no Latin letter or figure
# before them, none after them. The third is the Nepali and Hindi stem with its endings, after which no further
# Devanagari letter may follow ("जन्मेका", not "जन्मस्थान"). `birth_cue` checks the last two in code.
BIRTH_PLAIN = (rf"date{SP}*of{SP}*birth|birth{SP}*date|birthdate|birthday|जन्म{SP}*मित[िी]|जन्ममित[िी]|जन्म{SP}*तिथि|जन्मतिथि|जन्म{SP}*दिन|जन्मदिन|"
               rf"janma{SP}*miti|janmamiti|janma{SP}*din|janmadin")
BIRTH_WORD = rf"d\.?{SP}?o\.?{SP}?b|born|janma"
BIRTH_STEM = r"जन्म(?:ेक[ोाी]|िएक[ोाी]|[ेी])?"
BIRTH = re.compile(rf"(?i)(?P<plain>{BIRTH_PLAIN})|(?P<word>{BIRTH_WORD})|(?P<stem>{BIRTH_STEM})")
BORN_AFTER = re.compile(rf"(?i){SP}*(?:(?:गते|तारिख|तारीख|का{SP}+दिन|को{SP}+दिन|के{SP}+दिन|मा|में|को|,|ma|ko){SP}*){{0,3}}(?:जन्म|पैदा|janm)")
# Between the word for birth and a date these make it another date: the day a birth was registered, the place of birth.
NOT_BIRTH = re.compile(r"(?i)दर्ता|प्रमाण|regist|certificate")
WARD = r"(?:(?:वडा|वार्ड|ward)\s*(?:नं|नम्बर|न|no|number)?\.?\s*[-\u2013]?\s*[0-9०-९]{1,2}|\s?[-\u2013]\s?[0-9०-९]{1,2})(?![0-9०-९])"
WARD_AT = re.compile(rf"(?i){WARD}")
# What may stand between two places of one address.
JOINT = re.compile(rf"(?i)(?:[\s,]|जिल्ला|जिला|district|{WARD})*")
LIVES_AFTER = re.compile(r"(?i)[\s,]*(?:(?:स्थित|मा|में)\s+)?(?:बस्ने|बसोबास\s+गर्ने|निवासी|घर\s+भएक|स्थायी\s+घर|के\s+रहने\s+वाल|basne|niwasi|nivasi|"
                         r"(?:का|की|को|के)\s+[0-9०-९]{1,3}\s*(?:वर्ष|बर्ष|साल))")
# "of" after the places: with a person's name right behind it the places say where that person is from.
OF = re.compile(r"\s*(?:का|की|को|के)\s+")
LIVES_BEFORE = re.compile(r"(?i)(?:resident\s+of|residing\s+(?:at|in)|resides\s+(?:at|in)|lives\s+(?:at|in)|living\s+(?:at|in)|\br/o|"
                          r"स्थायी\s+ठेगाना|स्थायी\s+पता|sthayi\s+thegana)\W{0,6}$")


# A number that is already masked: stars or dots in a row, or X in a row in a value that has no other letter.
STARS = re.compile(r"[*\u2022\u25cf]{2,}")
CROSSES = re.compile(r"[Xx]{2,}")
OTHER_LETTER = re.compile(r"[A-WYZa-wyz\u0904-\u0939\u0958-\u0961\u0972-\u097f]")
# The labels under which a value may stand masked: numbers, and the e-mail address. A password may hold two stars.
MASKABLE = ("PHONE", "EMAIL", "NATIONAL_ID", "TAX_ID", "PASSPORT", "DRIVER_LICENSE", "VOTER_ID", "MEDICAL_ID", "EMPLOYEE_STUDENT_ID",
            "PROPERTY_UTILITY_ID", "ID_NUMBER", "BANK_ACCOUNT", "CREDIT_CARD", "PAYMENT_ID", "VEHICLE_ID")


def masked(value):
    """Whether a number or an e-mail address is written with a part of it masked ("XXXX XXXX 4521", "98******12", "ra****@...")."""
    if STARS.search(value):
        return True
    return bool(CROSSES.search(value)) and not OTHER_LETTER.search(value)


def nearest_cue(text, start, cues=None):
    """The nearest word before a span that names a kind, as (where it starts, the kind); None without one."""
    base = max(0, start - 48)
    before = text[base:start].lower()
    best = None
    for label, words in (cues or CUES).items():
        for cue in words:
            at = before.rfind(cue)
            # A cue in Latin letters counts at the start of a word only: "ration" is not in "registration".
            while at > 0 and cue[0].isascii() and before[at - 1].isascii() and before[at - 1].isalpha():
                at = before.rfind(cue, 0, at)
            if at >= 0 and (best is None or at > best[0]):
                best = (at, label)
    return (base + best[0], best[1]) if best else None


def kind_by_cue(text, start):
    """The final label of a number of several kinds, from the nearest word before it that names a kind; None without one."""
    found = nearest_cue(text, start)
    return found[1] if found else None


def enough(value):
    """Whether a date has at least two of day, month and year."""
    return len(FIGURES.findall(value)) + bool(MONTH_NAME.search(value)) >= 2


def word_like(ch):
    """A Latin letter, a figure or an underscore: what must not stand against a Latin word for birth."""
    return ch.isascii() and (ch.isalnum() or ch == "_")


def birth_cue(text, start):
    """The last word for birth in the 48 characters before `start`, as the place where it ends; None without one."""
    base = max(0, start - 48)
    window = text[base:start]
    found = None
    for m in BIRTH.finditer(window):
        a, b = base + m.start(), base + m.end()
        if m.lastgroup == "word":
            if (a > 0 and word_like(text[a - 1])) or (b < start and word_like(text[b])):
                continue
            b += b < start and text[b] == "."   # "D.O.B."
        elif m.lastgroup == "stem" and b < start and "\u0900" <= text[b] <= "\u097f":
            continue
        found = b
    return found


def of_birth(text, start, end, others=()):
    """Whether the date at [start, end) is given as a date of birth. `others` are the other spans of the text."""
    if not enough(text[start:end]):
        return False
    if BORN_AFTER.match(text[end:end + 30]):
        return True
    cue = birth_cue(text, start)
    if cue is None:
        return False
    gap = text[cue:start]
    between = [label for s, e, label in others if cue <= s < start]
    # A place may stand between ("born in Dharan on ..."); another date or a number makes this one something else,
    # and so do more words than name the date ("the date of birth be corrected, filed on ...").
    if len(gap) > (40 if between else 24) or any(ch in gap for ch in SENTENCE_END) or NOT_BIRTH.search(gap):
        return False
    return all(label == "LOCATION" for label in between)


def homes(text, spans):
    """Stretches of places that the text gives as where a person lives, with a part below the city: (start, end, spans inside)."""
    places = [span for span in spans if span[2] == "LOCATION"]
    taken = {(s, e) for s, e, _ in spans}
    out, k = [], 0
    while k < len(places):
        chain = [places[k]]
        while k + 1 < len(places):
            gap = text[chain[-1][1]:places[k + 1][0]]
            between = any(chain[-1][1] <= s < places[k + 1][0] for s, e in taken)
            if len(gap) > 24 or between or not JOINT.fullmatch(gap):
                break
            k += 1
            chain.append(places[k])
        k += 1
        start, end = chain[0][0], chain[-1][1]
        ward = WARD_AT.match(text, end)
        if ward:
            end = ward.end()
        below = ward is not None or len(chain) > 1
        of = OF.match(text, end)
        named = of is not None and any(s == of.end() and label == "PERSON" for s, e, label in spans)
        # "residing in" before two places may be a list of countries; with a figure among them it is an address.
        before = LIVES_BEFORE.search(text, max(0, start - 30), start) and any(ch.isdigit() for ch in text[start:end])
        if below and (named or before or LIVES_AFTER.match(text, end, end + 40)):
            out.append((start, end, chain))
    return out


def final(text, spans):
    """Spans as they leave the code: under the final names, a number under its kind and a date of birth as one where the words beside it tell."""
    return [(start, end, canonical(label)) for start, end, label in retype(text, spans, leave_homes=True)[0]]


def personal(text, spans):
    """What the profile "personal" gives out of the spans of a model and the rules.

    Personal data only: no place, organisation, date or web address. The phone number and the mailbox that a model
    of 1.0 marks as an office's are left alone, and so is a number that is already masked.
    """
    return [span for span in final(text, [span for span in spans if span[2] not in OFFICE])
            if span[2] in PERSONAL and not (span[2] in MASKABLE and masked(text[span[0]:span[1]]))]


def retype(text, spans, leave_homes=False):
    """The spans of a row labelled before 1.0 as a model of 1.0 learns from them, and how many of each change were made.

    With `leave_homes` the places where a person lives stay as they are: what a model or a rule marked is not
    taken back.
    """
    # Whose a phone number or a mailbox is, where a row or a model says it, stays said.
    spans = sorted((s, e, said(label)) for s, e, label in spans)
    counts = {}
    out = []
    for start, end, label in spans:
        new = label
        if label == "ID_NUMBER":
            cue = nearest_cue(text, start, {**CUES, "DIGITAL_SECRET": DEVICE})
            if MAC.fullmatch(text, start, end):
                new = "DIGITAL_SECRET"
            elif cue and not any(ch in text[cue[0]:start] for ch in SENTENCE_END):
                new = cue[1]
        elif label == "DATE" and of_birth(text, start, end, [o for o in spans if o[0] != start]):
            new = "DOB"
        if new != label:
            counts[new] = counts.get(new, 0) + 1
        out.append((start, end, new))
    for start, end, chain in ([] if leave_homes else homes(text, out)):
        inside = {(s, e) for s, e, _ in chain}
        out = [span for span in out if (span[0], span[1]) not in inside and not (start <= span[0] and span[1] <= end)]
        out.append((start, end, "?"))
        counts["?"] = counts.get("?", 0) + 1
    return sorted(out), counts


def tables():
    """What the Rust build needs to give the answers of `final` and `personal`: the words, the patterns and the labels."""
    from .spans import FINER, WHOLE

    from .labels import OWN

    # The words in the order in which they are tried: of two that begin at one place the first is taken.
    return {"cues": [[label, list(words)] for label, words in {**CUES, "DIGITAL_SECRET": DEVICE}.items()], "own": list(OWN),
            "mac": MAC.pattern, "sentence_end": SENTENCE_END, "figures": FIGURES.pattern, "month": MONTH_NAME.pattern,
            "birth": BIRTH.pattern, "born_after": BORN_AFTER.pattern, "not_birth": NOT_BIRTH.pattern,
            "stars": STARS.pattern, "crosses": CROSSES.pattern, "other_letter": OTHER_LETTER.pattern, "maskable": list(MASKABLE),
            "aliases": dict(ALIASES), "office": list(OFFICE), "personal": list(PERSONAL),
            "finer": {label: list(of) for label, of in FINER.items()}, "whole": {label: list(of) for label, of in WHOLE.items()}}


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True, metavar="FILE", help="write the tables for the Rust build")
    args = ap.parse_args()
    with open(args.export, "w", encoding="utf-8") as fh:
        json.dump(tables(), fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("wrote", args.export)
