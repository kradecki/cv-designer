# Agent instructions — cv-designer

CV Designer: a Claude skill (plus standalone Python pipeline) that turns a LinkedIn export into a
tailored, machine-readable single-column A4 CV. This repo is also its own plugin marketplace.

## Map

- `.claude-plugin/marketplace.json` — marketplace; the plugin lives at `plugins/cv-designer/`.
- `plugins/cv-designer/skills/cv-designer/` — the skill: `SKILL.md`, `scripts/`, `assets/`,
  `references/`, `designs/`.
- `designs/<name>/` — one folder per visual design (`template.html`, `style.css`, `design.json`,
  `preview.png`). `designs/nordic` is the default; `designs/_template/README.md` is the design
  contract and authoring guide. `_`-prefixed dirs are scaffolding, never listed or CI-checked.
- `examples/` — synthetic sample only.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium        # once; poppler-utils also needed

# from plugins/cv-designer/skills/cv-designer/ — render the sample and gate it:
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/cv.pdf --auto-fit
python scripts/check_pdf.py --pdf /tmp/cv.pdf --data assets/example-cv.yaml

# design test loop (per design):
python scripts/render_cv.py --data assets/example-cv.yaml --out /tmp/d.pdf --design designs/<name> --auto-fit
python scripts/check_pdf.py --pdf /tmp/d.pdf --data assets/example-cv.yaml

claude plugin validate .                               # after touching plugin/marketplace JSON
```

## Hard rules

- **`check_pdf.py` must pass.** It is the machine-readability gate; never merge or deliver around
  a failing check. CI (`check-designs.yml`) renders every design (plain + photo) and enforces it.
- **Never commit personal data.** `cv-work/`, `work/`, `evals/files/` are gitignored on purpose;
  test with the synthetic sample only.
- **Fonts:** only the bundled hinted Inter via `font_faces()`. Other fonts (and OpenType numeral
  variants) break pdfminer extraction — this is the single most fragile ATS constraint.
- **Marketplace `source` stays an explicit subdir** (`./plugins/cv-designer`). claude.ai's
  server-side sync rejects `source: "."` even though the Claude Code CLI accepts it.
- **README.md and CONTRIBUTING.md are updated in the same change** whenever behavior, layout,
  install flow, designs, or the release process shift. New designs also go into the README gallery.
- **Releases:** tag `vX.Y.Z` → CI builds and attaches `cv-designer.zip`. Never commit built zips.
  `plugin.json` intentionally has no `version` field (installs track git).
- **Design changes** follow `designs/_template/README.md`: exact section headings and order, rem
  sizing driven by `base_pt`, accent only via `var(--accent)`, `design.json` + `preview.png`
  required per design.
