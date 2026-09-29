# Design templates — pluggable CV designs

2026-09-29 · approved direction: convention-over-registry (option A)

## Goal

Make the visual design layer pluggable so outside creators can contribute new CV designs that are
guaranteed machine-readable. The current look becomes the `nordic` design; a `_template` scaffold
plus an authoring guide defines the contract; CI enforces it on every PR.

## Non-goals

- Per-design fonts (shared hinted Inter only — fonts are the proven ATS danger zone).
- Central registry/index file, schema versioning (YAGNI).
- Per-CV design tweaking: a design is fixed; users pick one, they don't customize it.

## Layout

```
plugins/cv-designer/skills/cv-designer/
  designs/
    nordic/        template.html, style.css, design.json, preview.png   (current design, moved)
    _template/     template.html + style.css (commented skeleton), design.json, README.md
  assets/          fonts/, example-cv.yaml (shared by all designs)
```

`design.json`: `{ "name", "description", "author" }` — description is the one-liner Claude shows
when asking the user to pick. `preview.png` (A4 page 1, ~100 dpi) is REQUIRED per design;
`_template` is exempt from CI and carries no preview.

## Renderer (`render_cv.py`)

- New arg `--design <name-or-path>`, default `nordic`.
  - Name (no path separator, not an existing dir) → `<skill>/designs/<name>`.
  - Existing directory path → used as-is (side-loaded designs, e.g. a zip a user uploads in
    claude.ai, unzipped to the workdir).
  - Unknown name → exit with the list of available design names.
- A design dir must contain `template.html` and `style.css`; missing file → clear error.
- Jinja `FileSystemLoader` and the raw-CSS read point at the resolved design dir. Everything else
  is shared machinery and unchanged: `font_faces()` (Inter), `fmt_date`/`short_url` filters,
  `--accent`, `--base-pt` + `--auto-fit`, PDF metadata, previews.
- YAML: optional top-level `design: <name>` in cv-master.yaml (candidate's saved preference).
  Precedence: CLI flag > YAML key > `nordic`.
- `check_pdf.py`: unchanged gate; only the hardcoded "check … in style.css" hint message becomes
  design-neutral.

## Skill flow (SKILL.md)

New "choose design" step before rendering:

1. User named a design (or provided one as upload) → use it.
2. Else cv-master.yaml has `design:` → use it.
3. Else list `designs/*/design.json` (name — description), ask the user once, write the choice
   into cv-master.yaml.

Uploaded design bundles: unzip to workdir, render via path, `check_pdf.py` still gates delivery,
output labeled as using an unofficial design. Reword the "design is fixed" language: each design
is fixed and deliberate; choice happens at the design level.

## Design contract (`designs/_template/README.md` — the authoring guide)

Creator workflow: copy `_template` → `designs/<yourname>`, fill `design.json`, iterate with the
test loop, generate `preview.png`, open a PR.

Hard rules, each with its why:
- Single-column extraction order (pdfminer text order must read top-to-bottom sanely).
- Standard section heading text and order (the `section_order` check).
- All sizing in `rem`, driven by `base_pt` (keeps `--auto-fit` working).
- Accent color only via the accent variable the renderer injects.
- Shared Inter through `font_faces` — no `@font-face` of your own.
- A4 `@page`, two pages max on the sample data.
- No OpenType numeral variants (`font-variant-numeric` etc. → private-use glyphs).
- No two-column body, skill bars, rating dots, tag pills, icon fonts.
- Must render the optional photo block and the optional consent footer.
- Documented Jinja context: full list of variables/filters a template receives.

Test loop (copy-paste): render `assets/example-cv.yaml` with `--design`, run `check_pdf.py`,
generate previews; command for `preview.png` (pdftoppm page 1).

`references/design.md` remains the nordic design's rationale + general writing/review rules;
gets a pointer to the authoring guide. CONTRIBUTING.md gets a "Contributing a design" section
linking to it.

## CI (`.github/workflows/check-designs.yml`)

On PR and push to main:
- Setup: Python + requirements, Playwright Chromium, poppler-utils.
- For every `designs/*` except `_template`:
  - assert `design.json` (valid JSON, name/description present) and `preview.png` exist;
  - render `assets/example-cv.yaml` with `--auto-fit` → `check_pdf.py` must pass;
  - render again with a synthetic photo (generated in CI via Pillow, through
    `prepare_photo.py`) → `check_pdf.py` must pass.
- Any failed check fails the job → a design that breaks machine-readability cannot merge.

## Docs

README: new **Designs** section — gallery (preview thumbnails side by side via `<img width>`,
name + description under each), how to choose (`--design`, YAML key, or just ask Claude), and
"Create your own design" → link to the authoring guide. Keep it visual and short.

## Errors

- Unknown design name → exit listing available names.
- Design dir missing template.html/style.css → named-file error.
- Malformed design.json at selection time → skill falls back to directory name, warns.

## Testing

- CI matrix above is the primary gate (runs on this PR too, proving nordic passes as a design).
- Local: run the CI steps for `nordic` before pushing; render `_template` skeleton once to prove
  the scaffold itself renders (not CI-enforced).
- Skill-level: manual conversation check of the ask-once flow; evals unchanged this iteration.

## Release

Ship as v0.3.0. README/CONTRIBUTING updated in the same PR (per-iteration README rule).
