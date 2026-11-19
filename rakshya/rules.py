"""Rule-based recognizers for identifiers as they are written in Nepal, in India and on the web.

Every pattern stays inside the syntax shared by Python `re` and the Rust `regex` crate: no
look-around and no back-references, and digits are written [0-9]. What look-around would
have checked is checked in code. `python -m rakshya.rules --export wasm/rules.json` writes the
patterns to the file the Rust build in `wasm/` reads, so the two cannot drift apart.

Numbers whose shape alone says nothing (citizenship, tax and account numbers) are reported
only when a keyword for that identifier stands shortly before them. Numbers that carry a
check digit (payment cards, IBAN, Aadhaar) and strings with a fixed form (addresses on the
web, keys of known services) are reported by shape. The sources for each format, and which
formats are not verified against an official document, are listed in `docs/identifiers.md`.
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

ID = r"(?:id|आईडी|आइडी)"
CODE = rf"(?:\s*(?:{ID}|code|संकेत))?\s*{NUM}|\s*(?:{ID}|code)"   # "... no.", "... id", "... code", "... id no."

# label, keywords that reach across a short clause, keywords that must stand against the number, the number
GATED = [
    ("CITIZENSHIP_NO",
     [rf"नागरिकता(?:\s*प्रमाण\s*पत्र)?{KO}\s*\(?\s*{NUM}",
      r"ना\.?\s*प्र\.?\s*(?:प\.?\s*)?नं[.॰]?",
      rf"naga?rika?ta(?:\s*praman\s*patra)?{KO}\s*{NUM}",
      rf"citizenship(?:\s*certificate)?\s*{NUM}", rf"ctzn?\s*{NUM}"],
     [r"नागरिकता", r"naga?rika?ta", r"citizenship"],
     r"[0-9]{1,8}(?:[-/][0-9]{1,8}){0,4}"),
    ("NATIONAL_ID",
     [rf"राष्ट्रिय\s*परिचय\s*पत्र{KO}\s*{NUM}", r"रा\.?\s*प\.?\s*नं[.॰]?",
      rf"rastriya\s*parichaya?\s*patra{KO}\s*{NUM}",
      rf"national\s*id(?:entity)?(?:\s*card)?\s*{NUM}", rf"ni[nd]\s*{NUM}"],
     [r"nin", r"nid", r"national\s*id", r"राष्ट्रिय\s*परिचय\s*पत्र"],
     r"[0-9]{3}[- ]?[0-9]{3}[- ]?[0-9]{3}[- ]?[0-9]"),
    ("NATIONAL_ID",   # Aadhaar, also with its first eight digits masked
     [rf"aa?dha?ar(?:\s*card)?(?:\s*{NUM})?", rf"आधार(?:\s*कार्ड)?(?:\s*(?:{NUM}|संख्या))?", rf"uid(?:ai)?(?:\s*{NUM})?"],
     [],
     r"[0-9x*]{4}[- ]?[0-9x*]{4}[- ]?[0-9]{4}"),
    ("NATIONAL_ID",   # United States social security number
     [rf"(?:ssn|social\s*security)(?:\s*{NUM})?"],
     [],
     r"[0-9x*]{3}[- ]?[0-9x*]{2}[- ]?[0-9]{4}"),
    ("TAX_ID",
     [rf"(?:पान|प्यान)\s*{NUM}", rf"स्थायी\s*लेखा\s*{NUM}", rf"(?:भ्याट|मू\.?\s*अ\.?\s*कर\s*दर्ता)\s*{NUM}",
      rf"pan(?:\s*card)?\s*{NUM}", rf"vat\s*{NUM}"],
     [r"pan", r"vat"],
     r"[0-9]{9}"),
    ("TAX_ID",        # the Indian PAN: five letters, four digits, one letter
     [rf"pan(?:\s*card)?(?:\s*{NUM})?", rf"पैन(?:\s*कार्ड)?(?:\s*(?:{NUM}|संख्या))?"],
     [],
     r"[a-z]{5} ?[0-9]{4} ?[a-z]"),
    ("TAX_ID",        # the Indian GSTIN
     [rf"gst(?:in)?(?:\s*{NUM})?", rf"जीएसटी(?:\s*{NUM})?"],
     [],
     r"[0-9]{2}[a-z]{5}[0-9]{4}[a-z][0-9a-z]z[0-9a-z]"),
    ("TAX_ID",        # employer and taxpayer numbers of the United States
     [rf"(?:ein|tin|tax(?:payer)?\s*id(?:entification)?)(?:\s*{NUM})?"],
     [],
     r"[0-9]{2}-?[0-9]{7}"),
    ("PASSPORT_NO",
     [rf"(?:राहदानी|पासपोर्ट){KO}\s*{NUM}", rf"(?:passport|rahadani){KO}\s*{NUM}"],
     [r"passport", r"राहदानी", r"पासपोर्ट"],
     r"[a-z]{1,2}[0-9]{6,8}|[0-9]{7,9}"),
    ("LICENSE_NO",
     [rf"(?:सवारी\s*)?चालक\s*अनुमति\s*पत्र{KO}\s*{NUM}", rf"ला[इई]सेन्स{KO}\s*{NUM}",
      rf"(?:driving\s*)?licen[sc]e{KO}\s*{NUM}", rf"(?:laisens|lisence|dl)\s*{NUM}"],
     [r"licen[sc]e", r"ला[इई]सेन्स"],
     r"[0-9]{2}-[0-9]{2,3}-[0-9]{6,8}|[0-9]{10,12}"),
    ("LICENSE_NO",    # India: state, office, year and serial; elsewhere a letter or two before the digits
     [rf"(?:driving\s*|driver'?s\s*)?licen[sc]e(?:\s*{NUM})?", rf"dl\s*{NUM}", rf"ड्राइविंग\s*लाइसेंस(?:\s*(?:{NUM}|संख्या))?"],
     [],
     r"[a-z]{2}[- ]?[0-9]{2}[- ]?[0-9]{4}[- ]?[0-9]{7}|[a-z]{1,2}[0-9]{6,14}"),
    ("VOTER_ID",
     [rf"मतदाता(?:\s*परिचय\s*पत्र)?{KO}\s*{NUM}", rf"mat[a]?data{KO}\s*{NUM}",
      rf"voter(?:'s)?(?:\s*id)?(?:\s*card)?\s*{NUM}"],
     [r"voter\s*id"],
     r"[0-9]{6,12}"),
    ("VOTER_ID",      # the Indian elector's photo identity card
     [rf"(?:epic|voter(?:'s)?\s*id(?:\s*card)?|मतदाता\s*पहचान\s*पत्र)(?:\s*(?:{NUM}|संख्या))?"],
     [],
     r"[a-z]{3}[0-9]{7}"),
    ("BANK_ACCOUNT",
     [rf"(?:बैंक\s*)?खाता{KO}\s*(?:{NUM}|संख्या)", rf"khata{KO}\s*{NUM}",
      rf"(?:bank\s*)?(?:account|acc(?:t|ount)?|a/c|ac)\s*{NUM}"],
     [r"a/c", r"account", r"खाता"],
     r"[0-9](?:-?[0-9]){6,19}"),
    ("CARD_NUMBER",   # a card named as one, also masked or with a wrong check digit
     [rf"(?:credit|debit|atm|visa|master|payment|क्रेडिट|डेबिट|एटीएम)\s*(?:card|कार्ड)(?:\s*(?:{NUM}|संख्या))?",
      rf"(?:card|कार्ड)\s*(?:{NUM}|संख्या)"],
     [],
     r"[0-9x*]{4}(?:[- ]?[0-9x*]{2,6}){2,4}"),
    ("UPI_ID",
     [rf"(?:upi|vpa|यूपीआई|युपिआई)(?:\s*{ID})?", rf"(?:gpay|google\s*pay|phonepe|paytm|bhim)(?:\s*(?:upi|{ID}))?"],
     [],
     r"[a-z0-9][a-z0-9._-]{1,63}@[a-z][a-z0-9]{1,30}"),
    ("SECRET",        # a code sent to confirm a payment or a sign-in, named just before it
     [],
     [rf"(?:otp|ओटीपी|one[- ]?time\s*(?:password|passcode|code|pin)|verification\s*code|login\s*code)"
      rf"(?:\s*(?:code|कोड|{NUM}))?(?:\s+for\s+[a-z]+)?"],
     r"[0-9]{4,8}"),
    ("SECRET",
     [],
     [r"m-?pin", r"t-?pin", r"atm\s*pin", r"cvv2?", r"cvc2?", r"security\s*code"],
     r"[0-9]{3,6}"),
    ("SECRET",        # "PIN" before six digits is a postal code in India, so only four count
     [],
     [r"pin", r"पिन"],
     r"[0-9]{4}"),
    ("ID_NUMBER",     # numbers an employer, a school, a hospital, an insurer or a seller gives a person
     [],
     [rf"(?:employee|emp|staff|कर्मचारी)(?:{CODE})", rf"(?:student|विद्यार्थी|छात्र)(?:{CODE})",
      rf"(?:roll|रोल|symbol|सिम्बोल|enrol?lment|registration|reg\.?|रजिष्ट्रेसन)\s*{NUM}",
      rf"(?:customer|client|consumer|subscriber|member(?:ship)?|ग्राहक|सदस्यता)(?:{CODE})",
      rf"(?:patient|बिरामी)(?:{CODE})", rf"(?:mrn|medical\s*record)(?:\s*{NUM})?",
      rf"(?:policy|बीमालेख|insurance)(?:{CODE})", rf"imei(?:\s*{NUM})?"],
     # A full stop joins two groups of figures: the customer number of the electricity authority is "021.08.319kha".
     r"(?:[a-z]{1,8}[-/]?){0,3}[0-9](?:[-/]?[a-z0-9]|\.[0-9]){2,22}"),
]

PHONE_KEYWORDS = [
    rf"(?:फोन|फ़ोन|टेलिफोन|मोबाइल|मोबाईल|सम्पर्क|संपर्क|दूरभाष|टोल\s*फ्र[ीि]|नोटिस\s*बोर्ड)(?:\s*{NUM})?", r"(?:मो|टे|फो)\.?\s*नं[.॰]?",
    rf"(?:phone|mobile|mob|cell|tel|telephone|contact|whatsapp|viber|sampark|fax|toll[\s-]*free|notice\s*board)(?:\s*{NUM})?",
]
DATE_KEYWORDS = [r"जन्म\s*मित[िी]", r"जन्ममित[िी]", r"मित[िी]", r"जन्म\s*तिथि", r"जन्मतिथि", r"दिनांक", r"तारीख",
                 r"date\s*of\s*birth", r"d\.?o\.?b\.?", r"janma\s*miti", r"miti", r"date"]

BS_MONTH = ("बैशाख|बैसाख|वैशाख|वैसाख|जेठ|जेष्ठ|ज्येष्ठ|असार|आषाढ|अषाढ|साउन|श्रावण|सावन|भदौ|भाद्र|असोज|"
            "आश्विन|अश्विन|कात्तिक|कार्तिक|मंसिर|मंसीर|मङ्सिर|मङ्सीर|पुष|पुस|पौष|माघ|फागुन|फाल्गुन|चैत्र|चैत")
AD_MONTH = ("जनवरी|फेब्रुअरी|फेब्रुवरी|मार्च|अप्रिल|अप्रील|जुलाई|अगस्ट|अगष्ट|अगस्त|सेप्टेम्बर|सेप्टेम्वर|"
            "अक्टोबर|अक्टोवर|नोभेम्बर|नोभेम्वर|डिसेम्बर|डिसेम्वर|"
            "फरवरी|फ़रवरी|अप्रैल|सितंबर|सितम्बर|अक्टूबर|अक्तूबर|नवंबर|नवम्बर|दिसंबर|दिसम्बर")
# जुन, मे and मार्ग (and मई and जून in Hindi) are also ordinary words, so they count as months only next to a year.
LOOSE_MONTH = "जुन|जून|मे|मई|मार्ग"
ENGLISH_MONTH = ("January|February|March|April|May|June|July|August|September|October|November|December|"
                 "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec")
LATIN_MONTH = ("january|february|march|april|june|july|august|september|october|november|december|"
               "jan|feb|mar|apr|may|jun|jul|aug|sept|sep|oct|nov|dec|"
               "baishakh|baisakh|jestha|jeth|ashadh|ashad|asar|shrawan|sawan|saun|bhadra|bhadau|"
               "ashwin|ashoj|asoj|kartik|mangshir|mangsir|poush|push|magh|falgun|fagun|phagun|"
               "chaitra|chait")
NAMED = rf"(?:{BS_MONTH}|{AD_MONTH}|{LATIN_MONTH})"
MONTH = rf"(?:{BS_MONTH}|{AD_MONTH}|{LOOSE_MONTH}|{LATIN_MONTH})"
# The space inside a date is never a line break: a page gives each line a block of its own, and a day at the end
# of one line with a year at the start of the next are two cells ("१८ असार" above "२०८०").
SP = r"[^\S\n\r]"
# The word for the era is part of the date (docs/annotation.md). The ones in Devanagari may also stand before a date
# in figures or one that starts with the day; "ad" and "bs" before those would be the end of a word ("road 12 March 2020").
ERA_WORD = rf"(?:[वब]ि\.?{SP}*सं?\.?|(?:(?:[वब]िक्रम|शक){SP}*)?(?:सम्[वब]त्?|संवत्?)|सन्|ई\.?{SP}*सं\.?)"
ERA_BEFORE = rf"(?:{ERA_WORD}{SP}*)"
ERA = rf"(?:(?:{ERA_WORD}|b\.?s\.?|a\.?d\.?){SP}*)"
# The era after a date in Latin letters: "9th Baisakh, 2083 B.S". Without its full stops it is in capitals,
# or "the March 5, 2020 ad" would be a date with its era.
ERA_AFTER = re.compile(rf"{SP}*(?:[Bb]\.[Ss]\.?|[Aa]\.[Dd]\.?|BS|AD)")
# The era at the end of what stands between a keyword and a date: "मिति वि.सं. २०६८/०४/१६".
ERA_END = re.compile(rf"{ERA_WORD}{SP}*$")
# The time of day that a page prints after the date of a post. What stands against its minutes starts a cell of its
# own: "Post date04/16/2024 - 12:24२०८० बैशाख १ गतेदेखि".
TIME = re.compile(r"[0-9]{1,2}:[0-9]{2}")
# A year before the word for a decade is not a date: "सन् १९९० को दशकमा".
DECADE = re.compile(rf"{SP}*(?:को|का|के){SP}*दशक")
TH = r"(?:st|nd|rd|th)?"
# In news the year of the Bikram era is also written with its last three figures: "०८० साउन १२".
YEAR = r"(?P<y>[0-9]{4}|0[5-9][0-9])"

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
# A full stop after a word of four letters or more and before a capital ends a sentence ("below. Page 12");
# after "Mr", "Dr" or "Prof" it does not.
SENTENCE_BREAK = re.compile(r"[a-z]{4}\.\s+[A-Z]")
SYMBOL = re.compile(r"(?i)symbol|सिम्बोल")
NEAR = r"(?:\s+is\s+|[\s:=#.\-)\]]{0,4})"   # against the number, or joined to it by "is"

STRONG = [(label, _gated(far, value, FAR)) for label, far, _, value in GATED if far]
WEAK = [(label, _gated(near, value, NEAR)) for label, _, near, value in GATED if near]
# A keyword of another identifier between a keyword and a number breaks the link between the two. Only a
# keyword that ends in a word for "number" counts: in "citizenship no. and PAN, mine are 49-07-62-14085
# and 630154836" the bare "PAN" does not stop the first number from being the citizenship number.
ANY_KEYWORD = re.compile(r"(?i)(?:^|[^a-z])(?:" + "|".join(
    k for _, far, _, _ in GATED for k in far if k.endswith((NUM, "नं[.॰]?"))) + r")(?:$|[^a-z])")
# A plus sign written before a number is part of it, also with a space between the two: "+ 977-1-4412345".
PHONE_GATED = _gated(PHONE_KEYWORDS, r"(?:\+ ?)?[0-9](?:[- ]?[0-9]){6,13}", FAR)

# The country code may stand in brackets, with the plus inside or before them, and a hyphen with a space may follow
# it: "(+977) 01-4412345", "+(977) 061-520123", "+977- 9841234567". After it the area code is often written with the
# zero it has inside the country, or in brackets: "+977 01 4412345", "+977-(021)-520123". Before a landline the bare
# code needs a hyphen or a space after it ("977-1-4412345"): eleven figures in a row that begin with 977 may be
# any number.
MARKED = r"(?:\+ ?\(977\)|\((?:\+|00)?977\)|(?:\+ ?|00)977)"
CODE_977 = rf"(?:{MARKED}[- ]{{0,3}}|977[- ]{{1,3}})"
JOIN = r"(?: ?- ?| )"   # between the area code and the number: a hyphen, a space, or a hyphen with a space beside it
MOBILE = re.compile(rf"(?P<cc>(?:{MARKED}|977)[- ]{{0,3}})?(?P<n>9[678][0-9](?:[- ]?[0-9]){{7}})")
LANDLINES = [
    re.compile(rf"{CODE_977}0?(?P<area>[0-9]{{1,2}}){JOIN}?(?P<rest>[0-9]{{6,7}})"),
    re.compile(rf"{CODE_977}\(0?(?P<area>[0-9]{{1,2}})\)[- ]{{0,3}}(?P<rest>[0-9]{{6,7}})"),
    # Inside the country: "01-4412345", "01- 4412345", "(061) 520123", and with a plus that a page puts before it.
    re.compile(rf"\+?0(?P<area>[0-9]{{1,2}}){JOIN}(?P<rest>[0-9]{{6,7}})"),
    re.compile(r"\+?\(0(?P<area>[0-9]{1,2})\)[- ]{0,3}(?P<rest>[0-9]{6,7})"),
]
# The last part of the address is in one case, or capitalised. Text copied from a web page can run
# the next label on to an address ("...comPhone"); the address then ends before "Phone".
# The part before the "@" may hold Latin letters with their marks ("lucía.márquez@"): without them the address
# began in the middle of the name. Letters of other scripts stay outside, since a page runs a Devanagari word
# against an address more often than an address begins with one.
EMAIL = re.compile(r"(?i:[a-z0-9À-ÖØ-öø-ɏ][a-z0-9À-ÖØ-öø-ɏ._%+-]*@[a-z0-9-]+(?:\.[a-z0-9-]+)*)\.(?:[A-Z][a-z]+|[a-z]{2,}|[A-Z]{2,})")
# A phone number written against the address that follows it: "9841234567ram.thapa@example.com".
# One more number in a list of phone numbers: "4412345, 4412346 / 4412347".
NEXT_PHONE = re.compile(r"\s*[,/|]\s*(?P<n>[0-9]{6,10})")
GLUED_PHONE = re.compile(r"(?i)(?P<n>(?:977-?)?9[678][0-9](?:-?[0-9]){7}|0[0-9]{1,2}-[0-9]{6,7})[a-z]")
LICENSE_SHAPE = re.compile(r"[0-9]{2}-[0-9]{2}-[0-9]{8}")

NUMERIC_DATES = [
    (re.compile(rf"{ERA_BEFORE}?(?P<y>[0-9]{{4}})(?P<s1>[-/.])(?P<a>[0-9]{{1,2}})(?P<s2>[-/.])(?P<b>[0-9]{{1,2}})"), "ymd"),
    (re.compile(r"(?P<a>[0-9]{1,2})(?P<s1>[-/.])(?P<b>[0-9]{1,2})(?P<s2>[-/.])(?P<y>[0-9]{4})"), "dmy"),
]
DATE_GATED = _gated(DATE_KEYWORDS, r"[0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4}", FAR)
# A date as a table prints it: the year, then month and day with two digits each. Text taken from a web page runs
# the cells of a table together, so the next cell may stand against the date: "2079-05-262079-05-26", "2077-04-2207 जेष्ठ".
# The year in a copyright line, and the second year where the line gives two: "© 2026", "Copyright © 1967 - 2026",
# "© Example School, 2024", "प्रतिलिपि अधिकार २०२६".
COPYRIGHT = re.compile(r"(?i)(?:©|copyright|प्रतिलिपि\s*अधिकार)(?P<gap>[^0-9\n।?!]{0,45}?)(?P<val>(?:19|20)[0-9]{2})"
                       r"(?:\s*-\s*(?P<to>(?:19|20)[0-9]{2}))?")
WHOLE_DATE = re.compile(r"(?P<y>(?:19|20)[0-9]{2})(?P<s1>[-/.])(?:0[1-9]|1[0-2])(?P<s2>[-/.])(?:0[1-9]|[12][0-9]|3[0-2])")
WORD_DATES = [
    # After the year a comma may stand ("२०८३, वैशाख १७"), and after the day in a date that starts with it ("12, Feb 2026").
    re.compile(rf"(?i){ERA}?{YEAR},?{SP}*(?:साल{SP}*)?{MONTH}{SP}*(?:महिना(?:को)?{SP}*)?(?P<d>[0-9]{{1,2}})"),
    re.compile(rf"(?i){ERA}?(?P<y>[0-9]{{4}}){SP}*(?:साल{SP}*)?(?P<m>{NAMED})"),
    re.compile(rf"(?i){MONTH}{SP}*(?P<d>[0-9]{{1,2}}){TH}(?:{SP}*(?:गते|तारिख))?{SP}*,?{SP}*{YEAR}"),
    re.compile(rf"(?i){ERA_BEFORE}?(?P<d>[0-9]{{1,2}}){TH},?{SP}*(?:of{SP}+)?{MONTH}{SP}*,?{SP}*{YEAR}"),
    # मे, मई and जून before a year are months. जुन is not taken: "जुन २०१७ को तुलनामा" says "which, compared to 2017".
    re.compile(rf"(?i)(?:{NAMED}|मे|मई|जून){SP}*,?{SP}*(?P<y>[0-9]{{4}})"),
    re.compile(rf"(?:{BS_MONTH}|{AD_MONTH}){SP}*(?P<d>[0-9]{{1,2}})"),
    re.compile(rf"(?i){ERA}(?P<y>[0-9]{{4}})(?:{SP}*साल)?"),
    re.compile(rf"(?P<y>[0-9]{{4}}){SP}*साल"),
    # The end of a month, with or without its year: "असोज मसान्त", "२०८१ चैत्र मसान्त".
    re.compile(rf"(?:{ERA}?(?P<y>[0-9]{{4}}){SP}*(?:साल{SP}*)?)?(?:{BS_MONTH}){SP}*मसान्त"),
    # An English month with a capital and a day, without a year: "March 5", "5th of March".
    re.compile(rf"(?:{ENGLISH_MONTH})\.?{SP}(?P<d>[0-9]{{1,2}}){TH}"),
    re.compile(rf"(?P<d>[0-9]{{1,2}}){TH}{SP}(?:of{SP})?(?:{ENGLISH_MONTH})"),
]
# A day before its month and no year, as in a dateline: "२६ कात्तिक, काठमाडौं". The month must
# end its word or carry only case markers, or "५ पुस्तक" (five books) would be a date in पुस.
DAY_MONTH = re.compile(rf"(?P<d>[0-9]{{1,2}}){SP}*(?:{BS_MONTH}|{AD_MONTH})")
MONTH_SUFFIX = re.compile(r"(?:मा|को|का|की|देखि|सम्म|बाट|लाई|मै|कै|भित्र|अघि|पछि|तिर)+")

PLATES = [
    # A plate is written on one line: a list of clauses ("२ क", "२ ख", "३") must not read as one.
    re.compile(rf"(?:{ZONE})\.? ?[0-9]{{1,2}} ?(?:{CLASS})\.? ?[0-9]{{1,4}}"),
    re.compile(rf"(?i)(?:{ZONE_LATIN})\.? ?[0-9]{{1,2}} ?(?:{CLASS_LATIN})\.? ?[0-9]{{1,4}}"),
    re.compile(rf"(?:(?:{PROVINCE}) *प्रदेश|प्रदेश *(?:नं\.? *)?[1-7]|(?:बा|को|म|ग|लु|क|सु)\. ?प्र\.)"
               rf" *-? *[0-9]{{2}} *- *[0-9]{{3}} *(?:{CLASS})\.? ?[0-9]{{1,4}}"),
    re.compile(rf"(?i)(?:{PROVINCE_LATIN}) +[a-k][0-9]? +[a-z]{{2}} +[0-9]{{1,4}}"),
]


def _longest_first(names):
    """An alternation that tries a longer name before a name it starts with."""
    return "|".join(sorted(names.split("|"), key=len, reverse=True))


# Payment cards are written in one piece or in the groups printed on the card.
CARD = re.compile(r"[0-9]{4} [0-9]{4} [0-9]{4} [0-9]{4}(?: [0-9]{3})?|[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}(?:-[0-9]{3})?|"
                  r"[0-9]{4} [0-9]{6} [0-9]{5}|[0-9]{4}-[0-9]{6}-[0-9]{5}|[0-9]{13,19}")
IBAN = re.compile(r"[A-Z]{2}[0-9]{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?")
IPV4 = re.compile(r"[0-9]{1,3}(?:\.[0-9]{1,3}){3}")
IPV6 = re.compile(r"(?i)(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}|(?:[0-9a-f]{1,4}:){1,7}:(?:[0-9a-f]{1,4}(?::[0-9a-f]{1,4}){0,6})?|"
                  r"::(?:[0-9a-f]{1,4}:){0,6}[0-9a-f]{1,4}")
# Words before four numbers with dots that make them a section or a version, not an address.
NOT_IP = re.compile(r"(?i)[^a-z](?:version|ver|v|build|release|firmware|kernel|patch|section|sec|clause|article|chapter|table|figure|fig|"
                    r"संस्करण|दफा|धारा|उपदफा|बुँदा|अनुसूची|तालिका|खण्ड|परिच्छेद)[\s.:#-]*$")
MAC = re.compile(r"(?i)[0-9a-f]{2}(?::[0-9a-f]{2}){5}|[0-9a-f]{2}(?:-[0-9a-f]{2}){5}")
SSN = re.compile(r"(?P<a>[0-9]{3})-(?P<g>[0-9]{2})-(?P<s>[0-9]{4})")
INDIA_STATE = "AN|AP|AR|AS|BR|CG|CH|DD|DL|DN|GA|GJ|HP|HR|JH|JK|KA|KL|LA|LD|MH|ML|MN|MP|MZ|NL|OD|OR|PB|PY|RJ|SK|TG|TN|TR|TS|UA|UK|UP|WB"
INDIA_PAN = re.compile(r"[A-Z]{3}[ABCFGHJLPT][A-Z][0-9]{4}[A-Z]")
GSTIN = re.compile(r"[0-3][0-9][A-Z]{3}[ABCFGHJLPT][A-Z][0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]")
INDIA_PLATE = re.compile(rf"(?:{INDIA_STATE})[- ]?[0-9]{{1,2}}(?:[A-Z][- ])?[- ]?[A-Z]{{1,3}}[- ]?[0-9]{{4}}")
INDIA_LICENSE = re.compile(rf"(?:{INDIA_STATE})[- ]?[0-9]{{2}}[- ]?(?:19|20)[0-9]{{2}}[- ]?[0-9]{{7}}")
INDIA_MOBILE = re.compile(r"(?:\+|00)91[- ]?[6-9][0-9]{4}[- ]?[0-9]{5}")
# A number that starts with "+" and a country code, and numbers written the North American way.
# Lines that cost the caller nothing and the notice boards of offices: 1660-01-55555, 1618-01-4200327.
TOLL_FREE = re.compile(r"1660[- ]?0[1-9][- ]?[0-9]{5}|1618[- ]0[0-9]{1,2}[- ][0-9]{6,7}")
# A card number printed with most of its digits hidden: "XXXX XXXX XXXX 4821", "4111 11** **** 1111".
MASKED_CARD = re.compile(r"(?:[Xx*•]{4}[- ]?){3}[0-9]{4}|[0-9]{4}[- ]?[0-9]{2}[Xx*•]{2}[- ]?[Xx*•]{4}[- ]?[0-9]{4}")
PLUS_PHONE = re.compile(r"\+[1-9][0-9]{0,2}(?:[- .]?\(?[0-9]{1,5}\)?){1,6}")
US_PHONE = re.compile(r"(?:\+?1[- .]?)?(?:\([2-9][0-9]{2}\) ?|[2-9][0-9]{2}[- .])[2-9][0-9]{2}[- .][0-9]{4}")

# Addresses on the web. One written with "http" or "www" is taken as it stands. One written without
# counts in three cases, because people leave out the space after a full stop ("ramro xa.bt", "end.In")
# and program text is full of names with dots ("user.name", "member.email"):
#   * it ends in one of the old generic domains (CORE_TLD);
#   * it ends in a country code under a second-level name such as "gov" or "co" (moha.gov.np, sbi.co.in);
#   * a path follows it (t.me/name, bit.ly/3mDxeHC).
URL_CHAR = r"[a-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]"
CORE_TLD = "com|org|net|edu|gov|mil|int"
SECOND_LEVEL = "com|org|net|edu|gov|mil|co|ac|nic|res|name|info"
PATH_TLD = (CORE_TLD + "|np|in|uk|us|au|ca|de|fr|jp|cn|ru|br|bd|pk|lk|bt|sg|hk|nz|za|ae|ch|nl|se|es|eu|"
            "me|ly|be|io|ai|app|dev|co|gg|tv|cc|to|xyz|info|biz|link|page|site|online|store|shop|blog|news")
HOST = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
URL = re.compile(rf"(?i)(?:https?://|ftp://|www\.){URL_CHAR}+")
DOMAIN = re.compile(rf"(?i){HOST}(?:\.{HOST}){{0,4}}\.(?:(?:{SECOND_LEVEL})\.[a-z]{{2}}|{CORE_TLD})(?:[/?#]{URL_CHAR}*)?")
PATH_DOMAIN = re.compile(rf"(?i){HOST}(?:\.{HOST}){{0,4}}\.(?:{_longest_first(PATH_TLD)})/{URL_CHAR}+")
HANDLE = re.compile(r"@[A-Za-z0-9_](?:[A-Za-z0-9_.]{0,28}[A-Za-z0-9_])?")
CLOCK = re.compile(r"(?i)[0-9]{1,2}(?:[:.][0-9]{2})?(?:am|pm)")   # "@11am" is a time
UPI_HANDLES = ("okaxis|oksbi|okhdfcbank|okicici|okbizaxis|ybl|ibl|axl|paytm|ptyes|ptaxis|ptsbi|pthdfc|upi|apl|yapl|rapl|"
               "sbi|hdfcbank|icici|axisbank|axis|kotak|barodampay|pnb|cnrb|unionbank|uboi|idbi|indus|federal|yesbank|"
               "yesbankltd|jupiteraxis|fbl|freecharge|airtel|jio|postbank|aubank|dbs|hsbc|citi|citigold|rbl|idfcbank|"
               "idfcfirst|idfc|bandhan|kvb|tmb|dlb|mahb|boi|cbin|cboi|uco|iob|indianbank|indbank|psb|jkb|kbl|ikwik|mbk|"
               "slice|superyes|naviaxis|timecosmos|tapicici|waaxis|wahdfcbank|wasbi|waicici|pingpay|abfspay|equitas|sib|"
               "csbpay|dcb|nsdl|pockets|myicici|imobile|ratn|utbi|vijb|allbank|andb|barb|centralbank|obc|syndicate")
UPI = re.compile(rf"(?i)[a-z0-9][a-z0-9._-]{{1,63}}@(?:{_longest_first(UPI_HANDLES)})")
# Keys and tokens that say what they are by how they start.
TOKEN = re.compile("|".join([
    r"(?:AKIA|ASIA)[0-9A-Z]{16}",                                   # Amazon Web Services access key
    r"gh[pousr]_[A-Za-z0-9]{36,255}", r"github_pat_[A-Za-z0-9_]{22,255}", r"glpat-[A-Za-z0-9_-]{20,64}",
    r"sk-[A-Za-z0-9_-]{20,255}", r"(?:sk|pk|rk)_(?:live|test)_[0-9A-Za-z]{16,255}",
    r"xox[abeprs]-[A-Za-z0-9-]{10,255}", r"AIza[0-9A-Za-z_-]{35}", r"ya29\.[0-9A-Za-z_-]{20,255}",
    r"hf_[A-Za-z0-9]{30,64}", r"npm_[A-Za-z0-9]{36}", r"SG\.[A-Za-z0-9_-]{16,32}\.[A-Za-z0-9_-]{16,64}",
    r"[0-9]{8,10}:AA[A-Za-z0-9_-]{33}",                             # Telegram bot
    r"eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}",  # JSON web token
    r"-----BEGIN [A-Z ]{0,30}PRIVATE KEY-----[\s\S]*?-----END [A-Z ]{0,30}PRIVATE KEY-----",
]))
BEARER = re.compile(r"(?:^|[^A-Za-z])[Bb]earer\s+(?P<val>[A-Za-z0-9._~+/=-]{16,})")
SECRET_GATED = re.compile(
    r"(?i)(?:^|[^a-z])(?P<kw>password|passwd|pwd|passcode|पासवर्ड|पासवोर्ड|secret(?:[ _-]?key)?|api[ _-]?key|apikey|"
    r"access[ _-]?(?:key|token)|auth(?:orization)?[ _-]?token|client[ _-]?secret|token)"
    r"(?P<gap>\s*[:=]\s*|\s+is\s*:?\s+)(?P<val>\"[^\"\n]{3,80}\"|'[^'\n]{3,80}'|[^\s\"'<>]{3,80})")
# What follows "password:" in a sentence about passwords and is not one.
NOT_SECRET = re.compile(r"(?i)(?:required|incorrect|invalid|expired|wrong|reset|changed|missing|empty|null|none|nil|true|false|"
                        r"string|optional|hidden|redacted|unknown|your|the|not|and|for|n/a|[*x.•-]+|<[^>]*>?|\[[^\]]*\]?|\{[^}]*\}?)")
OTP_BEFORE = re.compile(r"(?i)(?P<val>[0-9]{4,8})\s+is\s+(?:your|the)\s+(?:otp|one[- ]?time|verification|login|security)")
# "user:" and "login:" open a line of a chat or a log more often than they name an account, so alone
# they count only before "=".
USERNAME_GATED = re.compile(
    r"(?i)(?:^|[^a-z])(?P<kw>(?:user\s*name|username|user\s*id|userid|uname|login\s*id|युजरनेम|यूजरनेम|प्रयोगकर्ता\s*नाम)"
    r"(?P<gap>\s*[:=]\s*)|(?:user|usr|login)=)(?P<val>@?[a-z0-9_][a-z0-9._-]{2,63})")
SOCIAL_GATED = re.compile(
    r"(?i)(?:^|[^a-z])(?P<kw>instagram|insta|ig|twitter|telegram|tiktok|snapchat|discord|github|skype|facebook|fb)"
    r"(?:\s*(?:id|handle|username))?(?P<gap>\s*[:=]\s*)(?P<val>@?[a-z0-9_][a-z0-9._-]{2,31})")

# label, name of the check in CHECKS, rank among overlapping candidates, pattern
SHAPES = [
    ("PHONE", "plus_phone", 2, PLUS_PHONE),
    ("PHONE", "number", 3, INDIA_MOBILE),
    ("PHONE", "number", 3, TOLL_FREE),
]
# These run on the text with its digits unfolded, like the e-mail pattern. None of them is written with
# Devanagari digits, and tables of amounts and section numbers in Devanagari digits ("५७२७ ५६१५ ५५१९ ४३२१",
# "४.२.३.१२") must not be read as a card or an address. Twelve digits in three groups are not reported
# as an Aadhaar number without its keyword either: one such run in ten passes the check by chance.
MARK_SHAPES = [
    ("CARD_NUMBER", "card", 2, CARD),
    ("CARD_NUMBER", "word", 3, MASKED_CARD),
    ("URL", "url", 0, URL),
    ("URL", "domain", 2, DOMAIN),
    ("URL", "path_domain", 2, PATH_DOMAIN),
    ("USERNAME", "handle", 2, HANDLE),
    ("UPI_ID", "upi", 2, UPI),
    ("SECRET", "key", 2, TOKEN),
    ("BANK_ACCOUNT", "iban", 2, IBAN),
    ("IP_ADDRESS", "ipv4", 2, IPV4),
    ("IP_ADDRESS", "ipv6", 2, IPV6),
    ("PHONE", "number", 3, US_PHONE),
    ("NATIONAL_ID", "ssn", 3, SSN),
    ("TAX_ID", "word", 3, GSTIN),
    ("TAX_ID", "word", 3, INDIA_PAN),
    ("VEHICLE_PLATE", "word", 3, INDIA_PLATE),
    ("LICENSE_NO", "word", 3, INDIA_LICENSE),
    ("ID_NUMBER", "mac", 3, MAC),
]


def _digit(ch):
    """A Latin digit. The text has been folded, so Devanagari digits count too."""
    return "0" <= ch <= "9"


def _digits(value):
    return sum(_digit(ch) for ch in value)


def _letter(ch):
    """A Latin letter."""
    return "a" <= ch.lower() <= "z" and ch.isascii()


def _alone(text, start, end, cells=(), listed=False):
    """True when the number at [start, end) is not a piece of a longer number.

    `cells` are positions where a cell of a table ends: what starts there starts a number of its own. With
    `listed` a slash and a digit may follow: after a phone number a slash brings the next number of a list, or
    the endings of further numbers ("4412345/46/47").
    """
    before = text[start - 1] if start and start not in cells else " "
    after = text[end] if end < len(text) else " "
    if _digit(before) or _digit(after):
        return False
    if after in ("-" if listed else "-/") and end + 1 < len(text) and _digit(text[end + 1]):
        return False
    if before in "-/" and start > 1 and _digit(text[start - 2]):
        return False
    return True


def _next_cell(text, end):
    """True when the digits against the end of a date are the next cell of a table and not the rest of a longer number.

    The next cell is another whole date, a day or another small number (one or two digits), or a year (four digits
    that begin with 19 or 20). "2080-05-0123-45" is the number of a letter and "2023-10-123456" that of an order.
    """
    stop = end
    while stop < len(text) and _digit(text[stop]):
        stop += 1
    if text[stop:stop + 1] in ("-", "/") and _digit(text[stop + 1:stop + 2] or " "):
        m = WHOLE_DATE.match(text, end)
        return bool(m and m.group("s1") == m.group("s2"))
    return stop - end <= 2 or (stop - end == 4 and text[end:end + 2] in ("19", "20"))


def _whole_dates(text):
    """Dates written year-month-day that stand against a neighbouring cell of a table, and where every such date ends.

    Returns (dates, cells): the dates as (start, end) that the other date rules would pass over, because digits
    stand against them, and the positions where a whole date ends. What starts at such a position starts a cell of
    its own. A date with a hyphen or a slash and more digits on either side is a piece of a longer number.
    """
    out, cells = [], set()
    for m in WHOLE_DATE.finditer(text):
        start, end = m.span()
        before = text[start - 1] if start and start not in cells else " "
        after = text[end] if end < len(text) else " "
        if (m.group("s1") != m.group("s2") or _digit(before)
                or (before in "-/" and start > 1 and _digit(text[start - 2]))
                or (after in "-/" and end + 1 < len(text) and _digit(text[end + 1]))
                or (_digit(after) and not _next_cell(text, end))):
            continue
        if _digit(after) or start in cells:
            out.append((start, end))
        cells.add(end)
    return out, cells


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
        for label, pattern in table:
            for m in pattern.finditer(text):
                value, gap = m.group("val"), m.group("gap")
                start, end = m.span("val")
                if not _alone(text, start, end) or ANY_KEYWORD.search(gap) or SENTENCE_BREAK.search(gap):
                    continue
                if gap and _letter(gap[-1]):
                    continue   # the end of a longer token: "TXN7576964714"
                if label == "CITIZENSHIP_NO":
                    if not (5 if not strong else 4) <= _digits(value) <= 17:
                        continue
                    if not strong and AFTER_YEAR.match(text[end:end + 5]):
                        continue
                if end < len(text) and _letter(text[end]):
                    continue
                if label == "ID_NUMBER":
                    # Capitals written against the number are its first part, not a keyword: "MRN4416013", "MRN-0220BBC08A".
                    keyword = m.group("kw")
                    if gap in ("", "-") and len(keyword) <= 4 and keyword.isascii() and keyword.isupper() and keyword.isalpha():
                        start = m.start("kw")
                    # A word written against the number ("236345Section") is not part of it.
                    stop = end
                    while stop > start and _letter(text[stop - 1]):
                        stop -= 1
                    if end - stop >= 3 and any(ch.islower() for ch in text[stop:end]):
                        end = stop
                    while end > start and text[end - 1] in "-/":
                        end -= 1
                    if _digits(text[start:end]) < 3:
                        continue
                    # The letter after the symbol number of an examination belongs to it: "0234567 B".
                    if SYMBOL.match(m.group("kw")) and text[end:end + 1] == " " and "A" <= text[end + 1:end + 2] <= "Z" \
                            and not _wordy(text[end + 2:end + 3] or " "):
                        end += 2
                    # The one Devanagari letter that ends a number written in groups with full stops belongs to it:
                    # "०२१.०८.३१९ख", also with a case marker against it ("...३१९खको"). A word written against the
                    # number does not ("...३१९को").
                    if "." in text[start:end] and "क" <= text[end:end + 1] <= "ह" and _ends_word(text, end + 1):
                        end += 1
                if label == "SECRET" and text[end:end + 1] == " " and _digit(text[end + 1:end + 2] or " "):
                    continue   # the first group of a longer number
                if label == "CARD_NUMBER" and not (_digits(value) >= 4 and 12 <= sum(c not in "- " for c in value) <= 19):
                    continue
                if label == "UPI_ID" and text[end:end + 1] in (".", "-") and _letter(text[end + 1:end + 2] or " "):
                    continue   # the start of an e-mail address
                yield start, end, label, (0 if strong else 1, len(gap))


def _phones(text):
    found = list(_single_phones(text))
    yield from found
    # A bare number of six to ten digits after a phone number and a comma, a slash or a bar is one more of the list.
    ends = [end for _, end, _, _ in found]
    k = 0
    while k < len(ends):
        m = NEXT_PHONE.match(text, ends[k])
        if m:
            start, end = m.span("n")
            after = text[end] if end < len(text) else " "
            if not (_digit(after) or _letter(after) or (after == "-" and _digit(text[end + 1:end + 2] or " "))) and end not in ends:
                yield start, end, "PHONE", (2, 0)
                ends.append(end)
        k += 1


def _single_phones(text):
    for m in MOBILE.finditer(text):
        number = m.group("n")
        start = m.start("cc") if m.group("cc") else m.start("n")
        if (_alone(text, start, m.end(), listed=True) and MOBILE_PREFIX.match(number)
                and len(number) - _digits(number) <= 3 and not (start and text[start - 1] == "+")):
            yield start, m.end(), "PHONE", (2, 0)
    for pattern in LANDLINES:
        for m in pattern.finditer(text):
            if _alone(text, m.start(), m.end(), listed=True) and FIXED_LINE.fullmatch(m.group("area") + m.group("rest")):
                yield m.start(), m.end(), "PHONE", (2, 0)
    for m in PHONE_GATED.finditer(text):
        start, end = m.span("val")
        if end - start > 3 and text[end - 2] == " " and _digit(text[end - 3]):
            end -= 2   # a single digit after a space is the next cell of a table, not the end of the number
        if m.group("gap") and _letter(m.group("gap")[-1]):
            continue   # the end of a longer token: "TXN7576964714"
        if _alone(text, start, end, listed=True) and not ANY_KEYWORD.search(m.group("gap")):
            yield start, end, "PHONE", (2, len(m.group("gap")))


def _ends(text, end):
    """True when no digit follows position `end`, nor a hyphen or a slash with a digit behind it."""
    after = text[end] if end < len(text) else " "
    return not (_digit(after) or (after in "-/" and end + 1 < len(text) and _digit(text[end + 1])))


def _with_era(text, end):
    """The end of a date with the era that follows it in Latin letters, where that is a word of its own."""
    m = ERA_AFTER.match(text, end)
    after = text[m.end()] if m and m.end() < len(text) else " "
    return m.end() if m and not (_letter(after) or _digit(after)) else end


def _runs_on(text, start, end):
    """True when the letters against the year that ends a date may be the next word of a page that runs its cells
    together ("March 7, 2016by Admin", "April 19, 2026Notice"): the date has a space or a comma inside, so it is no
    code ("MAR2021A"), and what follows is not the "s" of a decade ("2010s")."""
    inside, after = text[start:end], text[end:end + 2]
    return (" " in inside or "," in inside) and not (after[:1] in "sS" and not _letter(after[1:2] or " "))


def _gated_date(value):
    """False for figures after a keyword that are no date as they stand: a year has a day or a month at its other
    end, and "2076-03-1014" is a date with the next cell of a table run on to it."""
    parts = value.replace("/", "-").replace(".", "-").split("-")
    return len(parts[0]) < 3 or len(parts[-1]) < 3


def _dates(text):
    whole, cells = _whole_dates(text)
    for start, end in whole:
        yield start, end, "DATE", (4, 0)
    for m in TIME.finditer(text):
        if not (m.start() and _digit(text[m.start() - 1])):
            cells.add(m.end())
    for m in COPYRIGHT.finditer(text):
        last = "to" if m.group("to") else "val"
        if _ends(text, m.end(last)):
            yield m.start("val"), m.end("val"), "DATE", (4, 0)
            if m.group("to"):
                yield m.start("to"), m.end("to"), "DATE", (4, 0)
    for pattern, order in NUMERIC_DATES:
        for m in pattern.finditer(text):
            if (m.group("s1") == m.group("s2") and _alone(text, m.start(), m.end())
                    and _plausible_date(int(m.group("y")), int(m.group("a")), int(m.group("b")), order)):
                yield m.start(), _with_era(text, m.end()), "DATE", (4, 0)
    for m in DATE_GATED.finditer(text):
        start, end = m.span("val")
        gap = m.group("gap")
        era = ERA_END.search(gap)
        if era:
            start -= len(gap) - era.start()
        if _alone(text, start, end) and _gated_date(text[m.start("val"):end]):
            yield start, end, "DATE", (3, len(gap))
    for pattern in WORD_DATES:
        for m in pattern.finditer(text):
            groups = m.groupdict()
            start, end = m.span()
            short = len(groups.get("y") or "") == 3
            year = int(groups.get("y") or 2000) + (2000 if short else 0)
            day = int(groups.get("d") or 1)
            closes = groups.get("y") is not None and m.end("y") == end   # the year ends the date
            after = text[end] if end < len(text) else " "
            # A date that starts with a word is not the rest of the number before it ("2026April 19, 2026"), and a
            # capital after a small letter starts a word on a page that runs its cells together ("jhapaApril 19").
            own = cells if _digit(text[start]) else {*cells, start}
            capital = start and "A" <= text[start] <= "Z" and "a" <= text[start - 1] <= "z"
            if not (1900 <= year <= 2099 and 1 <= day <= 32 and _alone(text, start, end, own)
                    and (capital or _word_start(text, start, text[start].isascii()))):
                continue
            if _letter(after) and not (closes and _runs_on(text, start, end)):
                continue
            if closes and DECADE.match(text, end):
                continue
            if groups.get("m") and m.end("m") == end:
                # A month that ends the date ends its word or carries only case markers, as after a day: in
                # "२००४ साल भाद्रकृष्ण अष्टमी" the month names a lunar day and the date is the year.
                rest = _rest_of_word(text, end)
                if rest and not MONTH_SUFFIX.fullmatch(rest):
                    continue
            yield start, _with_era(text, end) if closes else end, "DATE", (4, 0)
    for m in DAY_MONTH.finditer(text):
        rest = _rest_of_word(text, m.end())
        if (1 <= int(m.group("d")) <= 32 and _alone(text, m.start(), m.end(), cells)
                and (not rest or MONTH_SUFFIX.fullmatch(rest))):
            yield m.start(), m.end(), "DATE", (4, 0)


def _after_phone(text, start, end):
    """Where an e-mail address starts when a phone number is written against it.

    Text copied from a web page runs the cells of a table together, and the address then
    seems to begin with the number before it ("Phone9841234567ram@example.com"). A mobile
    or a landline number of Nepal followed by a letter, inside the part before the "@", is
    read as that number, and the address starts after it. An address is rarely a phone
    number with a name after it; with the name first ("ram9841234567@") it is left whole.
    """
    at = text.index("@", start, end)
    cut = start
    for m in GLUED_PHONE.finditer(text, start, at):
        number = m.group("n")
        if number[0] == "0":
            valid = FIXED_LINE.fullmatch(number[1:].replace("-", ""))
        else:
            mobile = number[3:].lstrip("-") if number.startswith("977") else number
            valid = MOBILE_PREFIX.match(mobile) and mobile.count("-") <= 1
        before = text[m.start() - 1] if m.start() else " "
        if valid and not _digit(before) and at - m.end("n") >= 2:
            cut = m.end("n")
    return cut


def _others(text, marks):
    """`marks` is the text with its digits unfolded: a Devanagari digit is never part of an address,
    so a phone number in Devanagari digits written against one stays outside it."""
    for m in EMAIL.finditer(marks):
        yield _after_phone(marks, m.start(), m.end()), m.end(), "EMAIL", (2, 0)
    for m in LICENSE_SHAPE.finditer(text):
        if _alone(text, m.start(), m.end()):
            yield m.start(), m.end(), "LICENSE_NO", (3, 0)
    for i, pattern in enumerate(PLATES):
        for m in pattern.finditer(text):
            latin = i in (1, 3)
            if latin and m.end() < len(text) and _letter(text[m.end()]):
                continue   # "ko 20 ka 250ru" is not a plate
            if _alone(text, m.start(), m.end()) and _word_start(text, m.start(), latin=latin):
                yield m.start(), m.end(), "VEHICLE_PLATE", (2, 0)


def _only_digits(value):
    return [ord(ch) - 48 for ch in value if _digit(ch)]


def luhn(value):
    """The check of payment card numbers (ISO/IEC 7812)."""
    total = 0
    for i, d in enumerate(reversed(_only_digits(value))):
        if i % 2:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def iban_valid(value):
    """ISO 13616: move the first four characters to the end, read letters as 10 to 35, and divide by 97."""
    value = value.replace(" ", "")
    if not 15 <= len(value) <= 34:
        return False
    rest = 0
    for ch in value[4:] + value[:4]:
        n = ord(ch) - 48 if _digit(ch) else ord(ch) - 55
        rest = (rest * (10 if n < 10 else 100) + n) % 97
    return rest == 1


def _card_issuer(d):
    """True when the first digits and the count of digits are those of a card network.

    Maestro (50, 56 to 69 with 12 to 19 digits) is too wide to tell from other numbers by
    form; such a card is found when a keyword names it. Fifteen digits that start with 35
    are the number of a phone (IMEI), not a card.
    """
    n, two = len(d), d[0] * 10 + d[1]
    three, four = two * 10 + d[2], two * 100 + d[2] * 10 + d[3]
    if d[0] == 4:
        return n in (13, 16, 19)                                   # Visa
    if 51 <= two <= 55 or 2221 <= four <= 2720:
        return n == 16                                             # Mastercard
    if two in (34, 37):
        return n == 15                                             # American Express
    if two in (36, 38, 39) or 300 <= three <= 305:
        return n in (14, 16)                                       # Diners Club
    if two == 35:
        return 16 <= n <= 19                                       # JCB
    if two in (60, 62, 64, 65, 81, 82) or three == 508:
        return 16 <= n <= 19                                       # Discover, UnionPay, RuPay
    return False


def _wordy(ch):
    """A Latin letter or a digit."""
    return _letter(ch) or _digit(ch)


# Case markers that are written against the word before them, in Nepali and in Hindi.
AFTER_A_WORD = ("को", "का", "की", "के", "ले", "मा", "लाई", "बाट", "सँग", "में", "से", "पर")


def _devanagari(ch):
    """A Devanagari letter or sign."""
    return "\u0900" <= ch <= "\u097f"


def _ends_word(text, at):
    """True when no Devanagari letter or sign stands at `at`, or a case marker does and the word ends after it."""
    if not _devanagari(text[at:at + 1] or " "):
        return True
    return any(text.startswith(marker, at) and not _devanagari(text[at + len(marker):at + len(marker) + 1] or " ")
               for marker in AFTER_A_WORD)


def _apart(text, start, end, also=""):
    """True when no Latin letter, digit or character of `also` touches the range on either side."""
    before = text[start - 1] if start else " "
    after = text[end] if end < len(text) else " "
    return not (_wordy(before) or _wordy(after) or before in also or after in also)


def _check_number(text, start, end):
    return (start, end) if _alone(text, start, end) and _apart(text, start, end, "+") else None


def _check_word(text, start, end):
    return (start, end) if _apart(text, start, end, "-_") else None


def _check_card(text, start, end):
    """A card number in one of its written forms with a valid check digit. When three more digits
    follow the sixteen, the nineteen are tried first and then the sixteen."""
    for stop in (end, end - 4):
        d = _only_digits(text[start:stop])
        if 13 <= len(d) <= 19 and _alone(text, start, stop) and _apart(text, start, stop) and _card_issuer(d) \
                and luhn(text[start:stop]):
            return start, stop
        if not (len(d) == 19 and text[stop - 4] in "- "):
            break
    return None


def _check_iban(text, start, end):
    """The longest run that passes the check. The pattern may have taken in a capital word after the number."""
    if _wordy(text[start - 1] if start else " "):
        return None
    stop = end
    while stop > start + 14:
        if iban_valid(text[start:stop]) and not _wordy(text[stop] if stop < len(text) else " "):
            return start, stop
        stop = text.rfind(" ", start, stop)
    return None


def _check_ipv4(text, start, end):
    parts = text[start:end].split(".")
    before = text[start - 1] if start else " "
    after = text[end] if end < len(text) else " "
    if any(int(part) > 255 or (len(part) > 1 and part[0] == "0") for part in parts):
        return None
    if _wordy(before) or before in "./-" or _wordy(after) or (after in ".-" and _digit(text[end + 1:end + 2] or " ")):
        return None
    if NOT_IP.search(" " + text[max(0, start - 24):start]) or all(int(part) < 10 for part in parts):
        return None   # a version or a section number
    return start, end


def _check_ipv6(text, start, end):
    value = text[start:end]
    groups = [g for g in value.split(":") if g]
    if not _apart(text, start, end, ":.") or len(groups) > 8 or (len(groups) < 8 and "::" not in value):
        return None
    if len(groups) < 2 or not any(_digit(ch) for ch in value):
        return None
    if len(groups) < 3 and not any(_letter(ch) for ch in value):
        return None   # "12::30"
    return start, end


def _check_mac(text, start, end):
    return (start, end) if _apart(text, start, end, ":-") and any(_digit(ch) for ch in text[start:end]) else None


def _check_ssn(text, start, end):
    area, group, serial = text[start:start + 3], text[start + 4:start + 6], text[start + 7:end]
    if area in ("000", "666") or area[0] == "9" or group == "00" or serial == "0000":
        return None
    if int(group) == (int(area) + 1) % 100:
        return None   # a fiscal year of Nepal before a serial number: 078-79-0012
    return (start, end) if _alone(text, start, end) and _apart(text, start, end) else None


# The fewest and the most digits of a number without its country code: where Nepalis live and work,
# the neighbours, and the countries most often written to. A mobile number of Nepal has ten.
NATIONAL = {"977": (8, 10), "91": (10, 10), "1": (10, 10), "44": (9, 10), "61": (9, 9), "971": (8, 9), "974": (8, 8),
            "966": (8, 9), "965": (8, 8), "973": (8, 8), "968": (8, 8), "60": (8, 10), "82": (8, 10), "81": (9, 10),
            "86": (10, 11), "880": (8, 10), "92": (9, 10), "94": (9, 9), "975": (7, 8), "49": (7, 11), "33": (9, 9),
            "65": (8, 8), "852": (8, 8), "66": (8, 9), "972": (8, 9), "351": (9, 9), "48": (9, 9), "40": (9, 9),
            "357": (8, 8), "7": (10, 10)}


def _check_plus_phone(text, start, end):
    """A number that starts with "+" and a country code.

    The pattern takes groups of digits as long as they come, so it may run on into the next
    cell of a table ("+977-9801234567 3 ..."). The match is cut back, group by group, until
    it has no more digits than a number of its country has (fifteen in all for a country
    that is not listed) and does not end in a single digit after a space.
    """
    before = text[start - 1] if start else " "
    if _wordy(before) or before == "+":
        return None
    run = "".join(ch for ch in text[start:end] if _digit(ch))
    code = next((run[:n] for n in (3, 2, 1) if run[:n] in NATIONAL), "")
    low, high = NATIONAL[code] if code else (8, 15)
    if code == "977" and not MOBILE_PREFIX.match(run[3:]):
        high = 8   # a landline: area code and number are eight digits together
    stop = end
    while stop > start:
        value = text[start:stop]
        last = value[-1]
        group_end = (_digit(last) or last == ")") and (stop == end or text[stop] in "- .(")
        count = _digits(value) - len(code)
        if group_end and count < low:
            return None
        stray = len(value) > 2 and value[-2] == " " and _digit(last)
        if group_end and count <= high and not stray and value.count("(") == value.count(")"):
            return start, stop
        stop -= 1
    return None


def _trim_address(value):
    """The length of a web address without the punctuation that ends a sentence or closes a bracket."""
    end = len(value)
    while end:
        ch = value[end - 1]
        if ch in ".,;:!?'*([" or (ch == ")" and value.count("(", 0, end) < value.count(")", 0, end)) \
                or (ch == "]" and value.count("[", 0, end) < value.count("]", 0, end)):
            end -= 1
        else:
            break
    return end


def _host_end(value):
    """Where a label written against the address starts ("...gov.npPhone"), or the length of the address.

    Only an address without a path is cut: its last part is then in one case, like an e-mail address's.
    """
    at = value.find("://")
    rest = value[at + 3:] if at >= 0 else value
    if any(ch in rest for ch in "/?#"):
        return len(value)
    last = value.rfind(".") + 1
    for i in range(last + 2, len(value)):
        if value[i].isupper() and value[i - 1].islower():
            return i
    return len(value)


def _check_url(text, start, end):
    if start and _wordy(text[start - 1]) and text[start:start + 4].lower() == "www.":
        return None   # "http" may be written against the word before it; "www." inside a word is no address
    # A second address may be written against the first, and a page that shortens an address ends it with three dots.
    again = min([i for i in (text.find(word, start + 4, end) for word in ("http://", "https://", "...")) if i > 0] or [end])
    stop = start + _trim_address(text[start:again])
    stop = start + _host_end(text[start:stop])
    return (start, stop) if "." in text[start:stop] and stop - start > 6 else None


def _check_domain(text, start, end):
    before = text[start - 1] if start else " "
    if _wordy(before) or before in "@._-/%+\\":
        return None
    stop = start + _trim_address(text[start:end])
    value = text[start:stop]
    cut = min([value.find(ch) for ch in "/?#" if ch in value] or [len(value)])
    host, after = value[:cut], text[stop] if stop < len(text) else " "
    tld = host[host.rfind(".") + 1:]
    if cut == len(value):
        # The name ends the match. A letter of the same case after it means the name goes on.
        if after == "@" or _digit(after) or after == "-" or (_letter(after) and not (tld.islower() and after.isupper())):
            return None
    letters = [ch for ch in host if _letter(ch)]
    if not (tld.islower() or all(ch.isupper() for ch in letters)):
        return None   # "office.In" at the start of a sentence
    return start, stop


def _check_path_domain(text, start, end):
    """A name with a path after it. The path must be more than the punctuation that was trimmed off."""
    span = _check_domain(text, start, end)
    return span if span and "/" in text[span[0]:span[1] - 1] else None


def _check_handle(text, start, end):
    before = text[start - 1] if start else " "
    body = text[start + 1:end].rstrip(".")
    if text[start + 1 + len(body):start + 4 + len(body)] == "://":
        body = body[:-5] if body.endswith("https") else body[:-4] if body.endswith("http") else body
        body = body.rstrip(".")   # an address written against the handle
    after = text[start + 1 + len(body):start + 2 + len(body)]
    if _wordy(before) or before in "@._%+-/" or after == "@" or len(body) < 3 or not any(_letter(ch) for ch in body):
        return None
    if DOMAIN.fullmatch(body) or CLOCK.fullmatch(body):
        return None   # "@gmail.com" names a mail service, "@11am" a time
    return start, start + 1 + len(body)


def _check_upi(text, start, end):
    before = text[start - 1] if start else " "
    after = text[end:end + 2]
    if _wordy(before) or before in "._-@" or (after and (_wordy(after[0]) or (after[0] in ".-" and _wordy(after[1:] or " ")))):
        return None
    return start, end


def _check_key(text, start, end):
    return (start, end) if _apart(text, start, end, "_-") else None


CHECKS = {"card": _check_card, "iban": _check_iban, "ipv4": _check_ipv4, "ipv6": _check_ipv6, "mac": _check_mac,
          "ssn": _check_ssn, "plus_phone": _check_plus_phone, "number": _check_number,
          "word": _check_word, "url": _check_url, "domain": _check_domain, "path_domain": _check_path_domain,
          "handle": _check_handle,
          "upi": _check_upi, "key": _check_key}


def _shapes(text, table):
    """Each match that passes its check. The search goes on from where the accepted part ends, so that
    what a check cut off the end of a match (a second address, a second number) is looked at again."""
    for label, check, rank, pattern in table:
        at = 0
        while True:
            m = pattern.search(text, at)
            if not m:
                break
            span = CHECKS[check](text, m.start(), m.end())
            if span:
                yield span[0], span[1], label, (rank, 0)
            at = max(span[1] if span else m.end(), m.start() + 1)


def _credentials(text):
    """Passwords, keys and user names that a word before them names. `text` has its digits unfolded."""
    for m in SECRET_GATED.finditer(text):
        start, end = m.span("val")
        if text[start] in "\"'":
            start, end = start + 1, end - 1
        else:
            while end > start and text[end - 1] in ".,;)":
                end -= 1
        value, keyword = text[start:end], m.group("kw").lower()
        long_one = keyword not in ("password", "passwd", "pwd", "passcode", "पासवर्ड", "पासवोर्ड")
        if len(value) < (8 if long_one else 4) or NOT_SECRET.fullmatch(value):
            continue
        if "is" in m.group("gap") and value.isalpha() and value.islower():
            continue   # "the password is only for members"
        yield start, end, "SECRET", (1, len(m.group("gap")))
    for m in BEARER.finditer(text):
        yield m.start("val"), m.end("val"), "SECRET", (2, 0)
    for m in OTP_BEFORE.finditer(text):
        if _alone(text, m.start("val"), m.end("val")):
            yield m.start("val"), m.end("val"), "SECRET", (1, 0)
    for pattern, handle_like in ((USERNAME_GATED, False), (SOCIAL_GATED, True)):
        for m in pattern.finditer(text):
            start, end = m.span("val")
            while end > start and text[end - 1] in ".-":
                end -= 1
            value = text[start:end]
            after = text[end:end + 1]
            if after == "@" or len(value) < 3 or NOT_SECRET.fullmatch(value) or not any(_letter(ch) for ch in value):
                continue   # an e-mail address, a word about user names, or a number that another rule reads
            if handle_like and not (value[0] == "@" or any(_digit(ch) or ch in "_." for ch in value)):
                continue   # after the name of a service a plain word is more often a person's name
            yield start, end, "USERNAME", (1, len(m.group("gap") or ""))


def find(text):
    """Return the identifiers in `text` as sorted, non-overlapping (start, end, label).

    Where candidates overlap, a number named by a keyword wins over one recognised by shape,
    the nearer keyword wins over the farther, and then the longer match wins.
    """
    folded, marks = fold(text), fold_marks(text)
    found = []
    for finder in (_ids, _phones, _dates):
        found.extend(finder(folded))
    found.extend(_others(folded, marks))
    found.extend(_shapes(folded, SHAPES))
    found.extend(_shapes(marks, MARK_SHAPES))
    found.extend(_credentials(marks))
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
        "strong": [[label, pattern.pattern] for label, pattern in STRONG],
        "weak": [[label, pattern.pattern] for label, pattern in WEAK],
        "any_keyword": ANY_KEYWORD.pattern,
        "after_year": AFTER_YEAR.pattern,
        "phone_gated": PHONE_GATED.pattern,
        "mobile": MOBILE.pattern,
        "mobile_prefix": MOBILE_PREFIX.pattern,
        "fixed_line": FIXED_LINE.pattern,
        "landlines": [pattern.pattern for pattern in LANDLINES],
        "email": EMAIL.pattern,
        "license_shape": LICENSE_SHAPE.pattern,
        "glued_phone": GLUED_PHONE.pattern,
        "next_phone": NEXT_PHONE.pattern,
        "sentence_break": SENTENCE_BREAK.pattern,
        "symbol": SYMBOL.pattern,
        "national": {code: list(limits) for code, limits in NATIONAL.items()},
        "numeric_dates": [[pattern.pattern, order] for pattern, order in NUMERIC_DATES],
        "date_gated": DATE_GATED.pattern,
        "era_after": ERA_AFTER.pattern,
        "era_end": ERA_END.pattern,
        "decade": DECADE.pattern,
        "time": TIME.pattern,
        "whole_date": WHOLE_DATE.pattern,
        "copyright": COPYRIGHT.pattern,
        "word_dates": [pattern.pattern for pattern in WORD_DATES],
        "day_month": DAY_MONTH.pattern,
        "month_suffix": MONTH_SUFFIX.pattern,
        "plates": [pattern.pattern for pattern in PLATES],
        "shapes": [[label, check, rank, pattern.pattern] for label, check, rank, pattern in SHAPES],
        "mark_shapes": [[label, check, rank, pattern.pattern] for label, check, rank, pattern in MARK_SHAPES],
        "not_ip": NOT_IP.pattern,
        "clock": CLOCK.pattern,
        "domain": DOMAIN.pattern,
        "secret_gated": SECRET_GATED.pattern,
        "not_secret": NOT_SECRET.pattern,
        "bearer": BEARER.pattern,
        "otp_before": OTP_BEFORE.pattern,
        "username_gated": USERNAME_GATED.pattern,
        "social_gated": SOCIAL_GATED.pattern,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True, help="file to write the patterns to, such as wasm/rules.json")
    args = ap.parse_args()
    Path(args.export).write_text(json.dumps(tables(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", args.export)


if __name__ == "__main__":
    main()
