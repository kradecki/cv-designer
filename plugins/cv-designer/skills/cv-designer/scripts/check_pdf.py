#!/usr/bin/env python3
"""
Machine-readability checks for a rendered CV PDF. Run this before delivering.

    python check_pdf.py --pdf out/Name-CV.pdf --data cv-tailored.yaml [--max-pages 2]

Checks (each reported as pass/fail with evidence):
  pages            page count within limit
  text_layer       text is extractable and contains the name
  section_order    standard headings appear in the extracted text in the order rendered
  fonts_embedded   every font is embedded (pdffonts)
  metadata         Title and Author set
  unicode_text     no private-use glyphs in the text layer (OpenType alternates break digits/ligatures)
  words_intact     pdfminer (the extractor behind many parsers) does not split words in titles/headings/bullets
  no_tiny_text     no characters below 6.5 pt (a hidden-keyword smell; parsers flag it)
  no_white_text    no near-white text on the page (same smell)
  links            link annotations exist for every URL in the data
  file_size        under 2 MB
  bullets_present  every visible role's bullets appear in the text layer

Exit 0 when all pass, 1 otherwise. Prints a JSON report on the last line.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pdfplumber
import yaml
from pypdf import PdfReader

HEADING_ORDER = ["Summary", "Experience", "Skills", "Selected projects", "Education",
                 "Certifications", "Publications & talks", "Languages"]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--max-pages", type=int, default=2)
    args = ap.parse_args()

    data = yaml.safe_load(args.data.read_text(encoding="utf-8"))
    basics = data["basics"]
    results = {}

    def rec(name, passed, evidence):
        results[name] = {"passed": bool(passed), "evidence": evidence}

    # --- text + chars ---
    with pdfplumber.open(str(args.pdf)) as doc:
        pages = len(doc.pages)
        text = "\n".join((p.extract_text() or "") for p in doc.pages)
        chars = [c for p in doc.pages for c in p.chars]
    ntext = norm(text)

    rec("pages", pages <= args.max_pages, f"{pages} page(s), limit {args.max_pages}")
    rec("text_layer", len(ntext) > 200 and norm(basics["name"]) in ntext,
        f"{len(ntext)} chars extracted; name {'found' if norm(basics['name']) in ntext else 'NOT found'}")

    # --- private-use glyphs (ligatures / numeral alternates without Unicode mapping) ---
    pua = re.findall(r"[\ue000-\uf8ff]", text)
    rec("unicode_text", not pua, f"{len(pua)} private-use chars" + (" — check font-variant settings in style.css" if pua else ""))

    # --- word integrity under pdfminer's own layout analysis (pdfplumber is more tolerant) ---
    from pdfminer.high_level import extract_text as _pm_extract
    pm_text = re.sub(r"\s+", " ", _pm_extract(str(args.pdf)))
    probe_words = set()
    for r in data.get("experience") or []:
        if not r.get("hidden"):
            probe_words.update(re.findall(r"[A-Za-z]{5,}", " ".join([r.get("title") or "", r.get("company") or "", *(r.get("bullets") or [])])))
    for g in data.get("skills") or []:
        probe_words.update(re.findall(r"[A-Za-z]{5,}", " ".join([g.get("group") or "", *(g.get("items") or [])])))
    probe_words.update(re.findall(r"[A-Za-z]{5,}", basics.get("headline") or ""))
    probe_words.update(["Summary", "Experience", "Skills", "Education", "Languages"])
    split = sorted(w for w in probe_words if not re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", pm_text))
    rec("words_intact", not split, f"{len(split)} word(s) split or missing under pdfminer" + (f": {split[:8]}" if split else ""))

    # --- section order ---
    found = [(m.start(), h) for h in HEADING_ORDER
             if (m := re.search(r"(?im)^\s*" + re.escape(h) + r"\s*$", text))]   # standalone lines only
    present = [h for _, h in sorted(found)]
    positions = [pos for pos, _ in found]
    rec("section_order", positions == sorted(positions) and len(present) >= 3,
        f"headings in text order: {present}")

    # --- fonts ---
    if shutil.which("pdffonts"):
        out = subprocess.run(["pdffonts", str(args.pdf)], capture_output=True, text=True).stdout
        rows = [ln for ln in out.splitlines()[2:] if ln.strip()]
        # pdffonts row: name type encoding emb sub uni object ID  → the three yes/no columns end the row
        not_emb = []
        for ln in rows:
            m = re.search(r"\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", ln)
            if m and m.group(1) == "no":
                not_emb.append(ln.split()[0])
        rec("fonts_embedded", len(rows) > 0 and not not_emb, f"{len(rows)} font(s); not embedded: {not_emb or 'none'}")
    else:
        rec("fonts_embedded", True, "pdffonts unavailable; skipped")

    # --- metadata ---
    meta = PdfReader(str(args.pdf)).metadata or {}
    title, author = meta.get("/Title"), meta.get("/Author")
    rec("metadata", bool(title) and bool(author), f"Title={title!r} Author={author!r}")

    # --- tiny / white text ---
    tiny = [c["text"] for c in chars if c.get("size", 10) < 6.5 and c["text"].strip()]
    rec("no_tiny_text", not tiny, f"{len(tiny)} chars under 6.5pt" + (f": {''.join(tiny[:40])!r}" if tiny else ""))

    def is_whiteish(col):
        if col is None:
            return False
        try:
            vals = [float(v) for v in (col if isinstance(col, (list, tuple)) else [col])]
        except Exception:
            return False
        if len(vals) == 1:
            return vals[0] > 0.92
        if len(vals) == 3:
            return all(v > 0.92 for v in vals)
        if len(vals) == 4:  # CMYK
            return all(v < 0.08 for v in vals)
        return False
    white = [c["text"] for c in chars if c["text"].strip() and is_whiteish(c.get("non_stroking_color"))]
    rec("no_white_text", not white, f"{len(white)} near-white chars")

    # --- links ---
    wanted = [l["url"] for l in (basics.get("links") or [])]
    if basics.get("email"):
        wanted.append("mailto:" + basics["email"])
    found = set()
    for pg in PdfReader(str(args.pdf)).pages:
        for a in (pg.get("/Annots") or []):
            obj = a.get_object()
            uri = (obj.get("/A") or {}).get("/URI")
            if uri:
                found.add(str(uri))
    missing = [u for u in wanted if not any(u.rstrip("/") == f.rstrip("/") for f in found)]
    rec("links", not missing, f"{len(found)} link annotation(s); missing: {missing or 'none'}")

    # --- size ---
    size = os.path.getsize(args.pdf)
    rec("file_size", size < 2 * 1024 * 1024, f"{size/1024:.0f} KB")

    # --- bullets present ---
    missing_b = []
    for r in data.get("experience") or []:
        if r.get("hidden"):
            continue
        for b in r.get("bullets") or []:
            probe = norm(b)[:60]
            if probe and probe not in ntext.replace("\n", " "):
                # allow line-wrap hyphenation differences: compare on a shorter prefix
                if norm(b)[:30] not in ntext:
                    missing_b.append(b[:50])
    rec("bullets_present", not missing_b, f"missing: {missing_b or 'none'}")

    ok = all(v["passed"] for v in results.values())
    for k, v in results.items():
        print(f"[{'PASS' if v['passed'] else 'FAIL'}] {k}: {v['evidence']}")
    print(json.dumps({"ok": ok, "pages": pages, "checks": results}, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
