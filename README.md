# cv-designer

A Claude skill that turns a LinkedIn profile export into a tailored, machine-readable CV as a
single-column A4 PDF — and a small Python pipeline you can also run on its own.

![Example CV rendered by the skill](examples/sample-cv.png)

## What it does

1. **Reads a LinkedIn "Save to PDF" export** and separates the sidebar (contact, skills, languages)
   from the main column so the two-column first page doesn't interleave. Produces a text dump and a
   heuristic draft, then Claude writes a complete, untrimmed `cv-master.yaml` — the single source of
   truth the candidate keeps and hands back next time.
2. **Asks for what the export cannot contain** — email, phone, a confirmation of the profile URL, and
   any inconsistency the extractor spots (years claimed vs. dated roles, profile location vs. role
   locations).
3. **Tailors to a job posting** (URL or pasted text) through a written protocol: requirements table →
   evidence map → strategy (headline, summary angle, expand/compress/hide per role, skills order) →
   rewrite. Every bullet must trace to the master; nothing is invented. Output includes a
   `tailoring-report.md` with requirement coverage and an honest-gaps list.
4. **Renders** the YAML through a fixed HTML/CSS template with headless Chromium: Inter embedded,
   A4, two pages max, optional photo, optional consent footer (Polish employers). Auto-fits density
   within a small range and warns about headlines and role headers that will wrap.
5. **Verifies** the PDF before delivery: page count, text layer, no private-use glyphs, words intact
   under pdfminer, standard section order, embedded fonts, metadata, no hidden/tiny/white text, link
   annotations, file size.

The design is deliberately plain — one typeface, one muted accent, hairlines, whitespace. Machine
readability drove several choices you might not expect: no two-column layout, mixed-case section
headings (uppercase + tracking splits under pdfminer), no OpenType numeral variants (they extract
as private-use glyphs), and the *hinted* Inter build (the unhinted web build makes pdfminer split
words after every "t" in the 500/600 weights).

## Installing the skill

A skill is just a folder with a `SKILL.md` in it. Claude.ai takes it as a zip whose root is that
folder; Claude Code takes the folder itself.

**Claude.ai (web / desktop / Cowork):** go to **Customize → Skills** (https://claude.ai/customize/skills)
and upload `dist/cv-designer.zip`. To rebuild the zip after editing the skill:

```bash
zip -r dist/cv-designer.zip cv-designer -x '*/__pycache__/*' -x '*/evals/*'
```

**Claude Code:** copy `cv-designer/` into `~/.claude/skills/` (or a project's `.claude/skills/`).

Then say something like *"Here's my LinkedIn export and a job posting URL — make me a CV"*.

## Running the pipeline without Claude

The scripts are plain Python and don't need the model; only the writing and tailoring steps do.

```bash
pip install -r requirements.txt
python -m playwright install chromium          # once
sudo apt install poppler-utils                 # pdftoppm / pdffonts (brew install poppler on macOS)

# 1. LinkedIn export → text + draft YAML
python cv-designer/scripts/extract_linkedin.py --pdf Profile.pdf --out-dir work/

# 2. Edit work/linkedin-draft.yaml into cv-master.yaml (schema: cv-designer/assets/example-cv.yaml)

# 3. Optional photo
python cv-designer/scripts/prepare_photo.py --in IMG_1234.jpg --out work/photo.jpg

# 4. Render
python cv-designer/scripts/render_cv.py --data cv-master.yaml --out work/My-Name-CV.pdf \
    --photo work/photo.jpg --auto-fit --preview-dir work/previews

# 5. Check
python cv-designer/scripts/check_pdf.py --pdf work/My-Name-CV.pdf --data cv-master.yaml
```

`examples/` has a synthetic `sample-cv.yaml` and its rendered PDF.

## Layout of this repository

```
cv-designer/            the skill — installable as-is
  SKILL.md              workflow the model follows
  references/           tailoring protocol, writing rules, design spec
  scripts/              extract_linkedin.py, prepare_photo.py, render_cv.py, check_pdf.py
  assets/               template.html, style.css, example-cv.yaml, fonts/ (Inter, OFL)
  evals/evals.json      test prompts and assertions used during development
examples/               synthetic sample: YAML → PDF → PNG
dist/cv-designer.zip    the skill packaged for upload to Claude.ai
```

## Evaluation

The skill was developed with skill-creator's eval loop: three test cases (LinkedIn export + posting
with photo; export only, general CV; existing master + posting), each run with and without the skill.
Final iteration: skill runs passed 100% of 71 assertions, baseline runs 86%. The assertions that
separated them were machine-readability (word integrity under pdfminer, standard headings, no
placeholders), the reusable master file, and the tailoring report with honest gaps.

Test inputs are a real person's data and are not in the repository.

## Licence

MIT for the code and documentation. Inter is bundled under the SIL Open Font License 1.1
(`cv-designer/assets/fonts/LICENSE-Inter.txt`).
