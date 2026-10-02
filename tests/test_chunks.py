import json

import pytest

from src.chunks import clean_text, load_chunks, write_chunks_json

HEADER = "CHUNK_ID,SEC_DOCUMENT_ID,ADSH,CHUNK_TEXT\n"


def write_csv(tmp_path, body):
    path = tmp_path / "chunks.csv"
    path.write_text(HEADER + body, encoding="utf-8")
    return path


def test_clean_text_drops_zero_width_filler_lines():
    raw = "RESULTS\n​\n​\n​\nRevenue rose 4%. Net income fell.  \n"
    assert clean_text(raw) == "RESULTS\n\nRevenue rose 4%. Net income fell."


def test_load_csv_maps_snowflake_columns(tmp_path):
    path = write_csv(tmp_path, '4,doc-1,adsh-1,"Revenue was $86.3 million."\n')
    assert load_chunks(path) == [
        {"chunk_id": "4", "text": "Revenue was $86.3 million.", "doc_id": "doc-1", "adsh": "adsh-1"}
    ]


def test_load_csv_accepts_lowercase_headers(tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("chunk_id,chunk_text\n1,hello\n", encoding="utf-8")
    assert load_chunks(path)[0]["text"] == "hello"


def test_load_skips_chunks_empty_after_cleaning(tmp_path):
    path = write_csv(tmp_path, '1,d,a,"​\n​"\n2,d,a,real text\n')
    assert [c["chunk_id"] for c in load_chunks(path)] == ["2"]


def test_load_rejects_duplicate_chunk_ids(tmp_path):
    path = write_csv(tmp_path, "1,d,a,one\n1,d,a,two\n")
    with pytest.raises(ValueError, match="duplicate chunk_id 1"):
        load_chunks(path)


def test_load_rejects_csv_without_text_column(tmp_path):
    path = tmp_path / "c.csv"
    path.write_text("CHUNK_ID,BODY\n1,x\n", encoding="utf-8")
    with pytest.raises(ValueError, match="CHUNK_TEXT"):
        load_chunks(path)


def test_json_round_trip(tmp_path):
    chunks = [{"chunk_id": "7", "text": "Some text", "doc_id": None, "adsh": None}]
    out = tmp_path / "nested" / "chunks.json"
    write_chunks_json(chunks, out)
    assert json.loads(out.read_text())[0]["chunk_id"] == "7"
    assert load_chunks(out) == chunks


def test_load_rejects_unknown_extension(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("x")
    with pytest.raises(ValueError, match=".txt"):
        load_chunks(path)
