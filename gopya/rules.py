"""Rule-based recognizers for identifiers as they are written in Nepal.

Every pattern stays inside the syntax shared by Python `re` and the Rust `regex` crate: no
look-around and no back-references, and digits are written [0-9]. What look-around would
have checked is checked in code. `python -m gopya.rules --export wasm/rules.json` writes the
patterns to the file the Rust build in `wasm/` reads, so the two cannot drift apart.

Numbers whose shape alone says nothing (citizenship, PAN, account numbers) are reported
only when a keyword for that identifier stands shortly before them. The sources for each
format, and which formats are not verified against an official document, are listed in
`docs/identifiers.md`.
"""
import argparse
import json
import re
from pathlib import Path

DIGITS = "०१२३४५६७८९"
HYPHENS = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"
SPACES = "\u00a0\u2007\u202f"
_MARKS = dict.fromkeys(map(ord, HYPHENS), "-")
_MARKS.update(dict.fromkeys(map(ord, SPACES), " "))
_FOLD = {ord(d): str(i) for i, d in enumerate(DIGITS)}
_FOLD.update(_MARKS)


def fold(text):
    """Latin digits, ASCII hyphens and plain spaces. Every character keeps its offset."""
    return text.translate(_FOLD)


def fold_marks(text):
    """ASCII hyphens and plain spaces, with the digits left as they are written."""
    return text.translate(_MARKS)


# "number" as it follows a keyword: नम्बर, नं., no., #
NUM = r"(?:नम्बर|नंबर|नम्वर|नं[.॰]?|न[.॰]|number|num\.?|no\.?|nambar|namber|#)"
KO = r"(?:\s*को|\s*ko)?"

KEYWORDS = {
    "CITIZENSHIP_NO": (
        [rf"नागरिकता(?:\s*प्रमाण\s*पत्र)?{KO}\s*\(?\s*{NUM}",
         r"ना\.?\s*प्र\.?\s*(?:प\.?\s*)?नं[.॰]?",
         rf"naga?rika?ta(?:\s*praman\s*patra)?{KO}\s*{NUM}",
         rf"citizenship(?:\s*certificate)?\s*{NUM}", rf"ctzn?\s*{NUM}"],
        [r"नागरिकता", r"naga?rika?ta", r"citizenship"]),
    "NATIONAL_ID": (
        [rf"राष्ट्रिय\s*परिचय\s*पत्र{KO}\s*{NUM}", r"रा\.?\s*प\.?\s*नं[.॰]?",
         rf"rastriya\s*parichaya?\s*patra{KO}\s*{NUM}",
         rf"national\s*id(?:entity)?(?:\s*card)?\s*{NUM}", rf"ni[nd]\s*{NUM}"],
        [r"nin", r"nid", r"national\s*id", r"राष्ट्रिय\s*परिचय\s*पत्र"]),
    "PAN": (
        [rf"(?:पान|प्यान)\s*{NUM}", rf"स्थायी\s*लेखा\s*{NUM}", rf"(?:भ्याट|मू\.?\s*अ\.?\s*कर\s*दर्ता)\s*{NUM}",
         rf"pan(?:\s*card)?\s*{NUM}", rf"vat\s*{NUM}"],
        [r"pan", r"vat"]),
    "PASSPORT_NO": (
        [rf"(?:राहदानी|पासपोर्ट){KO}\s*{NUM}", rf"(?:passport|rahadani){KO}\s*{NUM}"],
        [r"passport", r"राहदानी", r"पासपोर्ट"]),
    "LICENSE_NO": (
        [rf"(?:सवारी\s*)?चालक\s*अनुमति\s*पत्र{KO}\s*{NUM}", rf"ला[इई]सेन्स{KO}\s*{NUM}",
         rf"(?:driving\s*)?licen[sc]e{KO}\s*{NUM}", rf"(?:laisens|lisence|dl)\s*{NUM}"],
        [r"licen[sc]e", r"ला[इई]सेन्स"]),
    "VOTER_ID": (
        [rf"मतदाता(?:\s*परिचय\s*पत्र)?{KO}\s*{NUM}", rf"mat[a]?data{KO}\s*{NUM}",
         rf"voter(?:'s)?(?:\s*id)?(?:\s*card)?\s*{NUM}"],
        [r"voter\s*id"]),
    "BANK_ACCOUNT": (
        [rf"(?:बैंक\s*)?खाता{KO}\s*{NUM}", rf"khata{KO}\s*{NUM}",
         rf"(?:bank\s*)?(?:account|acc(?:t|ount)?|a/c|ac)\s*{NUM}"],
        [r"a/c", r"account", r"खाता"]),
}

VALUES = {
    "CITIZENSHIP_NO": r"[0-9]{1,8}(?:[-/][0-9]{1,8}){0,4}",
    "NATIONAL_ID": r"[0-9]{3}[- ]?[0-9]{3}[- ]?[0-9]{3}[- ]?[0-9]",
    "PAN": r"[0-9]{9}",
    "PASSPORT_NO": r"[a-z]{1,2}[0-9]{6,8}|[0-9]{7,9}",
    "LICENSE_NO": r"[0-9]{2}-[0-9]{2,3}-[0-9]{6,8}|[0-9]{10,12}",
    "VOTER_ID": r"[0-9]{6,12}",
    "BANK_ACCOUNT": r"[0-9](?:-?[0-9]){8,19}",
}

PHONE_KEYWORDS = [
    rf"(?:फोन|टेलिफोन|मोबाइल|मोबाईल|सम्पर्क)(?:\s*{NUM})?", r"(?:मो|टे|फो)\.?\s*नं[.॰]?",
    rf"(?:phone|mobile|mob|cell|tel|telephone|contact|whatsapp|viber|sampark)(?:\s*{NUM})?",
]
DATE_KEYWORDS = [r"जन्म\s*मित[िी]", r"जन्ममित[िी]", r"मित[िी]", r"date\s*of\s*birth", r"d\.?o\.?b\.?",
                 r"janma\s*miti", r"miti", r"date"]

BS_MONTH = ("बैशाख|बैसाख|वैशाख|वैसाख|जेठ|जेष्ठ|ज्येष्ठ|असार|आषाढ|अषाढ|साउन|श्रावण|सावन|भदौ|भाद्र|असोज|"
            "आश्विन|अश्विन|कात्तिक|कार्तिक|मंसिर|मंसीर|मङ्सिर|मङ्सीर|पुष|पुस|पौष|माघ|फागुन|फाल्गुन|चैत्र|चैत")
AD_MONTH = ("जनवरी|फेब्रुअरी|फेब्रुवरी|मार्च|अप्रिल|अप्रील|जुलाई|अगस्ट|अगष्ट|अगस्त|सेप्टेम्बर|सेप्टेम्वर|"
            "अक्टोबर|अक्टोवर|नोभेम्बर|नोभेम्वर|डिसेम्बर|डिसेम्वर")
# जुन, मे and मार्ग are also ordinary words, so they count as months only next to a year.
LOOSE_MONTH = "जुन|मे|मार्ग"
LATIN_MONTH = ("january|february|march|april|june|july|august|september|october|november|december|"
               "jan|feb|mar|apr|may|jun|jul|aug|sept|sep|oct|nov|dec|"
               "baishakh|baisakh|jestha|jeth|ashadh|ashad|asar|shrawan|sawan|saun|bhadra|bhadau|"
               "ashwin|ashoj|asoj|kartik|mangshir|mangsir|poush|push|magh|falgun|fagun|phagun|"
               "chaitra|chait")
NAMED = rf"(?:{BS_MONTH}|{AD_MONTH}|{LATIN_MONTH})"
MONTH = rf"(?:{BS_MONTH}|{AD_MONTH}|{LOOSE_MONTH}|{LATIN_MONTH})"
ERA = r"(?:(?:[वब]ि\.?\s*सं?\.?|[वब]िक्रम\s*सम्वत्?|सन्|ई\.?\s*सं\.?|b\.?s\.?|a\.?d\.?)\s*)"
TH = r"(?:st|nd|rd|th)?"

ZONE = "मे|को|स|ज|बा|ना|ग|लु|ध|रा|भे|क|से|म"
CLASS = "क|च|प|ख|ज|फ|ग|झ|ब|घ|ञ|य"
ZONE_LATIN = "bhe|dha|me|ko|sa|ja|ba|na|ga|lu|ra|ka|se|ma"
CLASS_LATIN = "kha|cha|pha|jha|gha|nya|ka|pa|ja|fa|ga|ba|ya"
PROVINCE = "कोशी|मधेश|बागमती|गण्डकी|लुम्बिनी|कर्णाली|सुदूरपश्चिम|सुदुरपश्चिम"
PROVINCE_LATIN = "koshi|madhesh|bagmati|gandaki|lumbini|karnali|sudurpashchim|sudurpaschim"

AFTER_YEAR = re.compile(r"\s*साल")   # a number before साल is a year, not a citizenship number
MOBILE_PREFIX = re.compile(r"9(?:6[0-3]|7[0-24-6]|8[0-24-68])")
FIXED_LINE = re.compile(r"(?:1[0-6][0-9]|99[02-6])[0-9]{5}|"
                        r"(?:2[13-79]|3[135-8]|4[146-9]|5[135-7]|6[13-9]|7[15-9]|8[1-46-9]|9[1-7])[2-6][0-9]{5}")


def _gated(keywords, value, gap):
    return re.compile(r"(?i)(?:^|[^a-z])(?P<kw>" + "|".join(keywords) + r")(?P<gap>" + gap +
                      r")(?P<val>" + value + r")")


FAR = r"(?:[^0-9a-z।\n?!][^0-9।\n?!]{0,40}?)?"   # up to a short clause, no digit and no sentence end
NEAR = r"[\s:=#.\-)\]]{0,4}"

STRONG = {lab: _gated(kw[0], VALUES[lab], FAR) for lab, kw in KEYWORDS.items()}
WEAK = {lab: _gated(kw[1], VALUES[lab], NEAR) for lab, kw in KEYWORDS.items()}
ANY_KEYWORD = re.compile(r"(?i)(?:" + "|".join(k for kw in KEYWORDS.values() for k in kw[0]) + r")")
PHONE_GATED = _gated(PHONE_KEYWORDS, r"\+?[0-9](?:[- ]?[0-9]){6,13}", FAR)

MOBILE = re.compile(r"(?P<cc>(?:\+|00)?977[- ]?)?(?P<n>9[678][0-9](?:[- ]?[0-9]){7})")
LANDLINE_INTL = re.compile(r"(?:\+|00)977[- ]?(?P<area>[0-9]{1,2})[- ]?(?P<rest>[0-9]{6,7})")
LANDLINE = re.compile(r"0(?P<area>[0-9]{1,2})[- ](?P<rest>[0-9]{6,7})")
# The last part of the address is in one case, or capitalised. Text copied from a web page can run
# the next label on to an address ("...comPhone"); the address then ends before "Phone".
EMAIL = re.compile(r"(?i:[a-z0-9][a-z0-9._%+-]*@[a-z0-9-]+(?:\.[a-z0-9-]+)*)\.(?:[A-Z][a-z]+|[a-z]{2,}|[A-Z]{2,})")
LICENSE_SHAPE = re.compile(r"[0-9]{2}-[0-9]{2}-[0-9]{8}")

NUMERIC_DATES = [
    (re.compile(r"(?P<y>[0-9]{4})(?P<s1>[-/.])(?P<a>[0-9]{1,2})(?P<s2>[-/.])(?P<b>[0-9]{1,2})"), "ymd"),
    (re.compile(r"(?P<a>[0-9]{1,2})(?P<s1>[-/.])(?P<b>[0-9]{1,2})(?P<s2>[-/.])(?P<y>[0-9]{4})"), "dmy"),
]
DATE_GATED = _gated(DATE_KEYWORDS, r"[0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4}", FAR)
WORD_DATES = [
    re.compile(rf"(?i){ERA}?(?P<y>[0-9]{{4}})\s*(?:साल\s*)?{MONTH}\s*(?:महिना(?:को)?\s*)?(?P<d>[0-9]{{1,2}})"),
    re.compile(rf"(?i){ERA}?(?P<y>[0-9]{{4}})\s*(?:साल\s*)?{NAMED}"),
    re.compile(rf"(?i){MONTH}\s*(?P<d>[0-9]{{1,2}}){TH}(?:\s*(?:गते|तारिख))?\s*,?\s*(?P<y>[0-9]{{4}})"),
    re.compile(rf"(?i)(?P<d>[0-9]{{1,2}}){TH}\s*{MONTH}\s*,?\s*(?P<y>[0-9]{{4}})"),
    re.compile(rf"(?i){NAMED}\s*,?\s*(?P<y>[0-9]{{4}})"),
    re.compile(rf"(?:{BS_MONTH}|{AD_MONTH})\s*(?P<d>[0-9]{{1,2}})"),
    re.compile(rf"(?i){ERA}(?P<y>[0-9]{{4}})(?:\s*साल)?"),
    re.compile(r"(?P<y>[0-9]{4})\s*साल"),
]
# A day before its month and no year, as in a dateline: "२६ कात्तिक, काठमाडौं". The month must
# end its word or carry only case markers, or "५ पुस्तक" (five books) would be a date in पुस.
DAY_MONTH = re.compile(rf"(?P<d>[0-9]{{1,2}})\s*(?:{BS_MONTH}|{AD_MONTH})")
MONTH_SUFFIX = re.compile(r"(?:मा|को|का|की|देखि|सम्म|बाट|लाई|मै|कै|भित्र|अघि|पछि|तिर)+")

PLATES = [
    re.compile(rf"(?:{ZONE})\.?\s?[0-9]{{1,2}}\s?(?:{CLASS})\.?\s?[0-9]{{1,4}}"),
    re.compile(rf"(?i)(?:{ZONE_LATIN})\.?\s?[0-9]{{1,2}}\s?(?:{CLASS_LATIN})\.?\s?[0-9]{{1,4}}"),
    re.compile(rf"(?:(?:{PROVINCE})\s*प्रदेश|प्रदेश\s*(?:नं\.?\s*)?[1-7]|(?:बा|को|म|ग|लु|क|सु)\.\s?प्र\.)"
               rf"\s*-?\s*[0-9]{{2}}\s*-\s*[0-9]{{3}}\s*(?:{CLASS})\.?\s?[0-9]{{1,4}}"),
    re.compile(rf"(?i)(?:{PROVINCE_LATIN})\s+[a-k][0-9]?\s+[a-z]{{2}}\s+[0-9]{{1,4}}"),
]


def _digit(ch):
    """A Latin digit. The text has been folded, so Devanagari digits count too."""
    return "0" <= ch <= "9"


def _digits(value):
    return sum(_digit(ch) for ch in value)


def _letter(ch):
    """A Latin letter."""
    return "a" <= ch.lower() <= "z" and ch.isascii()


def _alone(text, start, end):
    """True when the number at [start, end) is not a piece of a longer number."""
    before = text[start - 1] if start else " "
    after = text[end] if end < len(text) else " "
    if _digit(before) or _digit(after):
        return False
    if after in "-/" and end + 1 < len(text) and _digit(text[end + 1]):
        return False
    if before in "-/" and start > 1 and _digit(text[start - 2]):
        return False
    return True


def _word_start(text, start, latin):
    """True when the match does not begin inside a word of its own script."""
    if not start:
        return True
    before = text[start - 1]
    return not _letter(before) if latin else not "\u0900" <= before <= "\u097f"


def _rest_of_word(text, end):
    """The Devanagari letters and signs that follow position `end` without a break."""
    stop = end
    while stop < len(text) and "\u0900" <= text[stop] <= "\u097f" and text[stop] not in "।॥":
        stop += 1
    return text[end:stop]


def _plausible_date(year, a, b, order):
    """Year 1900 to 2099 covers both calendars; a Bikram Sambat month can have 32 days.

    A date that starts with the year is year-month-day. One that ends with the year may be
    day-month or month-day.
    """
    month_first = 1 <= a <= 12 and 1 <= b <= 32
    return 1900 <= year <= 2099 and (month_first or (order == "dmy" and 1 <= b <= 12 and 1 <= a <= 32))


def _ids(text):
    for strong, table in ((True, STRONG), (False, WEAK)):
        for label, pattern in table.items():
            for m in pattern.finditer(text):
                value, gap = m.group("val"), m.group("gap")
                start, end = m.span("val")
                if not _alone(text, start, end) or ANY_KEYWORD.search(gap):
                    continue
                if label == "CITIZENSHIP_NO":
                    if not (5 if not strong else 4) <= _digits(value) <= 17:
                        continue
                    if not strong and AFTER_YEAR.match(text[end:end + 5]):
                        continue
                if end < len(text) and _letter(text[end]):
                    continue
                yield start, end, label, (0 if strong else 1, len(gap))


def _phones(text):
    for m in MOBILE.finditer(text):
        number = m.group("n")
        start = m.start("cc") if m.group("cc") else m.start("n")
        if (_alone(text, start, m.end()) and MOBILE_PREFIX.match(number)
                and len(number) - _digits(number) <= 3 and not (start and text[start - 1] == "+")):
            yield start, m.end(), "PHONE", (2, 0)
    for pattern in (LANDLINE_INTL, LANDLINE):
        for m in pattern.finditer(text):
            if _alone(text, m.start(), m.end()) and FIXED_LINE.fullmatch(m.group("area") + m.group("rest")):
                yield m.start(), m.end(), "PHONE", (2, 0)
    for m in PHONE_GATED.finditer(text):
        start, end = m.span("val")
        if _alone(text, start, end) and not ANY_KEYWORD.search(m.group("gap")):
            yield start, end, "PHONE", (2, len(m.group("gap")))


def _dates(text):
    for pattern, order in NUMERIC_DATES:
        for m in pattern.finditer(text):
            if (m.group("s1") == m.group("s2") and _alone(text, m.start(), m.end())
                    and _plausible_date(int(m.group("y")), int(m.group("a")), int(m.group("b")), order)):
                yield m.start(), m.end(), "DATE", (4, 0)
    for m in DATE_GATED.finditer(text):
        start, end = m.span("val")
        if _alone(text, start, end):
            yield start, end, "DATE", (3, len(m.group("gap")))
    for pattern in WORD_DATES:
        for m in pattern.finditer(text):
            groups = m.groupdict()
            year = int(groups.get("y") or 2000)
            day = int(groups.get("d") or 1)
            first = text[m.start()]
            after = text[m.end()] if m.end() < len(text) else " "
            if (1900 <= year <= 2099 and 1 <= day <= 32 and _alone(text, m.start(), m.end())
                    and _word_start(text, m.start(), first.isascii())
                    and not _letter(after)):
                yield m.start(), m.end(), "DATE", (4, 0)
    for m in DAY_MONTH.finditer(text):
        rest = _rest_of_word(text, m.end())
        if (1 <= int(m.group("d")) <= 32 and _alone(text, m.start(), m.end())
                and (not rest or MONTH_SUFFIX.fullmatch(rest))):
            yield m.start(), m.end(), "DATE", (4, 0)


def _others(text, marks):
    """`marks` is the text with its digits unfolded: a Devanagari digit is never part of an address,
    so a phone number in Devanagari digits written against one stays outside it."""
    for m in EMAIL.finditer(marks):
        yield m.start(), m.end(), "EMAIL", (2, 0)
    for m in LICENSE_SHAPE.finditer(text):
        if _alone(text, m.start(), m.end()):
            yield m.start(), m.end(), "LICENSE_NO", (3, 0)
    for i, pattern in enumerate(PLATES):
        for m in pattern.finditer(text):
            if _alone(text, m.start(), m.end()) and _word_start(text, m.start(), latin=i in (1, 3)):
                yield m.start(), m.end(), "VEHICLE_PLATE", (2, 0)


def find(text):
    """Return the identifiers in `text` as sorted, non-overlapping (start, end, label).

    Where candidates overlap, a number named by a keyword wins over one recognised by shape,
    the nearer keyword wins over the farther, and then the longer match wins.
    """
    folded = fold(text)
    found = []
    for finder in (_ids, _phones, _dates):
        found.extend(finder(folded))
    found.extend(_others(folded, fold_marks(text)))
    found.sort(key=lambda c: (c[3], c[0] - c[1], c[0]))
    taken = []
    for start, end, label, _ in found:
        if all(end <= s or e <= start for s, e, _ in taken):
            taken.append((start, end, label))
    return sorted(taken)


def tables():
    """The patterns as text, in the order they are tried, for the Rust build in `wasm/`."""
    return {
        "fold": {"digits": DIGITS, "hyphens": HYPHENS, "spaces": SPACES},
        "strong": [[label, pattern.pattern] for label, pattern in STRONG.items()],
        "weak": [[label, pattern.pattern] for label, pattern in WEAK.items()],
        "any_keyword": ANY_KEYWORD.pattern,
        "after_year": AFTER_YEAR.pattern,
        "phone_gated": PHONE_GATED.pattern,
        "mobile": MOBILE.pattern,
        "mobile_prefix": MOBILE_PREFIX.pattern,
        "fixed_line": FIXED_LINE.pattern,
        "landline_intl": LANDLINE_INTL.pattern,
        "landline": LANDLINE.pattern,
        "email": EMAIL.pattern,
        "license_shape": LICENSE_SHAPE.pattern,
        "numeric_dates": [[pattern.pattern, order] for pattern, order in NUMERIC_DATES],
        "date_gated": DATE_GATED.pattern,
        "word_dates": [pattern.pattern for pattern in WORD_DATES],
        "day_month": DAY_MONTH.pattern,
        "month_suffix": MONTH_SUFFIX.pattern,
        "plates": [pattern.pattern for pattern in PLATES],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True, help="file to write the patterns to, such as wasm/rules.json")
    args = ap.parse_args()
    Path(args.export).write_text(json.dumps(tables(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", args.export)


if __name__ == "__main__":
    main()
