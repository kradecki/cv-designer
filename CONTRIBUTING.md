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
python cv-designer/scripts/render_cv.py --data examples/sample-cv.yaml --out /tmp/sample.pdf
python cv-designer/scripts/check_pdf.py --pdf /tmp/sample.pdf --data examples/sample-cv.yaml
```

## Guidelines

- **Never commit personal data.** Test with synthetic profiles only; `cv-work/`, `work/`, and
  `evals/files/` are gitignored for a reason.
- **Machine readability is a hard constraint.** Any change to the template, CSS, or fonts must
  still pass `check_pdf.py` (word integrity under pdfminer, embedded fonts, no private-use glyphs).
- **Skill changes**: edit `cv-designer/SKILL.md` or `references/`; keep instructions testable
  against `cv-designer/evals/evals.json`.
- **Update the README** when behavior, installation, or layout changes — it ships with every
  release.

## Testing the skill locally

Copy `cv-designer/` into `~/.claude/skills/` and exercise it in Claude Code, or build a zip for
Claude.ai:

```bash
zip -r cv-designer.zip cv-designer -x '*/__pycache__/*' -x '*/evals/*'
```

## Releases

Maintainers cut releases by pushing a tag; CI builds and attaches the zip:

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```
