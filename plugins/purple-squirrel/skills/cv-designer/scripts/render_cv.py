#!/usr/bin/env python3
"""
Render a cv YAML file to a single-column A4 PDF (plus optional HTML and PNG previews).

    python render_cv.py --data cv-tailored.yaml --out out/Anna-Lindqvist-CV.pdf \
        [--photo photo.jpg] [--design nordic] [--accent "#4a6b7c"] [--max-pages 2] [--auto-fit] \
        [--html-out out/cv.html] [--preview-dir out/previews]

Exit codes: 0 ok · 2 page count exceeds --max-pages after auto-fit (trim content and re-run) · 1 error.
Prints a JSON summary on the last line (pages, base_pt, last_page_fill, paths).
"""
import argparse
import base64
import json
import mimetypes
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
FONT_DIR = ASSETS / "fonts"
DESIGNS = HERE.parent / "designs"
DEFAULT_DESIGN = "nordic"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ---------- Jinja filters ----------

def fmt_date(v):
    """2021-03 -> 'Mar 2021'; 2021 -> '2021'; 'present'/None -> 'Present'."""
    if v is None:
        return "Present"
    s = str(v).strip()
    if s.lower() in ("present", "now", "current", ""):
        return "Present"
    m = re.fullmatch(r"(\d{4})-(\d{1,2})(?:-\d{1,2})?", s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return f"{MONTHS[mo - 1]} {y}"
    if re.fullmatch(r"\d{4}", s):
        return s
    return s  # leave unknown formats untouched rather than fail


def short_url(u):
    """https://www.linkedin.com/in/anna/ -> linkedin.com/in/anna"""
    s = re.sub(r"^https?://", "", str(u)).rstrip("/")
    s = re.sub(r"^www\.", "", s)
    return s


# ---------- helpers ----------

def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    if path.suffix == ".woff2":
        mime = "font/woff2"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def font_faces() -> str:
    faces = [
        ("Inter-Regular.woff2", 400, "normal"),
        ("Inter-Italic.woff2", 400, "italic"),
        ("Inter-Medium.woff2", 500, "normal"),
        ("Inter-SemiBold.woff2", 600, "normal"),
        ("Inter-Bold.woff2", 700, "normal"),
    ]
    out = []
    for fname, weight, style in faces:
        p = FONT_DIR / fname
        if not p.exists():
            continue
        out.append(
            f"@font-face{{font-family:'Inter';font-weight:{weight};font-style:{style};"
            f"font-display:block;src:url({data_uri(p)}) format('woff2');}}"
        )
    return "\n".join(out)


def load_data(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    basics = data.get("basics") or {}
    for k in ("name", "headline"):
        if not basics.get(k):
            sys.exit(f"error: basics.{k} is required")
    for role in data.get("experience") or []:
        role.setdefault("hidden", False)
        role.setdefault("bullets", [])
        role.setdefault("tech", [])
    data.setdefault("skills", [])
    data.setdefault("education", [])
    data.setdefault("certifications", [])
    data.setdefault("languages", [])
    data.setdefault("projects", [])
    data.setdefault("publications", [])
    data.setdefault("footer", {}) or {}
    return data


def resolve_design(arg: str) -> Path:
    """Name -> designs/<name>; existing directory path -> used as-is (side-loaded designs)."""
    arg = str(arg)
    cand = Path(arg)
    if cand.is_dir():
        d = cand
    elif "/" in arg or "\\" in arg:
        sys.exit(f"error: design directory not found: {arg}")
    else:
        d = DESIGNS / arg
        if not d.is_dir():
            if not DESIGNS.is_dir():
                sys.exit(f"error: designs directory missing: {DESIGNS}")
            names = sorted(p.name for p in DESIGNS.iterdir() if p.is_dir() and not p.name.startswith("_"))
            sys.exit(f"error: unknown design '{arg}'. Available: {', '.join(names)}")
    missing = [f for f in ("template.html", "style.css") if not (d / f).exists()]
    if missing:
        sys.exit(f"error: design '{d}' is missing {', '.join(missing)}")
    return d


def build_html(data: dict, base_pt: float, accent: str, photo: Path | None, design_dir: Path) -> str:
    env = Environment(loader=FileSystemLoader(str(design_dir)), autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters["fmt_date"] = fmt_date
    env.filters["short_url"] = short_url
    tpl = env.get_template("template.html")
    from markupsafe import Markup
    return tpl.render(
        **data,
        css=Markup((design_dir / "style.css").read_text(encoding="utf-8")),  # raw CSS: autoescape would break quotes
        font_faces=Markup(font_faces()),
        base_pt=base_pt,
        accent=accent,
        photo_data_uri=data_uri(photo) if photo else None,
    )


def html_to_pdf(html: str, out_pdf: Path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.pdf(path=str(out_pdf), format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()


def set_metadata(pdf: Path, data: dict):
    from pypdf import PdfReader, PdfWriter
    basics = data["basics"]
    keywords = []
    for g in data.get("skills") or []:
        keywords.extend(g.get("items") or [])
    reader = PdfReader(str(pdf))
    writer = PdfWriter()
    for pg in reader.pages:
        writer.add_page(pg)
    writer.add_metadata({
        "/Title": f"{basics['name']} – CV",
        "/Author": basics["name"],
        "/Subject": basics.get("headline", ""),
        "/Keywords": ", ".join(keywords[:40]),
        "/Creator": "cv-designer",
    })
    # keep link annotations & outlines from the reader
    with open(pdf, "wb") as fh:
        writer.write(fh)


def page_stats(pdf: Path):
    import pdfplumber
    with pdfplumber.open(str(pdf)) as doc:
        n = len(doc.pages)
        last = doc.pages[-1]
        chars = last.chars
        fill = (max(c["bottom"] for c in chars) / last.height) if chars else 0.0
    return n, round(fill, 2)


def make_previews(pdf: Path, out_dir: Path, dpi: int = 100):
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("page-*.png"):
        f.unlink()
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(out_dir / "page")], check=True)
    return sorted(out_dir.glob("page-*.png"))


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="output PDF path")
    ap.add_argument("--photo", type=Path, help="prepared square JPEG; overrides basics.photo")
    ap.add_argument("--design", help="design name under designs/ or a path to a design directory (default: YAML 'design:' key, else 'nordic')")
    ap.add_argument("--accent", default="#4a6b7c")
    ap.add_argument("--base-pt", type=float, default=10.0, help="body font size in pt (1rem)")
    ap.add_argument("--max-pages", type=int, default=2)
    ap.add_argument("--auto-fit", action="store_true", help="step base-pt down to 9.2 until it fits max-pages")
    ap.add_argument("--html-out", type=Path)
    ap.add_argument("--preview-dir", type=Path)
    args = ap.parse_args()

    data = load_data(args.data)
    design_dir = resolve_design(args.design or data.get("design") or DEFAULT_DESIGN)
    photo = args.photo or (Path(data["basics"]["photo"]) if data["basics"].get("photo") else None)
    if photo and not photo.is_absolute():
        photo = (args.data.parent / photo) if not photo.exists() else photo
    if photo and not photo.exists():
        sys.exit(f"error: photo not found: {photo}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    sizes = [args.base_pt]
    if args.auto_fit:
        sizes = [s for s in (args.base_pt, 9.6, 9.2) if s <= args.base_pt] or [args.base_pt]
        sizes = sorted(set(sizes), reverse=True)

    # Auto-fit policy: prefer the largest density that (a) fits max_pages and (b) does not leave a
    # nearly empty last page. A spill of a few lines onto a new page is the most common defect, and a
    # small density step usually cures it without the author having to cut content.
    attempts = []
    for base_pt in sizes:
        html = build_html(data, base_pt, args.accent, photo, design_dir)
        html_to_pdf(html, args.out)
        pages, fill = page_stats(args.out)
        attempts.append((base_pt, pages, fill, html))
        if pages <= args.max_pages and not (pages > 1 and fill < 0.15):
            break

    fitting = [a for a in attempts if a[1] <= args.max_pages]
    if fitting:
        # fewest pages wins; among equals, the largest type
        best = sorted(fitting, key=lambda a: (a[1], -a[0]))[0]
    else:
        best = attempts[-1]
    used, pages, fill, html = best
    if best is not attempts[-1]:
        html_to_pdf(html, args.out)  # re-render the chosen variant
    density_note = None
    if used < sizes[0] and attempts[0][1] > pages:
        density_note = (f"Chose {used} pt to reach {pages} page(s); at {sizes[0]} pt the content spilled "
                        f"{int(attempts[0][2]*100)}% onto page {attempts[0][1]}. If you would rather keep {sizes[0]} pt, "
                        "trim roughly that many lines and re-render with --base-pt " + str(sizes[0]) + ".")

    set_metadata(args.out, data)
    if args.html_out:
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        args.html_out.write_text(html, encoding="utf-8")
    previews = make_previews(args.out, args.preview_dir) if args.preview_dir else []

    # Layout warnings the author should act on in the YAML (not the CSS)
    warnings = []
    if len(data["basics"].get("headline") or "") > 62:
        warnings.append(f"headline is {len(data['basics']['headline'])} chars and will likely wrap; keep it to one role phrase (~60 chars)")
    for role in data.get("experience") or []:
        if role.get("hidden"):
            continue
        hdr = len(role.get("title") or "") + len(role.get("company") or "") + len(role.get("location") or "")
        if hdr > 78:
            warnings.append(f"role header '{role.get('title')} — {role.get('company')}' is ~{hdr} chars and will wrap; "
                            "shorten the title or move the employer gloss into the one-liner")
    for g in data.get("skills") or []:
        long_items = [i for i in (g.get("items") or []) if len(str(i).split()) > 5]
        if long_items:
            warnings.append(f"skills group '{g.get('group')}' has sentence-length items: {long_items[:2]} — keep items to 1–4 words")

    summary = {
        "pdf": str(args.out),
        "design": design_dir.name,
        "warnings": warnings,
        "pages": pages,
        "max_pages": args.max_pages,
        "base_pt": used,
        "last_page_fill": fill,
        "previews": [str(p) for p in previews],
        "html": str(args.html_out) if args.html_out else None,
    }
    if density_note:
        summary["density_note"] = density_note
    if pages > args.max_pages:
        summary["status"] = "TOO_LONG"
        summary["hint"] = ("Content exceeds max pages even at the smallest allowed density. "
                           "Trim per references/writing-rules.md (cut order) and re-render.")
        print(json.dumps(summary, ensure_ascii=False))
        sys.exit(2)
    if pages == args.max_pages and fill is not None and fill < 0.3:
        summary["status"] = "OK_BUT_SPARSE_LAST_PAGE"
        summary["hint"] = (f"Last page is only {int(fill*100)}% used. Either trim to {pages-1} page(s) "
                           "or add substance — a nearly empty page reads as padding.")
    else:
        summary["status"] = "OK"
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
