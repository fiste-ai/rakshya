"""Put the test labels of Rakshya back on their texts.

The texts of the test sets are not ours to publish. A file in benchmark/labels/ holds, for every text of one set,
where the text came from, its length, the SHA-256 of its UTF-8 bytes and its labels as character ranges. This
script takes texts that you have obtained, keeps those whose hash matches an entry, and writes them with their
labels, one JSON object on a line.

Two sets were cut from public datasets and come back exactly. "source" in the label file names the dataset, the
file, its revision and its hash:

    python benchmark/rebuild.py benchmark/labels/real-roman-v0.json --parquet nepali_corpus_roman.parquet
    python benchmark/rebuild.py benchmark/labels/real-gov-v1.json --parquet documents.parquet

The web sets are pieces of web pages. With your own saved copy of each page, named as "page" in the label file
says (w001.html and so on), the pieces are cut the way we cut them:

    python benchmark/rebuild.py benchmark/labels/real-web-v0.json --pages saved-pages/

For any set the texts can also be given as they are, one JSON object with "text" on a line, or one JSON string on
a line. This is the way for the news sets, whose texts are sentences from the start of the articles named by "url":

    python benchmark/rebuild.py benchmark/labels/real-news-v2.json --texts candidates.jsonl

A page or an article may have changed since the day in "retrieved", so these sets may not come back in full. The
script says how many texts it found and which are missing, and ends with status 1 when one is missing.

The result goes to NAME.jsonl in the current folder, or to --out. Each line holds "id", "text", "spans" and, where
the labelling guide accepts another reading of the text as well, "also": a list of such readings. A span is
[start, end, label]. Start and end count Unicode code points, as Python indexes a string, and the end is exclusive.
To score a system the way BENCHMARK.md does, compare its spans for a text with every accepted reading ("spans" and
each reading in "also") and keep the reading it matches best.

Needs Python 3.9 or later. --parquet needs pyarrow (pip install pyarrow).
"""
import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def visible(page):
    """The text of a web page as a person would copy it: one line for each block, the cells of a table row on one line."""
    page = re.sub(r"(?is)<(script|style|noscript|svg|head|template|iframe)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<!--.*?-->", " ", page)
    page = re.sub(r"(?i)</t[dh]\s*>", "\t", page)
    page = re.sub(r"(?i)<br\s*/?>|</(?:p|div|li|tr|h[1-6]|section|article|header|footer|table|ul|ol|dd|dt|option|address)\s*>", "\n", page)
    text = html.unescape(re.sub(r"<[^>]+>", "", page))
    lines = (re.sub(r"[ \t\r\f\v\u00a0\u200b]+", " ", line).strip() for line in text.split("\n"))
    return "\n".join(line for line in lines if line)


def from_parquet(labels, path):
    """The texts of a set that was cut from a table of a public dataset."""
    source = labels.get("source")
    if not source:
        raise SystemExit(f"{labels['name']} was not cut from a dataset: use --pages or --texts")
    try:
        import pyarrow as pa
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
    except ImportError:
        raise SystemExit("--parquet needs pyarrow: pip install pyarrow") from None
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != source["sha256"]:
        print(f"note: {path} is not the file the texts were cut from (another revision of {source['dataset']}?)", file=sys.stderr)
    columns = [source["key"], source["field"]] if "key" in source else [source["field"]]
    try:
        table = pq.read_table(path, columns=columns)
    except Exception as error:   # another table: it has no such column, or it is no parquet file
        raise SystemExit(f"{path} cannot be read as {source['file']} of {source['dataset']}: {str(error).splitlines()[0]}") from None
    if "key" in source:   # documents with an id: a text is a range of characters of one document
        wanted = sorted({item["doc"] for item in labels["items"]})
        table = table.filter(pc.is_in(table[source["key"]], value_set=pa.array(wanted)))
        documents = dict(zip(table.column(source["key"]).to_pylist(), table.column(source["field"]).to_pylist()))
        return [documents[item["doc"]][item["start"]:item["end"]] for item in labels["items"] if item["doc"] in documents]
    rows = table.column(source["field"]).to_pylist()   # a text is one row
    return [rows[item["row"]] for item in labels["items"] if item["row"] < len(rows)]


def from_pages(labels, folder):
    """The texts of a set that was cut from web pages, out of saved copies of those pages."""
    if not all("page" in item for item in labels["items"]):
        raise SystemExit(f"{labels['name']} was not cut from saved pages: use --parquet or --texts")
    pages, texts = {}, []
    for item in labels["items"]:
        path = Path(folder) / (item["page"] + ".html")
        if not path.exists():
            continue
        if path not in pages:
            pages[path] = visible(path.read_text(encoding="utf-8", errors="replace"))
        texts.append(pages[path][item["start"]:item["end"]])
    return texts


def from_texts(path):
    """Texts given as they are: on each line a JSON object with "text", or a JSON string."""
    texts = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").split("\n"), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
            texts.append(value if isinstance(value, str) else value["text"])
        except (ValueError, KeyError, TypeError):
            raise SystemExit(f"{path}, line {number}: expected a JSON object with \"text\", or a JSON string") from None
    return texts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("labels", help="a file of benchmark/labels/")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--parquet", help="the table of the public dataset that the set was cut from")
    where.add_argument("--pages", help="a folder with saved copies of the web pages, named as the label file says")
    where.add_argument("--texts", help="texts as they are: a JSON object with \"text\" on each line")
    parser.add_argument("--out", help="where the labelled texts are written; by default NAME.jsonl in the current folder")
    args = parser.parse_args()
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))
    if args.parquet:
        texts = from_parquet(labels, args.parquet)
    elif args.pages:
        texts = from_pages(labels, args.pages)
    else:
        texts = from_texts(args.texts)
    found = {digest(text): text for text in texts}
    rows, missing = [], []
    for item in labels["items"]:
        if item["sha256"] not in found:
            missing.append(item["id"])
            continue
        row = {"id": item["id"], "text": found[item["sha256"]], "spans": item["spans"]}
        if "also" in item:
            row["also"] = item["also"]
        rows.append(row)
    out = Path(args.out or labels["name"] + ".jsonl")
    out.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(f"{len(rows)} of {len(labels['items'])} texts of {labels['name']} -> {out}")
    if missing:
        print("not found: " + " ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
