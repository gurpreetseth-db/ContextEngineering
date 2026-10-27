"""Chunking strategies for the GridWorks procedure documents (stdlib only).

Teaching point: pick the strategy from document structure and query type; do not treat one size as universal.
  structure_aware : split on markdown headings, keep the heading path with each chunk (stable, meaningful units)
  recursive       : fallback for weakly structured text; split by paragraph, then sentence, with overlap
Every chunk gets a stable id (document_id#n) and carries the metadata used for filtering.
"""
from __future__ import annotations
import re


def structure_aware(doc: dict, max_chars: int = 1200, merge_small: bool = False) -> list[dict]:
    """Split on markdown headings. Oversized sections fall through to the recursive splitter.

    merge_small=True keeps adjacent small sections together (up to max_chars) so that a rule and its
    conditions are not separated: a short procedure stays one chunk."""
    sections, path, buf = [], [], []

    def flush():
        text = "\n".join(buf).strip()
        if text:
            sections.append((" > ".join(path), text))

    for line in doc["text"].splitlines():
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            flush(); buf.clear()
            level = len(m.group(1))
            path[:] = path[: level - 1] + [m.group(2).strip()]
        else:
            buf.append(line)
    flush()
    if merge_small:
        merged = []
        for heading, text in sections:
            if merged and len(merged[-1][1]) + len(text) + 2 <= max_chars:
                h0, t0 = merged[-1]
                merged[-1] = (h0.split(" > ")[0] if " > " in h0 else h0, t0 + "\n\n" + text)
            else:
                merged.append((heading, text))
        sections = merged
    chunks = []
    for heading, text in sections:
        parts = [text] if len(text) <= max_chars else recursive(text, max_chars, overlap=int(max_chars * 0.12))
        for p in parts:
            chunks.append((heading, p))
    return _decorate(doc, chunks)


def recursive(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Paragraph -> sentence splitting with a small overlap so facts spanning a boundary survive."""
    pieces = [s for para in re.split(r"\n\s*\n", text) for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
    out, cur = [], ""
    for s in pieces:
        if len(cur) + len(s) + 1 > max_chars and cur:
            out.append(cur.strip())
            cur = cur[-overlap:] + " " + s if overlap else s
        else:
            cur = (cur + " " + s).strip()
    if cur.strip():
        out.append(cur.strip())
    return out


def _decorate(doc: dict, chunks: list[tuple[str, str]]) -> list[dict]:
    rows = []
    for i, (heading, text) in enumerate(chunks):
        rows.append({
            "chunk_id": f"{doc['document_id']}#{i:02d}",
            "document_id": doc["document_id"],
            "title": doc["title"],
            "heading": heading,
            # Embed title + heading with the text so a chunk is understandable on its own
            "text": f"{doc['title']} — {heading}\n{text}" if heading else f"{doc['title']}\n{text}",
            "region_code": doc["region_code"],
            "status": doc["status"],
            "effective_date": str(doc["effective_date"]),
            "source_uri": f"/Volumes/gsethi/ce_shared/docs/{doc['document_id']}.md",
        })
    return rows


def chunk_corpus(docs: list[dict], strategy: str = "structure_aware") -> list[dict]:
    if strategy == "structure_aware":
        return [c for d in docs for c in structure_aware(d)]
    if strategy == "merged":
        return [c for d in docs for c in structure_aware(d, merge_small=True)]
    if strategy == "fixed_sentence":  # deliberately bad: used in the lab to show lost conditions
        return [c for d in docs for c in _decorate(d, [("", s) for s in re.split(r"(?<=[.!?])\s+", d["text"]) if s.strip()])]
    raise ValueError(strategy)
