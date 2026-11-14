"""The labels of the tagger and the rules.

`docs/annotation.md` says what each label covers. The order here is the order of the tags in
a model trained on all of them.
"""

LABELS = ["PERSON", "LOCATION", "ORGANIZATION", "DATE", "PHONE", "EMAIL", "URL", "USERNAME", "IP_ADDRESS",
          "CITIZENSHIP_NO", "NATIONAL_ID", "TAX_ID", "PASSPORT_NO", "LICENSE_NO", "VOTER_ID", "ID_NUMBER",
          "BANK_ACCOUNT", "CARD_NUMBER", "UPI_ID", "VEHICLE_PLATE", "SECRET"]
# Release 0.1 called the tax number PAN. Files and models that still do are read under the new name.
ALIASES = {"PAN": "TAX_ID"}
NAMES = ("PERSON", "LOCATION", "ORGANIZATION")
# Numbers that have four digits or more, whatever their kind.
NUMBERS = ("CITIZENSHIP_NO", "NATIONAL_ID", "TAX_ID", "PASSPORT_NO", "LICENSE_NO", "VOTER_ID", "BANK_ACCOUNT",
           "CARD_NUMBER", "PHONE")
# The level at which models with other label sets are compared: every identity number is one label.
COARSE = {"CITIZENSHIP_NO": "ID", "NATIONAL_ID": "ID", "TAX_ID": "ID", "PASSPORT_NO": "ID", "LICENSE_NO": "ID",
          "VOTER_ID": "ID", "ID_NUMBER": "ID", "BANK_ACCOUNT": "ACCOUNT", "CARD_NUMBER": "ACCOUNT", "UPI_ID": "ACCOUNT",
          "VEHICLE_PLATE": "PLATE"}
# The level at which systems with any label set stand in one table: every identifying number is one label.
COMMON = {**{label: "NUMBER" for label in COARSE}, "ID": "NUMBER", "ACCOUNT": "NUMBER", "PLATE": "NUMBER"}
# What release 0.1 could mark. The test sets labelled before 0.2 are scored on these.
LABELS_0_1 = ("PERSON", "LOCATION", "ORGANIZATION", "DATE", "PHONE", "EMAIL", "CITIZENSHIP_NO", "NATIONAL_ID",
              "TAX_ID", "PASSPORT_NO", "LICENSE_NO", "VOTER_ID", "BANK_ACCOUNT", "VEHICLE_PLATE")


def canonical(label):
    """The current name of a label."""
    return ALIASES.get(label, label)


def rename(spans):
    """Spans with every label under its current name."""
    return [(start, end, canonical(label)) for start, end, label in spans]


def common(spans):
    """Spans at the level of `COMMON`."""
    return [(start, end, COMMON.get(label, label)) for start, end, label in spans]
