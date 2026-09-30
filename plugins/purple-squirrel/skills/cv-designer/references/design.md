# Design spec — what the template does and what you may change

> This file is the rationale and review checklist for the **nordic** design and the general rules
> all designs share. Building a new design? Start at `designs/_template/README.md`.

The visual language is Scandinavian in the functional sense: one typeface, generous whitespace, a
single muted accent, hairline rules, nothing decorative. The design should be invisible; the reader
should notice the content and, at most, that the document feels calm and well made.

Each design (`designs/<name>/template.html` + `style.css`) implements this; `designs/nordic` is the reference. Read this file
so you know what is deliberate and do not "improve" it ad hoc.

## Page

- A4 portrait, margins 16 mm top/bottom, 18 mm sides. Enough air; not so much that two pages become
  three.
- White paper. Off-white backgrounds look refined on screen and dirty when printed.
- Single column, full width. See writing-rules.md for why.
- No header/footer, no page numbers. The name is on page 1; page 2 is obviously the continuation.

## Type

- Inter, embedded from `assets/fonts/` (OFL licence included). Weights: 400, 400 italic, 500, 600, 700.
  These are the *hinted* woff2 builds from the Inter release: the unhinted `web/` builds make pdfminer
  split words after every "t" in the 500/600 weights ("Invest igat or"). Do not swap the files.
- Body 10 pt (1 rem), line-height 1.42. The renderer may step to 9.6 or 9.2 pt to fit; below that it
  refuses and asks for cuts.
- Scale (in rem): name 2.4, headline 1.15, role title 1.05, body 0.97–1.0, secondary 0.85–0.95,
  section heading 0.95 mixed case (uppercase + tracking splits under pdfminer), consent footer 0.72.
- Ligatures off and no OpenType numeral variants: both substitute glyphs that pdfminer-based
  parsers extract as private-use characters, which turns "2021" into garbage for a screening tool.

## Colour

Four inks and one accent; nothing else.

| Token | Default | Use |
|---|---|---|
| `--ink` | #1f2328 | body text, names |
| `--ink-2` | #5b6570 | dates, locations, stack lines, company one-liners |
| `--ink-3` | #8a939c | separators, bullet dashes, consent footer |
| `--rule` | #dcdfe3 | hairlines |
| `--accent` | #4a6b7c | section headings, headline |

The accent is a muted blue-grey. It may be overridden per render with `--accent "#hex"` when the
candidate asks; keep it desaturated and dark enough to read at 8.5 pt on white (contrast ≥ 4.5:1).
Reasonable alternatives: sage #5b7263, warm grey #6b625a, slate #4b5563. Not: bright blue, red,
orange, anything that reads as a brand.

## Structure and rhythm

- Header: name, headline in accent, one line of contact separated by middle dots, hairline below.
  Photo (if any) top right, 28 mm square, 2 mm corner radius, colour, `object-fit: cover`.
- Sections separated by 5.5 mm; heading in accent colour, mixed case, with a hairline under it. The rhythm — heading, hairline,
  content, air — is the whole visual system. Do not add boxes, backgrounds, icons, or a second rule.
- Experience entry: title (600) — company, location (400, location in ink-2), dates right-aligned.
  Optional grey one-liner. Dashes, not discs, for bullets; hanging indent 3.2 mm.
- Skills: two-column definition grid, label column sized to content (max 48 mm). This is a grid
  inside a single column — DOM order is label then items, which parses as "Label: items".
- Certifications and languages are plain inline lists. No badges.

## What you may change

- `--accent` via the CLI flag.
- Nothing in the CSS for a single CV. If a structural change is truly needed (a new section type,
  say), change the template and CSS in the skill so every future CV benefits, and update this file.

## What you should not do, and why

- **Two columns / sidebar**: scrambles reading order for extractors; also breaks the page rhythm.
- **Icons for phone/email/location**: icon fonts render as private-use glyphs in the text layer
  and the labels are obvious from the content anyway.
- **Skill bars, ratings, tag pills**: unverifiable, parse as noise, and look like a template.
- **Coloured header block or photo filters**: the calmness comes from restraint. A dark header band
  is the single most common way CVs of this genre become loud.
- **Decorative timelines**: same reasons; and they cost vertical space.
- **Justified text**: rivers of white in narrow measures. Left-aligned throughout.
- **Shrinking type below 9.2 pt or margins below 14 mm to fit**: it reads as cramming. Cut content.

## Reviewing the render

After every render, look at the PNG previews (`--preview-dir`) with the image reader before
delivering. Check, in this order:

1. Page count and last-page fill (the renderer prints both). A last page under ~30 % full is a
   defect: trim to the shorter count.
2. A section heading stranded at the bottom of a page with its content on the next. The CSS asks
   for `break-after: avoid`, but a heading followed by a very tall unbreakable entry can still
   strand. Fix by reordering or trimming, not by adding manual page breaks.
3. A single bullet or the stack line orphaned at the top of page 2. Cut or merge a bullet above it.
4. The contact line: wrapped cleanly (a wrapped line ends with the dot), nothing hidden under the
   photo.
5. Long role titles pushing the date column to a second line — shorten the title or location.
6. Photo crop: head not cut, not too tight, not looking away from the page. Re-run
   `prepare_photo.py` with `--anchor center` if `top` cut the chin.
7. Anything that looks like a template artefact: an empty section, a "None", a "present" that was
   not formatted, a stray YAML value.
