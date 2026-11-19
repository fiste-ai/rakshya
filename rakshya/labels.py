"""The labels of the tagger and the rules.

`docs/annotation.md` says what each label covers. `LABELS` is the one set of 1.0, which the
model, every training text, every test set and the dataset of practical paragraphs share
(`docs/plan-data.md`): the order here is the order of the tags in a model trained on all of
them. Releases 0.1 to 0.3 had 21 labels under partly other names (`LABELS_0_3`).

Inside, the rules and the checks on a tagger's spans go on telling apart what the older names
told apart (an address of a machine from a password, a citizenship number from a national
identity number): `plausible` in `rakshya/spans.py` knows both sets of names. What leaves the
code, in a training row, a score or the answer of the runtime, carries the final names
(`rename`).
"""

LABELS = ["PERSON", "LOCATION", "ORGANIZATION", "DATE", "ADDRESS", "DOB", "PHONE", "EMAIL", "URL", "DIGITAL_SECRET",
          "NATIONAL_ID", "TAX_ID", "PASSPORT", "DRIVER_LICENSE", "VOTER_ID", "MEDICAL_ID", "EMPLOYEE_STUDENT_ID",
          "PROPERTY_UTILITY_ID", "ID_NUMBER", "BANK_ACCOUNT", "CREDIT_CARD", "PAYMENT_ID", "VEHICLE_ID"]
# The labels of the models of 0.2 and 0.3, in the order of their tags.
LABELS_0_3 = ["PERSON", "LOCATION", "ORGANIZATION", "DATE", "PHONE", "EMAIL", "URL", "USERNAME", "IP_ADDRESS",
              "CITIZENSHIP_NO", "NATIONAL_ID", "TAX_ID", "PASSPORT_NO", "LICENSE_NO", "VOTER_ID", "ID_NUMBER",
              "BANK_ACCOUNT", "CARD_NUMBER", "UPI_ID", "VEHICLE_PLATE", "SECRET"]
# Names of things. Every other label is personal data: what a redaction takes out under the profile "personal".
THINGS = ("LOCATION", "ORGANIZATION", "DATE", "URL")
PERSONAL = tuple(label for label in LABELS if label not in THINGS)
# What a tagger of 1.0 tells apart beyond the 23 labels: whether a phone number or a mailbox is a person's or that of
# an office, a helpline, a shared desk. Both leave the code under the one label where every label is asked for; the
# profile "personal" leaves the office's alone (the owner's decision of 2026-11-17).
OFFICE = {"OFFICE_PHONE": "PHONE", "OFFICE_EMAIL": "EMAIL"}
# In a training row: a phone number or a mailbox that is said to be a person's own. Under the plain label the row
# does not tell whose it is, and the tagger may give either (`rakshya.train`).
OWN = {"OWN_PHONE": "PHONE", "OWN_EMAIL": "EMAIL"}
# The labels of a tagger of 1.0, in the order of its tags.
TAGGED = [*LABELS, *OFFICE]
# Release 0.1 called the tax number PAN. A model that still does is read under the new name before its spans are checked.
EARLY = {"PAN": "TAX_ID"}
# The names of releases 0.1 to 0.3 and of the batches of the dataset. Files and models that use them are read under the final name.
ALIASES = {**EARLY, "CITIZENSHIP_NO": "NATIONAL_ID", "PASSPORT_NO": "PASSPORT", "LICENSE_NO": "DRIVER_LICENSE",
           "CARD_NUMBER": "CREDIT_CARD", "UPI_ID": "PAYMENT_ID", "VEHICLE_PLATE": "VEHICLE_ID", "USERNAME": "DIGITAL_SECRET",
           "IP_ADDRESS": "DIGITAL_SECRET", "SECRET": "DIGITAL_SECRET", "DEVICE_ID": "DIGITAL_SECRET", "DRIVING_LICENSE": "DRIVER_LICENSE",
           "HEALTH_ID": "MEDICAL_ID", "PAYMENT_CARD": "CREDIT_CARD", "AADHAAR": "NATIONAL_ID", "CITIZENSHIP_ID": "NATIONAL_ID",
           **OFFICE, **OWN}
# A source that leaves a label unmarked leaves these unmarked with it: text labelled before 1.0 has a date of birth among its
# dates, the address of a person among its places and every number of a person under one label, or not at all.
WIDER = {"DATE": ("DOB",), "LOCATION": ("ADDRESS",), "ID_NUMBER": ("MEDICAL_ID", "EMPLOYEE_STUDENT_ID", "PROPERTY_UTILITY_ID")}
NAMES = ("PERSON", "LOCATION", "ORGANIZATION")
# Numbers that have four digits or more, whatever their kind, under their final and their older names.
NUMBERS = ("NATIONAL_ID", "TAX_ID", "PASSPORT", "DRIVER_LICENSE", "VOTER_ID", "BANK_ACCOUNT", "CREDIT_CARD", "PHONE",
           "CITIZENSHIP_NO", "PASSPORT_NO", "LICENSE_NO", "CARD_NUMBER", "OFFICE_PHONE")
# The level at which models with other label sets are compared: every identity number is one label.
COARSE = {"NATIONAL_ID": "ID", "TAX_ID": "ID", "PASSPORT": "ID", "DRIVER_LICENSE": "ID", "VOTER_ID": "ID", "ID_NUMBER": "ID",
          "MEDICAL_ID": "ID", "EMPLOYEE_STUDENT_ID": "ID", "PROPERTY_UTILITY_ID": "ID", "BANK_ACCOUNT": "ACCOUNT",
          "CREDIT_CARD": "ACCOUNT", "PAYMENT_ID": "ACCOUNT", "VEHICLE_ID": "PLATE"}
# The level at which systems with any label set stand in one table: every identifying number is one label, the address of a
# person counts with the places and a date of birth with the dates, as the text labelled before 1.0 has them.
COMMON = {**{label: "NUMBER" for label in COARSE}, "ID": "NUMBER", "ACCOUNT": "NUMBER", "PLATE": "NUMBER", "ADDRESS": "LOCATION",
          "DOB": "DATE"}
# A label under an older name stands at either level where its final name stands.
COARSE.update({old: COARSE.get(new, new) for old, new in ALIASES.items()})
COMMON.update({old: COMMON.get(new, new) for old, new in ALIASES.items()})
# What release 0.1 could mark. The test sets labelled before 0.2 are scored on these.
LABELS_0_1 = ("PERSON", "LOCATION", "ORGANIZATION", "DATE", "PHONE", "EMAIL", "NATIONAL_ID", "TAX_ID", "PASSPORT",
              "DRIVER_LICENSE", "VOTER_ID", "BANK_ACCOUNT", "VEHICLE_ID")


def canonical(label):
    """The final name of a label."""
    return ALIASES.get(label, label)


def said(label):
    """The label of a training row under its final name; whose a phone number or a mailbox is stays as the row says it."""
    return label if label in OFFICE or label in OWN else canonical(label)


def inner(label):
    """The label under which a tagger of 1.0 learns a label of a training row: the final name, and the office's own."""
    return label if label in OFFICE else canonical(label)


def either(label):
    """The other label a tagger may give where a training row does not tell whose a phone number or a mailbox is; None where it tells."""
    return {new: office for office, new in OFFICE.items()}.get(label)


def rename(spans):
    """Spans with every label under its final name."""
    return [(start, end, canonical(label)) for start, end, label in spans]


def common(spans):
    """Spans at the level of `COMMON`."""
    return [(start, end, COMMON.get(label, label)) for start, end, label in spans]


def widened(unknown):
    """The labels a source leaves unmarked, with those that 1.0 split off from them."""
    out = list(unknown)
    for label in unknown:
        out += [more for more in WIDER.get(canonical(label), ()) if more not in out]
    return out
