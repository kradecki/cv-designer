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
