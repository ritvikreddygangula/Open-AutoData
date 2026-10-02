"""Load SEC text chunks from the Snowflake CSV export or data/chunks.json."""
import csv
import json
import re
import sys
from pathlib import Path

from src import config

_INVISIBLE = dict.fromkeys(map(ord, "​‌‍﻿"), None)


def clean_text(text: str) -> str:
    text = text.translate(_INVISIBLE).replace(" ", " ")
    lines = [line.rstrip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _from_csv(path: Path) -> list[dict]:
    csv.field_size_limit(2**31 - 1)  # sys.maxsize overflows a C long on Windows
    with path.open(newline="", encoding="utf-8-sig") as f:
        # DictReader files values beyond the header under a None key; drop them.
        rows = [{k.strip().upper(): v for k, v in row.items() if k} for row in csv.DictReader(f)]
    if rows and not {"CHUNK_ID", "CHUNK_TEXT"} <= rows[0].keys():
        raise ValueError(f"{path} needs CHUNK_ID and CHUNK_TEXT columns")
    return [
        {
            "chunk_id": row["CHUNK_ID"].strip(),
            "text": row["CHUNK_TEXT"],
            "doc_id": row.get("SEC_DOCUMENT_ID"),
            "adsh": row.get("ADSH"),
        }
        for row in rows
    ]


def load_chunks(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix == ".csv":
        raw = _from_csv(path)
    elif path.suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"unsupported chunk file type {path.suffix}")

    chunks, seen = [], set()
    for item in raw:
        chunk_id = str(item["chunk_id"])
        if chunk_id in seen:
            raise ValueError(f"duplicate chunk_id {chunk_id} in {path}")
        seen.add(chunk_id)
        text = clean_text(item["text"])
        if text:
            chunks.append({**item, "chunk_id": chunk_id, "text": text})
    return chunks


def write_chunks_json(chunks: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: python -m src.chunks <in.csv> [out.json]")
    out = sys.argv[2] if len(sys.argv) == 3 else config.CHUNKS_PATH
    chunks = load_chunks(sys.argv[1])
    write_chunks_json(chunks, out)
    print(f"wrote {len(chunks)} chunks to {out}")
