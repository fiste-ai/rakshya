"""Hide personal information in text from the command line.

    rakshya "मेरो नाम सीता थापा हो, फोन ९८००००००००"      # prints the text with [PERSON_1], [PHONE_1], ...
    rakshya --spans < letter.txt                          # prints one JSON line: [[start, end, label], ...]
    rakshya --personal "..."                              # personal data only: places, organisations and dates stay
    rakshya --lite "..."                                  # the lighter model of the same version
    rakshya --model folder "..."                          # a model folder instead of a released model

Without a text argument the text is read from standard input.
"""
import argparse
import json
import sys

from .runtime import NO_SERVER, Rakshya


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rakshya", description="Find and hide personal information in Nepali, romanised Nepali and English text.")
    ap.add_argument("text", nargs="?", help="the text; read from standard input when left out")
    ap.add_argument("--spans", action="store_true", help="print the spans as JSON and leave the text as it is")
    ap.add_argument("--model", help="a folder with the model files; by default the released model is fetched")
    ap.add_argument("--lite", action="store_true", help="use the lighter model of the same version: 6 layers, smaller and faster")
    ap.add_argument("--server", action="store_true", help=argparse.SUPPRESS)   # an option of release 0.2
    ap.add_argument("--personal", action="store_true",
                    help="hide personal data only: places, organisations, dates, web addresses, an office's phone number and mailbox and masked numbers stay")
    ap.add_argument("--threads", type=int, default=0)
    args = ap.parse_args(argv)
    if args.server:
        ap.error(NO_SERVER)
    text = args.text if args.text is not None else sys.stdin.read()
    pii = Rakshya(args.model, threads=args.threads, model="lite" if args.lite else "small")
    labels = "personal" if args.personal else "all"
    print(json.dumps(pii.find(text, labels), ensure_ascii=False) if args.spans else pii.redact(text, labels))


if __name__ == "__main__":
    main()
