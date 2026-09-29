# Contributing

Thanks for your interest in improving cv-designer.

## Getting started

```bash
pip install -r requirements.txt
python -m playwright install chromium
# poppler-utils for pdftoppm / pdffonts (brew install poppler on macOS)
```

Render the synthetic example to confirm your setup:

```bash
SKILL=plugins/cv-designer/skills/cv-designer
python $SKILL/scripts/render_cv.py --data examples/sample-cv.yaml --out /tmp/sample.pdf
python $SKILL/scripts/check_pdf.py --pdf /tmp/sample.pdf --data examples/sample-cv.yaml
```

## Guidelines

- **Never commit personal data.** Test with synthetic profiles only; `cv-work/`, `work/`, and
  `evals/files/` are gitignored for a reason.
- **Machine readability is a hard constraint.** Any change to the template, CSS, or fonts must
  still pass `check_pdf.py` (word integrity under pdfminer, embedded fonts, no private-use glyphs).
- **Skill changes**: edit `plugins/cv-designer/skills/cv-designer/SKILL.md` or its `references/`;
  keep instructions testable against the skill's `evals/evals.json`.
- **Update the README** when behavior, installation, or layout changes — it ships with every
  release.

## Testing the skill locally

Install your working copy as a plugin from the local marketplace:

```bash
claude plugin marketplace add /path/to/cv-designer
claude plugin install cv-designer@cv-designer
```

Or copy `plugins/cv-designer/skills/cv-designer/` into `~/.claude/skills/`, or build a zip for
Claude.ai:

```bash
cd plugins/cv-designer/skills && zip -r ../../../cv-designer.zip cv-designer -x '*/__pycache__/*' -x '*/evals/*'
```

Validate plugin metadata before pushing:

```bash
claude plugin validate .
```

## Contributing a design

Copy `plugins/cv-designer/skills/cv-designer/designs/_template/` to `designs/<your-name>/` and
follow its [README](plugins/cv-designer/skills/cv-designer/designs/_template/README.md) — it
carries the full contract (headings, rem sizing, fonts, forbidden patterns), the test loop, and
the preview.png requirement. CI must be green: every design is rendered (plain + photo) and
checked with `check_pdf.py` on each PR.

## Releases

Maintainers cut releases by pushing a tag; CI builds and attaches the zip:

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```
