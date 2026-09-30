#!/usr/bin/env python3
"""
Extract text from a LinkedIn "Save to PDF" profile export, separating the sidebar
(Contact, Top Skills, Languages, Certifications, ...) from the main column
(name, headline, Summary, Experience, Education), and write a best-effort draft YAML.

    python extract_linkedin.py --pdf Profile.pdf --out-dir work/

Writes:
  work/linkedin.txt        clean text, sidebar and main column kept apart, page by page
  work/linkedin-draft.yaml heuristic structured draft (experience entries split on date lines)

The draft is a starting point, not the truth: read linkedin.txt and correct the YAML by hand.
Exit 0 on success; prints a JSON summary line.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber
import yaml

SIDEBAR_HEADINGS = {"Contact", "Top Skills", "Languages", "Certifications", "Honors-Awards",
                    "Publications", "Patents", "Courses", "Projects", "Organizations", "Test Scores"}
MAIN_HEADINGS = {"Summary", "Experience", "Education", "Volunteer Experience"}

DATE_RANGE = re.compile(
    r"^(?P<start>(?:[A-Z][a-z]+ )?\d{4})\s*[-–]\s*(?P<end>(?:[A-Z][a-z]+ )?\d{4}|Present)"
    r"(?:\s*\((?P<dur>[^)]*)\))?\s*$"
)
DURATION_ONLY = re.compile(r"^\(?\d+\s+(?:year|years|month|months)(?:\s+\d+\s+months?)?\)?$")
PAGE_FOOTER = re.compile(r"^\s*Page \d+ of \d+\s*$")
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], 1)}


def norm_date(s: str) -> str:
    s = s.strip()
    if s.lower() == "present":
        return "present"
    m = re.fullmatch(r"([A-Z][a-z]+) (\d{4})", s)
    if m and m.group(1) in MONTHS:
        return f"{m.group(2)}-{MONTHS[m.group(1)]:02d}"
    return s


def clean_lines(text: str):
    out = []
    for ln in (text or "").splitlines():
        ln = ln.rstrip()
        if not ln.strip() or PAGE_FOOTER.match(ln):
            continue
        out.append(ln.strip())
    return out


def split_page(page, split_x):
    """Return (sidebar_lines, main_lines) for one page."""
    w, h = page.width, page.height
    if split_x is None:
        return [], clean_lines(page.extract_text())
    left = page.crop((0, 0, split_x, h))
    right = page.crop((split_x, 0, w, h))
    left_chars = len(left.chars)
    total = len(page.chars) or 1
    if left_chars == 0:
        return [], clean_lines(right.extract_text())
    if left_chars / total > 0.6:
        # main column occupies the left region on this page → treat as full-width main
        return [], clean_lines(page.extract_text())
    return clean_lines(left.extract_text()), clean_lines(right.extract_text())


def find_split_x(page):
    """Locate the main column: the x0 of the largest text on page 1 (the person's name)."""
    if not page.chars:
        return None
    biggest = max(page.chars, key=lambda c: c["size"])
    name_x0 = min(c["x0"] for c in page.chars if abs(c["size"] - biggest["size"]) < 0.5
                  and abs(c["top"] - biggest["top"]) < biggest["size"])
    # only split if something sits clearly to the left of the name
    has_left = any(c["x1"] < name_x0 - 8 for c in page.chars)
    return (name_x0 - 6) if has_left else None


def sections_from(lines, headings):
    """Split a flat list of lines into {heading: [lines]} using exact heading matches."""
    cur = "_pre"
    out = {cur: []}
    for ln in lines:
        if ln in headings:
            cur = ln
            out.setdefault(cur, [])
            continue
        out.setdefault(cur, []).append(ln)
    return out


BULLET_START = re.compile(r"^[•\-–*·]\s+")


def unwrap(lines):
    """
    Join PDF-wrapped lines into logical lines. A new logical line starts at a bullet marker, a date
    range, a duration-only line, or after a line that ends a sentence. A trailing hyphen joins without
    a space ("large-" + "scale" -> "large-scale").
    """
    out = []
    for ln in lines:
        starts_new = (not out or BULLET_START.match(ln) or DATE_RANGE.match(ln) or DURATION_ONLY.match(ln)
                      or DATE_RANGE.match(out[-1]) or DURATION_ONLY.match(out[-1])
                      or re.search(r"[.!?:]\s*$", out[-1]) or len(out[-1]) < 40 and not out[-1].endswith(","))
        if starts_new:
            out.append(ln)
        elif out[-1].endswith("-") and not out[-1].endswith(" -"):
            out[-1] = out[-1] + ln
        else:
            out[-1] = out[-1] + " " + ln
    return out


def looks_like_header(ln):
    """Company or title line: short, no terminal punctuation, no bullet marker."""
    return len(ln) < 70 and not re.search(r"[.!?]$", ln) and not BULLET_START.match(ln)


def parse_experience(lines):
    """
    LinkedIn layout per role:  Company / Title / 'Mar 2021 - Present (x years)' / Location? / description...
    Multi-role at one company:  Company / '(total duration)' / Title / dates / ... / Title / dates / ...
    """
    roles = []
    i = 0
    company = None
    pending = []  # lines seen since the last role ended (company / title candidates)
    while i < len(lines):
        ln = lines[i]
        m = DATE_RANGE.match(ln)
        if m:
            # the line(s) before the date are title (and maybe company)
            title = pending[-1] if pending else None
            if len(pending) >= 2:
                company = pending[-2]
            elif company is None and pending:
                company = pending[0]
            role = {"company": company, "title": title,
                    "start": norm_date(m.group("start")), "end": norm_date(m.group("end")),
                    "location": None, "bullets": [], "_raw": []}
            i += 1
            # optional location line: short, few words, no sentence punctuation, no bullet marker
            if i < len(lines) and len(lines[i]) < 50 and len(lines[i].split()) <= 5 \
                    and not re.search(r"[.!?:]$", lines[i]) and not BULLET_START.match(lines[i]) \
                    and not DATE_RANGE.match(lines[i]) and not DURATION_ONLY.match(lines[i]) \
                    and re.search(r"[A-Za-z]", lines[i]):
                role["location"] = lines[i]
                i += 1
            # description until the next date line (minus the 1–2 header lines before it)
            desc = []
            while i < len(lines) and not DATE_RANGE.match(lines[i]):
                desc.append(lines[i])
                i += 1
            # the last 1–2 non-empty lines before the next date range are the next role's headers
            if i < len(lines):
                # Next role's header is 1 line (title only, same company) or 2 lines (company + title).
                # Description lines are long or punctuated; header lines are short and bare.
                if len(desc) >= 2 and DURATION_ONLY.match(desc[-2]) and len(desc) >= 3:
                    nxt_hdr = 3          # company / (total duration) / title
                elif len(desc) >= 2 and looks_like_header(desc[-2]) and looks_like_header(desc[-1]):
                    nxt_hdr = 2
                else:
                    nxt_hdr = 1
                nxt_hdr = min(nxt_hdr, len(desc))
                pending = desc[len(desc) - nxt_hdr:]
                desc = desc[:len(desc) - nxt_hdr]
                if len(pending) == 3 and DURATION_ONLY.match(pending[1]):
                    company = pending[0]
                    pending = pending[2:]
            else:
                pending = []
            role["_raw"] = desc
            role["bullets"] = [BULLET_START.sub("", d).strip() for d in desc]
            roles.append(role)
            continue
        if DURATION_ONLY.match(ln):
            # multi-role company header: the previous line is the company
            company = pending[-1] if pending else company
            pending = []
            i += 1
            continue
        pending.append(ln)
        i += 1
    return roles


def parse_education(lines):
    out, buf = [], []
    for ln in lines + [None]:
        if ln is None or (buf and re.search(r"\((?:\d{4})?\s*[-–]?\s*(?:\d{4})?\)$", ln) and len(buf) >= 1):
            if ln is not None:
                buf.append(ln)
            if buf:
                inst = buf[0]
                rest = " ".join(buf[1:])
                yrs = re.search(r"\((\d{4})?\s*[-–]?\s*(\d{4})?\)", rest)
                degree_field = re.sub(r"\s*\([^)]*\)\s*$", "", rest).strip(" ·,")
                parts = [p.strip(" ·,") for p in re.split(r"\s+·\s+|,\s+", degree_field, maxsplit=1)]
                y1, y2 = (yrs.group(1), yrs.group(2)) if yrs else (None, None)
                if y1 and not y2 and "-" not in (yrs.group(0) if yrs else "") and "–" not in (yrs.group(0) if yrs else ""):
                    y1, y2 = None, y1      # "(2004)" is the graduation year
                out.append({"institution": inst,
                            "degree": parts[0] if parts and parts[0] else None,
                            "field": parts[1] if len(parts) > 1 else None,
                            "start": y1, "end": y2, "notes": None})
            buf = []
            continue
        buf.append(ln)
    return out


def parse_contact(lines):
    c = {"email": None, "phone": None, "links": []}
    joined = []
    for ln in lines:   # LinkedIn wraps long URLs: "www.linkedin.com/in/firstname-" / "lastname (LinkedIn)"
        if joined and re.search(r"(linkedin\.com/in/|https?://|www\.)\S*$", joined[-1]) and not re.search(r"\(\w+\)$", joined[-1]):
            joined[-1] += ln
        else:
            joined.append(ln)
    for ln in joined:
        if "@" in ln and c["email"] is None:
            c["email"] = ln.split()[0]
        elif re.search(r"linkedin\.com/in/", ln):
            url = re.search(r"\S*linkedin\.com/in/\S+", ln).group(0).rstrip(")")
            c["links"].append({"label": "LinkedIn", "url": "https://" + url if not url.startswith("http") else url})
        elif re.search(r"\(\s*(Personal|Company|Portfolio|Blog|Other)\s*\)", ln):
            url = ln.split()[0]
            c["links"].append({"label": re.search(r"\((\w+)\)", ln).group(1), "url": url if url.startswith("http") else "https://" + url})
        elif re.fullmatch(r"[+\d][\d\s()-]{6,}(?:\s*\(\w+\))?", ln):
            c["phone"] = re.sub(r"\s*\(\w+\)$", "", ln)
    return c


def parse_certs(lines):
    # LinkedIn lists one certification name per line (long names wrap onto a second line — heuristic join)
    out = []
    for ln in lines:
        if out and (ln[:1].islower() or len(ln) < 12):
            out[-1]["name"] += " " + ln
        else:
            out.append({"name": ln, "issuer": None, "year": None, "url": None})
    return out


LEVELS = {"native or bilingual": "Native", "full professional": "C1", "professional working": "B2",
          "limited working": "B1", "elementary": "A2",
          "muttersprache oder zweisprachig": "Native", "verhandlungssicher": "C1", "fließend": "B2",
          "gute kenntnisse": "B1", "grundkenntnisse": "A2",
          "ojczysty lub dwujęzyczny": "Native", "pełna biegłość zawodowa": "C1",
          "biegłość zawodowa": "B2", "ograniczona biegłość": "B1", "podstawowy": "A2"}


def parse_languages(lines):
    out = []
    for ln in lines:
        m = re.match(r"^(.*?)\s*\((.*)\)$", ln)
        lang = m.group(1) if m else ln
        lvl = m.group(2) if m else None
        out.append({"language": lang, "level": LEVELS.get((lvl or "").strip().lower(), lvl)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    sidebar, main = [], []
    with pdfplumber.open(str(args.pdf)) as doc:
        split_x = find_split_x(doc.pages[0])
        for pno, page in enumerate(doc.pages, 1):
            s, m = split_page(page, split_x)
            sidebar += s
            main += m

    txt = ["# SIDEBAR", *sidebar, "", "# MAIN", *main]
    (args.out_dir / "linkedin.txt").write_text("\n".join(txt), encoding="utf-8")

    side = sections_from(sidebar, SIDEBAR_HEADINGS)
    body = sections_from(main, MAIN_HEADINGS)
    pre = body.get("_pre", [])
    name = pre[0] if pre else None
    location = pre[-1] if len(pre) > 2 else None
    headline = " ".join(pre[1:-1]) if len(pre) > 2 else (pre[1] if len(pre) > 1 else None)
    contact = parse_contact(side.get("Contact", []))

    draft = {
        "meta": {"version": 1, "source": "linkedin-pdf", "updated": None, "target": None,
                 "_note": "Heuristic draft. Verify every field against linkedin.txt before use."},
        "basics": {"name": name, "headline": headline, "location": location,
                   "email": contact["email"], "phone": contact["phone"], "links": contact["links"], "photo": None},
        "summary": "\n".join(unwrap(body.get("Summary", []))) or None,
        "experience": [{k: v for k, v in r.items()} for r in parse_experience(unwrap(body.get("Experience", [])))],
        "earlier_experience": None,
        "skills": [{"group": "Top skills (LinkedIn)", "items": side.get("Top Skills", [])}],
        "education": parse_education(body.get("Education", [])),
        "certifications": parse_certs(side.get("Certifications", [])),
        "languages": parse_languages(side.get("Languages", [])),
        "projects": [], "publications": [],
        "footer": {"consent": None},
    }
    for r in draft["experience"]:
        r["summary"] = None
        r["tech"] = []
        r["hidden"] = False
    (args.out_dir / "linkedin-draft.yaml").write_text(
        yaml.safe_dump(draft, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")

    # What the export cannot tell us, and what looks inconsistent — the question round should cover these.
    missing = [k for k in ("email", "phone") if not draft["basics"].get(k)]
    hints = []
    starts = [r["start"] for r in draft["experience"] if r.get("start")]
    yrs = re.search(r"(\d{2})\+?\s*(?:years|yrs|lat|Jahre)", draft["summary"] or "")
    if yrs and starts:
        earliest = min(int(str(s)[:4]) for s in starts)
        claimed = int(yrs.group(1))
        from datetime import date as _d
        if abs((_d.today().year - earliest) - claimed) >= 2:
            hints.append(f"summary claims {claimed} years; earliest listed role starts {earliest} "
                         f"({_d.today().year - earliest} years) — ask which is right and why")
    loc = (draft["basics"].get("location") or "").split(",")[0].split()[0] if draft["basics"].get("location") else ""
    role_locs = [r.get("location") or "" for r in draft["experience"]]
    if loc and role_locs and not any(loc.lower() in rl.lower() for rl in role_locs if rl):
        hints.append(f"profile location '{draft['basics']['location']}' matches none of the role locations "
                     f"{[rl for rl in role_locs if rl]} — ask which location to show")
    for r in draft["experience"]:
        if not r["bullets"]:
            hints.append(f"role '{r['title']}' at {r['company']} has no description — ask for 1–3 facts")
    if any("linkedin.com/in/" in l["url"] for l in draft["basics"]["links"]):
        hints.append("LinkedIn wraps URLs in the export — confirm the profile URL with the candidate")

    print(json.dumps({
        "txt": str(args.out_dir / "linkedin.txt"),
        "missing_contact": missing,
        "hints": hints,
        "draft": str(args.out_dir / "linkedin-draft.yaml"),
        "name": name, "roles_found": len(draft["experience"]),
        "sidebar_sections": [k for k in side if k != "_pre"],
        "main_sections": [k for k in body if k != "_pre"],
        "split_detected": split_x is not None,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
