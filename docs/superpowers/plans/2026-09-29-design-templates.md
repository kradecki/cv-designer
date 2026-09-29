# Design Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the CV design layer pluggable: current look becomes `designs/nordic`, a `_template` scaffold + authoring guide defines the contract, CI renders and machine-readability-checks every design on every push/PR.

**Architecture:** Convention over registry. A design is a directory (`template.html`, `style.css`, `design.json`, `preview.png`) inside the skill at `designs/<name>`. `render_cv.py --design <name-or-path>` resolves it (name → `designs/`, path → as-is, enabling side-loaded zips in claude.ai); fonts, filters, auto-fit, accent and `check_pdf.py` stay shared machinery. A GitHub Actions workflow renders `assets/example-cv.yaml` with every design (plain + synthetic photo) and fails if any `check_pdf.py` check fails.

**Tech Stack:** Python 3 (Jinja2, Playwright/Chromium, pdfplumber, pdfminer, pypdf, Pillow, PyYAML), poppler-utils, GitHub Actions. No test framework exists in this repo; verification is running the pipeline scripts and asserting on their output/exit codes — keep it that way.

**Spec:** `docs/superpowers/specs/2026-09-29-design-templates-design.md`

## Global Constraints

- Skill root (all paths below relative to it unless noted): `plugins/cv-designer/skills/cv-designer/`.
- Design dir contract: MUST contain `template.html` + `style.css`; official (in-repo) designs also `design.json` (`name`, `description`, `author`) + `preview.png`. `design.json`/`preview.png` are NOT required to render (side-loaded dirs may lack them).
- Default design name: `nordic`. Precedence: `--design` flag > top-level `design:` key in the YAML > `nordic`.
- Directories starting with `_` under `designs/` are never listed as available and are skipped by CI.
- Fonts: shared hinted Inter via `font_faces()` only; designs must not add `@font-face`.
- Standard heading text/order (from `check_pdf.py` `HEADING_ORDER`): `Summary, Experience, Skills, Selected projects, Education, Certifications, Publications & talks, Languages`.
- Every commit leaves the repo green: `render_cv.py` + `check_pdf.py` run clean on `assets/example-cv.yaml` at that commit.
- Commit messages: concise, end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Working dir for throwaway outputs: use `/tmp/cvd-plan/` (never commit it).
- This repo commits directly to `main` (no PR flow yet); push after each task.

## Review Focus

Spec-implied failure modes; each line's pinning test is added to the owning task:

1. YAML `design: <unknown>` (no flag) → must exit 1 listing available names, not stack-trace. (Task 1, step 6)
2. `--design` given a path whose dir exists but lacks `style.css` → named-file error, exit 1. (Task 1, step 6)
3. `_template` leaking: listed in the "available designs" error, or run by CI. (Task 1 step 6; Task 4 step 2 glob)
4. Side-loaded dir without `design.json` must still render + pass checks (design.json is list-time only). (Task 1, step 7)
5. A design whose template drops the photo block silently ships photo-less CVs → CI photo-variant must assert an image is embedded on page 1. (Task 4, step 2)

---

### Task 1: Renderer `--design` + move current design to `designs/nordic`

**Files:**
- Move (git mv): `assets/template.html` → `designs/nordic/template.html`; `assets/style.css` → `designs/nordic/style.css`
- Create: `designs/nordic/design.json`
- Modify: `scripts/render_cv.py` (lines 26-28, 108-121, 178-197, 253-262), `scripts/check_pdf.py:71`
- (All paths relative to `plugins/cv-designer/skills/cv-designer/`)

**Interfaces:**
- Consumes: existing `build_html(data, base_pt, accent, photo)`, `ASSETS` constant.
- Produces: `resolve_design(arg: str) -> Path` (exits 1 with message on error); `build_html(data, base_pt, accent, photo, design_dir: Path) -> str`; CLI `--design <name-or-path>` (default resolves to `nordic`); YAML top-level `design:` honored; render summary JSON gains `"design": "<resolved dir name>"`. Later tasks rely on: unknown-name error text starting `error: unknown design`, and `_`-prefixed dirs excluded from the available list.

- [ ] **Step 1: Move the design files and write the manifest**

```bash
cd plugins/cv-designer/skills/cv-designer
mkdir -p designs/nordic
git mv assets/template.html designs/nordic/template.html
git mv assets/style.css designs/nordic/style.css
```

Create `designs/nordic/design.json`:

```json
{
  "name": "nordic",
  "description": "Scandinavian restraint — single muted accent, hairline rules, Inter, lots of air. The original cv-designer look.",
  "author": "Krzysztof Radecki"
}
```

- [ ] **Step 2: Verify the renderer now fails (files moved, code not yet updated)**

Run: `python plugins/cv-designer/skills/cv-designer/scripts/render_cv.py --data plugins/cv-designer/skills/cv-designer/assets/example-cv.yaml --out /tmp/cvd-plan/t1.pdf`
Expected: FAIL (`TemplateNotFound: template.html` or missing style.css) — this is the failing state the code change must fix.

- [ ] **Step 3: Update `render_cv.py`**

Replace lines 26-28:

```python
HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
FONT_DIR = ASSETS / "fonts"
DESIGNS = HERE.parent / "designs"
DEFAULT_DESIGN = "nordic"
```

Add after `load_data` (before `build_html`):

```python
def resolve_design(arg: str) -> Path:
    """Name -> designs/<name>; existing directory path -> used as-is (side-loaded designs)."""
    cand = Path(arg)
    if cand.is_dir():
        d = cand
    elif "/" in arg or "\\" in arg:
        sys.exit(f"error: design directory not found: {arg}")
    else:
        d = DESIGNS / arg
        if not d.is_dir():
            names = sorted(p.name for p in DESIGNS.iterdir() if p.is_dir() and not p.name.startswith("_"))
            sys.exit(f"error: unknown design '{arg}'. Available: {', '.join(names)}")
    missing = [f for f in ("template.html", "style.css") if not (d / f).exists()]
    if missing:
        sys.exit(f"error: design '{d}' is missing {', '.join(missing)}")
    return d
```

Change `build_html` signature and body (lines 108-121) to take the design dir:

```python
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
```

In `main()`: add after the `--photo` argument (line 182):

```python
    ap.add_argument("--design", help="design name under designs/ or a path to a design directory (default: YAML 'design:' key, else 'nordic')")
```

After `data = load_data(args.data)` (line 191) add:

```python
    design_dir = resolve_design(args.design or data.get("design") or DEFAULT_DESIGN)
```

Change the render call (line 209) to `html = build_html(data, base_pt, args.accent, photo, design_dir)` and add `"design": design_dir.name,` to the `summary` dict (after `"pdf"`, line 254). Update the module docstring usage line (line 5-7) to include `[--design nordic]`.

Also `scripts/check_pdf.py:71`: change the hint `" — check font-variant settings in style.css"` to `" — check font-variant settings in the design's style.css"`.

- [ ] **Step 4: Verify default + explicit name + path form all render and pass checks**

```bash
cd plugins/cv-designer/skills/cv-designer
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cvd-plan/default.pdf --auto-fit
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cvd-plan/named.pdf --design nordic
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cvd-plan/path.pdf --design designs/nordic
python scripts/check_pdf.py --pdf /tmp/cvd-plan/default.pdf --data assets/example-cv.yaml
```

Expected: three renders exit 0, summary JSON contains `"design": "nordic"`; check_pdf prints `"ok": true`.

- [ ] **Step 5: Verify the YAML `design:` key and flag precedence**

```bash
python - <<'EOF'
import yaml, pathlib
d = yaml.safe_load(pathlib.Path("assets/example-cv.yaml").read_text())
d["design"] = "nordic"
pathlib.Path("/tmp/cvd-plan/with-key.yaml").write_text(yaml.safe_dump(d, allow_unicode=True))
EOF
python scripts/render_cv.py --data /tmp/cvd-plan/with-key.yaml --out /tmp/cvd-plan/key.pdf
```

Expected: exit 0, `"design": "nordic"`.

- [ ] **Step 6: Verify error paths (Review Focus 1-3)**

```bash
python - <<'EOF'
import yaml, pathlib
d = yaml.safe_load(pathlib.Path("assets/example-cv.yaml").read_text())
d["design"] = "does-not-exist"
pathlib.Path("/tmp/cvd-plan/bad-key.yaml").write_text(yaml.safe_dump(d, allow_unicode=True))
EOF
python scripts/render_cv.py --data /tmp/cvd-plan/bad-key.yaml --out /tmp/cvd-plan/x.pdf; echo "exit=$?"
mkdir -p /tmp/cvd-plan/broken-design && cp designs/nordic/template.html /tmp/cvd-plan/broken-design/
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cvd-plan/x.pdf --design /tmp/cvd-plan/broken-design; echo "exit=$?"
```

Expected: first → `error: unknown design 'does-not-exist'. Available: nordic` (list must NOT contain `_template` once it exists), exit=1. Second → `error: design '/tmp/cvd-plan/broken-design' is missing style.css`, exit=1.

- [ ] **Step 7: Verify a side-loaded dir without design.json renders (Review Focus 4)**

```bash
cp -r designs/nordic /tmp/cvd-plan/sideload && rm /tmp/cvd-plan/sideload/design.json
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cvd-plan/side.pdf --design /tmp/cvd-plan/sideload
python scripts/check_pdf.py --pdf /tmp/cvd-plan/side.pdf --data assets/example-cv.yaml
```

Expected: render exit 0, check `"ok": true`.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat: pluggable designs — nordic + render_cv --design (name or path)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push origin main
```

---

### Task 2: `designs/nordic/preview.png`

**Files:**
- Create: `designs/nordic/preview.png` (page 1, 100 dpi, from the repo-level synthetic sample)

**Interfaces:**
- Consumes: Task 1 renderer.
- Produces: the preview convention every design follows: page 1 of `examples/sample-cv.yaml` (repo root) rendered with that design, `pdftoppm -r 100`, file named exactly `preview.png`. Task 4 CI asserts the file exists; Task 6 README embeds it.

- [ ] **Step 1: Render the sample with nordic and extract page 1**

```bash
cd plugins/cv-designer/skills/cv-designer
python scripts/render_cv.py --data ../../../../examples/sample-cv.yaml --out /tmp/cvd-plan/nordic-sample.pdf --design nordic --auto-fit
pdftoppm -r 100 -png -f 1 -l 1 /tmp/cvd-plan/nordic-sample.pdf /tmp/cvd-plan/nordic-preview
mv /tmp/cvd-plan/nordic-preview-1.png designs/nordic/preview.png
```

(If pdftoppm names it `nordic-preview-01.png`, move that. If the sample photo isn't referenced by the YAML, the preview is photo-less — that's fine and consistent for all designs.)

- [ ] **Step 2: Verify with the image reader**

Read `designs/nordic/preview.png` — it must show the familiar page 1 (name, headline, Summary, Experience), not a blank or clipped page.

- [ ] **Step 3: Commit**

```bash
git add designs/nordic/preview.png && git commit -m "nordic preview.png (sample page 1, 100dpi)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push origin main
```

---

### Task 3: `designs/_template/` scaffold + authoring guide

**Files:**
- Create: `designs/_template/template.html`, `designs/_template/style.css`, `designs/_template/design.json`, `designs/_template/README.md`

**Interfaces:**
- Consumes: Task 1 contract (`resolve_design` accepts a path; `_` prefix excluded from listings).
- Produces: the scaffold creators copy; CONTRIBUTING (Task 6) links to `designs/_template/README.md`.

- [ ] **Step 1: Create the skeleton files**

`template.html`: copy of `designs/nordic/template.html` with this comment block inserted after line 1 (`<!doctype html>`):

```html
<!--
  cv-designer design template. Start here:
  1. cp -r designs/_template designs/<your-name>   (lowercase, hyphens)
  2. Edit style.css first — most designs need no template changes.
  3. Rules you MUST keep (CI enforces them via check_pdf.py):
     - the {{ font_faces }}, {{ css }}, base_pt and --accent lines in <style> stay as-is
     - section <h2> texts and their order stay exactly as in this file
     - single-column flow: text must extract top-to-bottom
     - keep the photo block and the consent footer block
  Full contract + test loop: designs/_template/README.md
-->
```

`style.css`: copy of `designs/nordic/style.css` with the header comment replaced by:

```css
/* <your-design-name> — your look, machine-readable by contract.
   Everything in rem: render_cv.py scales density via html{font-size} (--auto-fit).
   Never: fixed pt sizes, columns for body content, @font-face, images-as-text,
   font-variant-numeric (private-use glyphs break ATS extraction).
   Colours: define your palette here, but headings/accents key off var(--accent),
   which the renderer injects (--accent flag). */
```

`design.json`:

```json
{
  "name": "_template",
  "description": "Scaffold for new designs — copy this directory, do not use it directly.",
  "author": "you"
}
```

- [ ] **Step 2: Write `designs/_template/README.md`** — the authoring guide, with exactly these sections:

````markdown
# Creating a cv-designer design

A design is a folder: `template.html` + `style.css` + `design.json` + `preview.png`.
Copy this folder, restyle it, prove it machine-readable, open a PR.

## Quick start

```bash
cp -r designs/_template designs/my-design
# edit designs/my-design/style.css (and template.html if you must)
```

## The contract (CI-enforced)

Every rule exists because screening software reads the PDF before a human does.

| Rule | Why |
|---|---|
| Single-column body; text extracts top-to-bottom | two-column first pages interleave under pdfminer |
| Section headings: exact text and order `Summary, Experience, Skills, Selected projects, Education, Certifications, Publications & talks, Languages` (render only what the data has, ≥3) | `section_order` check; parsers key on standard headings |
| All sizes in `rem`; keep the `html { font-size: {{ base_pt }}pt }` line | `--auto-fit` steps density down to fit 2 pages |
| Accent only via `var(--accent)`; keep the `:root { --accent: {{ accent }} }` line | `--accent` flag must restyle any design |
| Keep `{{ font_faces }}` + `{{ css }}` in `<style>`; no own `@font-face` | the hinted Inter build is the one font proven not to split words under pdfminer |
| No `font-variant-numeric` / OpenType numeral variants | they extract as private-use glyphs (`unicode_text` check) |
| No skill bars, rating dots, tag pills, icon fonts, text-in-images | unverifiable, parse as noise (`words_intact` check) |
| Keep the photo block (`photo_data_uri`) and consent footer (`footer.consent`) | candidates opt in; CI renders a photo variant |
| A4 `@page`; sample data fits 2 pages with `--auto-fit` | `pages` check |

## Template context

Top-level YAML keys arrive as variables (schema + field lists: `assets/example-cv.yaml`):
`basics` (name, headline, location, email, phone, links, photo), `summary`,
`experience` (each: title, company, location, start, end, summary, bullets, tech, hidden),
`earlier_experience`, `skills` (group, items), `projects`, `education`, `certifications`,
`publications`, `languages`, `footer` (consent), `meta`.

Injected by the renderer: `css`, `font_faces`, `base_pt`, `accent`, `photo_data_uri`.
Filters: `fmt_date` (`2021-03` → `Mar 2021`), `short_url` (strips scheme/www).

## Test loop (from the skill root)

```bash
python scripts/render_cv.py --data assets/example-cv.yaml \
    --out /tmp/my-design.pdf --design designs/my-design --auto-fit --preview-dir /tmp/previews
python scripts/check_pdf.py --pdf /tmp/my-design.pdf --data assets/example-cv.yaml
```

Iterate until every check passes and the previews look right.

## Before the PR

1. Fill `design.json`: `name` (= folder name), one-line `description` (shown when Claude
   asks users to pick a design), `author`.
2. Generate the required `preview.png` (page 1 of the repo's synthetic sample, 100 dpi):

```bash
python scripts/render_cv.py --data ../../../../examples/sample-cv.yaml \
    --out /tmp/sample.pdf --design designs/my-design --auto-fit
pdftoppm -r 100 -png -f 1 -l 1 /tmp/sample.pdf /tmp/preview && mv /tmp/preview-1.png designs/my-design/preview.png
```

3. Add your design to the gallery table in the repo README.
4. CI re-renders every design (plain + photo) and blocks the PR if any check fails.
````

- [ ] **Step 3: Verify the skeleton itself renders and passes checks**

```bash
cd plugins/cv-designer/skills/cv-designer
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cvd-plan/tmpl.pdf --design designs/_template --auto-fit
python scripts/check_pdf.py --pdf /tmp/cvd-plan/tmpl.pdf --data assets/example-cv.yaml
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cvd-plan/x.pdf --design nope 2>&1 | grep -q "Available: nordic$" && echo "listing-ok"
```

Expected: render exit 0, `"ok": true`, and `listing-ok` (proves `_template` stays out of the available list — Review Focus 3).

- [ ] **Step 4: Commit**

```bash
git add designs/_template && git commit -m "designs/_template scaffold + authoring guide

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push origin main
```

---

### Task 4: CI — `check-designs.yml`

**Files:**
- Create: `.github/workflows/check-designs.yml` (repo root)

**Interfaces:**
- Consumes: Task 1 CLI, Task 2 preview convention, `_`-prefix exclusion.
- Produces: the merge gate. Runs on `push` to `main` and `pull_request`.

- [ ] **Step 1: Write the workflow**

```yaml
name: Check designs

on:
  push:
    branches: [main]
  pull_request:

jobs:
  check-designs:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: plugins/cv-designer/skills/cv-designer
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: |
          pip install -r ../../../../requirements.txt
          python -m playwright install --with-deps chromium
          sudo apt-get install -y poppler-utils

      - name: Synthetic photo
        run: |
          python -c "from PIL import Image; Image.new('RGB',(800,800),(120,140,160)).save('/tmp/ci-face.jpg')"
          python scripts/prepare_photo.py --in /tmp/ci-face.jpg --out /tmp/ci-photo.jpg

      - name: Render and check every design
        run: |
          set -e
          for d in designs/*/; do
            name=$(basename "$d")
            case "$name" in _*) continue;; esac
            echo "::group::$name"
            python -c "import json,sys; m=json.load(open('designs/$name/design.json')); assert m.get('name') and m.get('description'), 'design.json needs name+description'"
            test -f "designs/$name/preview.png" || { echo "designs/$name/preview.png missing (required)"; exit 1; }
            python scripts/render_cv.py --data assets/example-cv.yaml --out "/tmp/$name-plain.pdf" --design "$name" --auto-fit
            python scripts/check_pdf.py --pdf "/tmp/$name-plain.pdf" --data assets/example-cv.yaml
            python scripts/render_cv.py --data assets/example-cv.yaml --out "/tmp/$name-photo.pdf" --design "$name" --auto-fit --photo /tmp/ci-photo.jpg
            python scripts/check_pdf.py --pdf "/tmp/$name-photo.pdf" --data assets/example-cv.yaml
            python - "$name" <<'EOF'
          import sys, pdfplumber
          name = sys.argv[1]
          with pdfplumber.open(f"/tmp/{name}-photo.pdf") as doc:
              assert doc.pages[0].images, f"{name}: photo variant embeds no image on page 1"
          EOF
            echo "::endgroup::"
          done
```

(The heredoc pins Review Focus 5: a design that drops the photo block fails CI. Note: inside GitHub Actions `run:` blocks the heredoc body keeps the leading spaces shown; python tolerates them only if consistent — verify the step locally in Task 4 step 2 form before pushing, and if the heredoc misbehaves, write the four python lines to `/tmp/assert_photo.py` in the "Synthetic photo" step and call `python /tmp/assert_photo.py "$name"` instead.)

- [ ] **Step 2: Verify locally before pushing**

```bash
ruby -ryaml -e "YAML.load_file('.github/workflows/check-designs.yml'); puts 'yaml ok'"
# dry-run the loop body locally from the skill root:
cd plugins/cv-designer/skills/cv-designer
python -c "from PIL import Image; Image.new('RGB',(800,800),(120,140,160)).save('/tmp/ci-face.jpg')"
python scripts/prepare_photo.py --in /tmp/ci-face.jpg --out /tmp/ci-photo.jpg
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/nordic-photo.pdf --design nordic --auto-fit --photo /tmp/ci-photo.jpg
python scripts/check_pdf.py --pdf /tmp/nordic-photo.pdf --data assets/example-cv.yaml
python -c "import pdfplumber; doc=pdfplumber.open('/tmp/nordic-photo.pdf'); assert doc.pages[0].images"
ls designs/*/ | grep -v _template
```

Expected: `yaml ok`; photo render + check pass; image assertion passes; only `nordic` is a non-underscore design.

- [ ] **Step 3: Commit, push, watch the run**

```bash
git add .github/workflows/check-designs.yml && git commit -m "CI: render + check_pdf every design (plain + photo), preview/manifest required

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push origin main
gh run watch $(gh run list --workflow=check-designs.yml --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status
```

Expected: workflow green on main.

---

### Task 5: SKILL.md — design selection step + rewording

**Files:**
- Modify: `plugins/cv-designer/skills/cv-designer/SKILL.md` (lines 12, 140-165, 199-200, 206-217)

**Interfaces:**
- Consumes: Task 1 CLI + `design.json` descriptions.
- Produces: the conversational flow claude.ai users get.

- [ ] **Step 1: Edit SKILL.md**

Line 12, replace `The design is fixed and deliberate (see `references/design.md`).` with:

```
Each design is fixed and deliberate — the candidate picks a design from `designs/`, nothing is
tweaked per CV (see `references/design.md`).
```

In section "### 6. Render and review", insert before the ```bash render block:

```markdown
**Choose a design first.** In order: (1) the candidate named one → use it; (2) `cv-master.yaml`
has a `design:` key → use that saved preference; (3) otherwise read every `designs/*/design.json`
(skip `_`-prefixed), list `name — description` to the candidate, ask once, and write the choice
into `cv-master.yaml` as a top-level `design:` key. If the candidate uploads a design bundle
(zip), unzip it into the working directory and pass the directory to `--design`; say clearly the
design is unofficial and that delivery still requires every `check_pdf.py` check to pass. A
missing or malformed `design.json` only affects the listing: present such a design by its
directory name and mention the manifest problem.
```

In the render command block (line 143-146), add `--design <name-or-dir> \` after the `--photo` line.

Line 164-165, replace the sentence `Nothing else about the look is configurable per CV.` with
`Design choice and accent are the only look controls; nothing else is configurable per CV.`

Guardrail lines 199-200, replace with:

```markdown
- **Designs are not per-CV configurable.** Pick a design; structural changes go into that design's
  folder (or a new design) via PR so every future CV benefits, with `design.md` updated to match.
```

Reference map (line 206-217): add row `| Available designs + their one-liners | `designs/*/design.json` |` and row `| Create a new design | `designs/_template/README.md` |`.

- [ ] **Step 2: Verify**

```bash
grep -n "design:" plugins/cv-designer/skills/cv-designer/SKILL.md | head
grep -c "designs/" plugins/cv-designer/skills/cv-designer/SKILL.md
```

Expected: the new step and reference rows present; read the modified sections once end-to-end for flow.

- [ ] **Step 3: Commit**

```bash
git add plugins/cv-designer/skills/cv-designer/SKILL.md && git commit -m "SKILL.md: design selection step (ask once, save to master), uploaded-bundle flow

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push origin main
```

---

### Task 6: README gallery + CONTRIBUTING + design.md pointer

**Files:**
- Modify: `README.md` (repo root), `CONTRIBUTING.md` (repo root), `plugins/cv-designer/skills/cv-designer/references/design.md` (top)

**Interfaces:**
- Consumes: Task 2 preview, Task 3 guide path.
- Produces: user/creator-facing docs. Per project rule, README must reflect every layout/flow change in this plan.

- [ ] **Step 1: README — add a `## Designs` section** (after "How it works", before "Installation"):

```markdown
## Designs

Pick a look; every design passes the same machine-readability gate before it can merge.

| | |
|---|---|
| <img src="plugins/cv-designer/skills/cv-designer/designs/nordic/preview.png" width="260" alt="nordic design preview"> | **nordic** — Scandinavian restraint: single muted accent, hairline rules, Inter, lots of air. The default. |

Choose it in conversation ("use the nordic design"), save it in your `cv-master.yaml`
(`design: nordic`), or pass `--design nordic` to the renderer.

**Create your own:** copy `designs/_template/`, restyle, run the test loop, open a PR — the
[design authoring guide](plugins/cv-designer/skills/cv-designer/designs/_template/README.md)
has the full contract. CI renders every design against the sample CV and blocks anything that
breaks ATS extraction.
```

Also in README: update the "How it works" Render bullet `fixed HTML/CSS template` → `the chosen design's HTML/CSS template (see Designs)`; update the repository-layout block to show `designs/nordic/` and `designs/_template/` under the skill; update the pipeline `# 4. Render` command to include `--design nordic`.

- [ ] **Step 2: CONTRIBUTING — add section** (before "Releases"):

```markdown
## Contributing a design

Copy `plugins/cv-designer/skills/cv-designer/designs/_template/` to `designs/<your-name>/` and
follow its [README](plugins/cv-designer/skills/cv-designer/designs/_template/README.md) — it
carries the full contract (headings, rem sizing, fonts, forbidden patterns), the test loop, and
the preview.png requirement. CI must be green: every design is rendered (plain + photo) and
checked with `check_pdf.py` on each PR.
```

- [ ] **Step 3: design.md — scope note.** At the top of `references/design.md`, after the first heading, add:

```markdown
> This file is the rationale and review checklist for the **nordic** design and the general rules
> all designs share. Building a new design? Start at `designs/_template/README.md`.
```

- [ ] **Step 4: Verify all referenced paths exist**

```bash
for f in plugins/cv-designer/skills/cv-designer/designs/nordic/preview.png \
         plugins/cv-designer/skills/cv-designer/designs/_template/README.md; do
  test -e "$f" || echo "MISSING: $f"; done; echo done
grep -n "designs/" README.md CONTRIBUTING.md | head
```

Expected: `done` with no MISSING lines; README/CONTRIBUTING reference the new paths.

- [ ] **Step 5: Commit**

```bash
git add README.md CONTRIBUTING.md plugins/cv-designer/skills/cv-designer/references/design.md \
  && git commit -m "docs: Designs gallery, design-contribution guide links

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" && git push origin main
```

---

### Task 7: Release v0.3.0 + end-to-end verification

**Files:**
- None new (tag + verification only).

**Interfaces:**
- Consumes: everything above, both workflows.
- Produces: v0.3.0 release; updated installed plugin.

- [ ] **Step 1: Confirm both workflows green on main**

```bash
gh run list --limit 4
```

Expected: latest `Check designs` and any release runs green.

- [ ] **Step 2: Tag and push**

```bash
git tag v0.3.0 && git push origin v0.3.0
gh run watch $(gh run list --workflow=release.yml --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status
```

- [ ] **Step 3: Verify the release zip contains designs**

```bash
cd "$(mktemp -d)" && gh release download v0.3.0 -R kradecki/cv-designer -p cv-designer.zip
unzip -l cv-designer.zip | grep -E "designs/(nordic|_template)/" | head
```

Expected: `designs/nordic/{template.html,style.css,design.json,preview.png}` and `designs/_template/*` present in the zip (so claude.ai manual-upload users get designs too).

- [ ] **Step 4: Update the locally installed plugin and smoke-test**

```bash
claude plugin marketplace update cv-designer && claude plugin update cv-designer@cv-designer
find ~/.claude/plugins/cache/cv-designer -path "*designs/nordic/design.json" | head -1
```

Expected: plugin updated to the new commit; nordic design.json present in the cache.

- [ ] **Step 5: Commit nothing — update project memory instead.** Update
`~/.claude/projects/-Users-kradecki-development-git-private-cv-designer/memory/readme-per-iteration.md` “Current facts” with: designs live at `designs/<name>` inside the skill, default `nordic`, `--design` name-or-path, CI `check-designs.yml` gates designs, preview.png required.
