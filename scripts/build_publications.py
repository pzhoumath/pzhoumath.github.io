#!/usr/bin/env python3
"""Convert data/publications.bib into data/publications.json for Hugo.

Pure standard library, no third-party dependencies (so CI needs nothing
but a system python3). Handles the BibTeX Google Scholar exports produce:
brace- or quote-delimited field values, nested braces (e.g. for protected
capitalization like ``{The {A}-side}``), and ``%``-prefixed comment lines.

Two extra, non-standard fields are recognized if present on an entry:
``tags`` (comma-separated) and ``pdf`` (a direct URL), for manual
curation on top of what Google Scholar exports.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB_PATH = ROOT / "bibliography" / "publications.bib"
JSON_PATH = ROOT / "data" / "publications.json"


def strip_comments(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("%"):
            continue
        lines.append(line)
    return "\n".join(lines)


def split_top_level(s: str, sep: str = ",") -> list[str]:
    """Split on sep, ignoring occurrences inside {..} or "..." nesting."""
    parts = []
    depth = 0
    in_quotes = False
    current = []
    for ch in s:
        if ch == '"' and depth == 0:
            in_quotes = not in_quotes
        elif ch == "{" and not in_quotes:
            depth += 1
        elif ch == "}" and not in_quotes:
            depth -= 1
        if ch == sep and depth == 0 and not in_quotes:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return parts


def clean_value(value: str) -> str:
    value = value.strip().rstrip(",").strip()
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1]
    elif value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    value = value.replace("{", "").replace("}", "")
    value = " ".join(value.split())
    return value.strip()


def parse_entries(text: str):
    entries = []
    pos = 0
    n = len(text)
    while True:
        at = text.find("@", pos)
        if at == -1:
            break
        m = re.match(r"@(\w+)\s*\{", text[at:])
        if not m:
            pos = at + 1
            continue
        entry_type = m.group(1).lower()
        body_start = at + m.end()
        depth = 1
        i = body_start
        while i < n and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[body_start : i - 1]
        pos = i

        if entry_type == "comment":
            continue

        top = split_top_level(body, ",")
        if not top:
            continue
        citekey = top[0].strip()
        fields = {}
        for chunk in top[1:]:
            if "=" not in chunk:
                continue
            key, value = chunk.split("=", 1)
            key = key.strip().lower()
            if not key:
                continue
            fields[key] = clean_value(value)
        entries.append({"type": entry_type, "key": citekey, "fields": fields})
    return entries


def format_authors(raw: str) -> list[str]:
    if not raw:
        return []
    names = [n.strip() for n in raw.split(" and ") if n.strip()]
    formatted = []
    for name in names:
        if "," in name:
            last, first = name.split(",", 1)
            formatted.append(f"{first.strip()} {last.strip()}")
        else:
            formatted.append(name)
    return formatted


ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5})")


def resolve_venue_and_arxiv(fields: dict):
    arxiv_id = ""
    if fields.get("archiveprefix", "").lower() == "arxiv" and fields.get("eprint"):
        arxiv_id = fields["eprint"]

    venue = ""
    if fields.get("journal"):
        journal = fields["journal"]
        if "arxiv" in journal.lower():
            venue = "arXiv"
            if not arxiv_id:
                match = ARXIV_RE.search(journal)
                if match:
                    arxiv_id = match.group(1)
        else:
            venue = journal
    elif fields.get("booktitle"):
        venue = fields["booktitle"]
    elif arxiv_id:
        venue = "arXiv"

    if not arxiv_id and fields.get("url"):
        match = ARXIV_RE.search(fields["url"])
        if match and "arxiv" in fields["url"].lower():
            arxiv_id = match.group(1)

    return venue, arxiv_id


def to_record(entry: dict) -> dict:
    fields = entry["fields"]
    venue, arxiv_id = resolve_venue_and_arxiv(fields)
    arxiv_match = ARXIV_RE.fullmatch(arxiv_id)
    arxiv_year = 2000 + int(arxiv_id[:2]) if arxiv_match else None
    year_raw = fields.get("year", "")
    try:
        year = int(re.sub(r"\D", "", year_raw)) if year_raw else None
    except ValueError:
        year = None

    tags = []
    if fields.get("tags"):
        tags = [t.strip() for t in fields["tags"].split(",") if t.strip()]

    return {
        "key": entry["key"],
        "type": entry["type"],
        "title": fields.get("title", ""),
        "authors": format_authors(fields.get("author", "")),
        "year": year,
        "venue": venue,
        "arxiv": arxiv_id,
        "arxiv_year": arxiv_year,
        "doi": fields.get("doi", ""),
        "url": fields.get("url", ""),
        "pdf": fields.get("pdf", ""),
        "tags": tags,
    }


def main() -> int:
    if not BIB_PATH.exists():
        print(f"error: {BIB_PATH} not found", file=sys.stderr)
        return 1

    text = strip_comments(BIB_PATH.read_text(encoding="utf-8"))
    entries = parse_entries(text)
    records = [to_record(e) for e in entries]
    records.sort(
        key=lambda r: tuple(int(part) for part in r["arxiv"].split("."))
        if ARXIV_RE.fullmatch(r["arxiv"])
        else (-1, -1),
        reverse=True,
    )

    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {len(records)} publication(s) to {JSON_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
