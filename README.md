# cv-designer

[![Latest release](https://img.shields.io/github/v/release/kradecki/cv-designer)](https://github.com/kradecki/cv-designer/releases/latest)
[![Release build](https://github.com/kradecki/cv-designer/actions/workflows/release.yml/badge.svg)](https://github.com/kradecki/cv-designer/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A Claude skill that turns a LinkedIn profile export into a tailored, machine-readable CV as a
single-column A4 PDF — plus a small Python pipeline you can run on its own.

![Example CV rendered by the skill](examples/sample-cv.png)

## How it works

1. **Extract** — reads a LinkedIn "Save to PDF" export, separates the sidebar (contact, skills,
   languages) from the main column, and drafts `cv-master.yaml` — the single source of truth the
   candidate keeps and hands back next time.
2. **Complete** — asks for what the export cannot contain (email, phone, profile URL) and flags any
   inconsistency the extractor spots (years claimed vs. dated roles, location mismatches).
3. **Tailor** — matches the master against a job posting (URL or pasted text) through a written
   protocol: requirements table → evidence map → strategy → rewrite. Every bullet traces back to
   the master; nothing is invented. Ships a `tailoring-report.md` with requirement coverage and an
   honest-gaps list.
4. **Render** — YAML through a fixed HTML/CSS template with headless Chromium: Inter embedded, A4,
   two pages max, optional photo, optional consent footer (Polish employers). Auto-fits density and
   warns about headlines and role headers that will wrap.
5. **Verify** — checks the PDF before delivery: page count, text layer, word integrity under
   pdfminer, standard section order, embedded fonts, metadata, no hidden/tiny/white text, link
   annotations, file size.

The design is deliberately plain — one typeface, one muted accent, hairlines, whitespace. Machine
readability drove choices you might not expect: no two-column layout, mixed-case section headings
(uppercase + tracking splits under pdfminer), no OpenType numeral variants (they extract as
private-use glyphs), and the *hinted* Inter build (the unhinted web build makes pdfminer split
words after every "t" in the 500/600 weights).

## Installation

This repository is a Claude plugin marketplace — one install flow everywhere.

**Claude Code:**

```bash
claude plugin marketplace add kradecki/cv-designer
claude plugin install cv-designer@cv-designer
```

or in-session: `/plugin install cv-designer@cv-designer`.

**Claude.ai / Claude Desktop:** go to **Customize → Plugins → Add → Add marketplace**, enter
`kradecki/cv-designer`, then add the **cv-designer** plugin. Enable *Sync automatically* to pick up
updates.

**Manual fallback:** download `cv-designer.zip` from the
[latest release](https://github.com/kradecki/cv-designer/releases/latest) and upload it at
**Customize → Skills**, or copy `plugins/cv-designer/skills/cv-designer/` into `~/.claude/skills/`.

Then say something like *"Here's my LinkedIn export and a job posting URL — make me a CV."*

## Running the pipeline without Claude

The scripts are plain Python and don't need the model; only the writing and tailoring steps do.

```bash
pip install -r requirements.txt
python -m playwright install chromium          # once
sudo apt install poppler-utils                 # pdftoppm / pdffonts (brew install poppler on macOS)

SKILL=plugins/cv-designer/skills/cv-designer

# 1. LinkedIn export → text + draft YAML
python $SKILL/scripts/extract_linkedin.py --pdf Profile.pdf --out-dir work/

# 2. Edit work/linkedin-draft.yaml into cv-master.yaml (schema: $SKILL/assets/example-cv.yaml)

# 3. Optional photo
python $SKILL/scripts/prepare_photo.py --in IMG_1234.jpg --out work/photo.jpg

# 4. Render
python $SKILL/scripts/render_cv.py --data cv-master.yaml --out work/My-Name-CV.pdf \
    --photo work/photo.jpg --auto-fit --preview-dir work/previews

# 5. Check
python $SKILL/scripts/check_pdf.py --pdf work/My-Name-CV.pdf --data cv-master.yaml
```

`examples/` has a synthetic `sample-cv.yaml` and its rendered PDF.

## Repository layout

```
.claude-plugin/           marketplace.json — the repo is its own marketplace
plugins/cv-designer/      the plugin (.claude-plugin/plugin.json)
  skills/cv-designer/     the skill
    SKILL.md              workflow the model follows
    references/           tailoring protocol, writing rules, design spec
    scripts/              extract_linkedin.py, prepare_photo.py, render_cv.py, check_pdf.py
    assets/               template.html, style.css, example-cv.yaml, fonts/ (Inter, OFL)
    evals/evals.json      test prompts and assertions used during development
examples/                 synthetic sample: YAML → PDF → PNG
```

## Releases

Pushing a tag `vX.Y.Z` triggers CI, which builds `cv-designer.zip` and attaches it to a GitHub
release — the zip is never committed to the repository. Marketplace installs track the repo
directly; the release zip is the manual-upload fallback.

```bash
git tag v0.2.0 && git push origin v0.2.0
```

## Evaluation

Developed with skill-creator's eval loop: three test cases (export + posting with photo; export
only; existing master + posting), each run with and without the skill. Final iteration: skill runs
passed 100% of 71 assertions, baseline 86%. The gap came from machine-readability (word integrity
under pdfminer, standard headings, no placeholders), the reusable master file, and the tailoring
report with honest gaps. Test inputs are a real person's data and are not in the repository.

## Contributing

Issues and pull requests welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT for the code and documentation. Inter is bundled under the SIL Open Font License 1.1
(`plugins/cv-designer/skills/cv-designer/assets/fonts/LICENSE-Inter.txt`).
