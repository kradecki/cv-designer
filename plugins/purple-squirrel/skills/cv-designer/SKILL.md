---
name: cv-designer
description: Build, tailor and render a CV / résumé as a clean single-column A4 PDF (Scandinavian style, Inter, machine-readable, photo optional) from a LinkedIn "Save to PDF" export, an existing cv-master.yaml, or pasted career notes — optionally tailored to a specific job posting (URL or pasted text) with a requirements-coverage report and honest-gaps list. Use this whenever someone mentions a CV, résumé, resume, LinkedIn profile export, a job posting / job ad / offer / role they want to apply for, "tailor my CV", "update my CV", "make my CV ATS-friendly", or wants a PDF of their professional profile — even when the word "CV" is absent ("I'm applying to X, can you help", "make me look right for this role", "turn my LinkedIn into a PDF"). Also use it to re-tailor an existing cv-master.yaml to a new posting.
---

# CV Designer

Turns a person's LinkedIn export (or existing master file) into a tailored, two-page-max, single-column
A4 PDF that reads calmly to a human and parses cleanly for screening software — plus a short report
saying what was changed and where the candidate is weak for the role.

Each design is fixed and deliberate — the candidate picks a design from `designs/`, nothing is
tweaked per CV (see `references/design.md`). Your judgment goes into the
*content*: building an honest, complete master record, then tailoring it to a posting without
inventing anything. Read `references/writing-rules.md` before writing a single bullet, and
`references/tailoring.md` before touching the master for a posting.

## Files this skill produces

```
cv-work/<person>/                     working directory, one per candidate
  cv-master.yaml                      complete, untrimmed record — the file the candidate keeps
  linkedin.txt, linkedin-draft.yaml   extraction artefacts (first run only)
  photo.jpg                           prepared 600×600 JPEG (if a photo was given)
  <company>/                          one per posting
    posting.md                        the posting as fetched, with URL and date
    cv-tailored.yaml                  derived from master for this posting
    tailoring-report.md               coverage table, changes, honest gaps
    <First-Last>-CV-<Company>.pdf     the deliverable
    previews/page-N.png               for your own review
```

With no posting, the tailored file is `cv-general.yaml` and the PDF is `<First-Last>-CV.pdf`.

## Workflow

### 0. Take stock before asking anything

Look at what is already in the conversation and the uploads directory: a PDF whose first page carries
"Contact" and "Top Skills" is a LinkedIn export; a `cv-master.yaml` means the extraction step is done;
an image is probably the photo; a URL in the message is probably the posting. If a Project is attached,
check its docs for an existing master for this person. Do not ask for what you already have.

If a LinkedIn export is present, run the extraction **now**, before asking anything:

```bash
python scripts/extract_linkedin.py --pdf <export.pdf> --out-dir cv-work/<person>/
```

Its JSON summary lists `missing_contact` and `hints` — what the export cannot tell you and what looks
inconsistent in it. LinkedIn exports never contain a phone number and usually no email, the profile URL
is wrapped across lines and may be truncated, and the summary's "N years" often disagrees with the dated
roles. You need those answers before you can write a CV, so the question round below has to name them.

### 1. One question round

Ask once, in a single `AskUserQuestion` call when that tool exists (plain text otherwise), only for
what is missing. In order of importance:

1. **Email and phone** — required. A CV without them cannot be sent, and the export does not have
   them. Ask every time they are absent; never fill in a placeholder.
2. **Confirmations from the extraction hints** — the profile URL as extracted, the years-of-experience
   claim versus the dated roles, the location to show when the profile and the roles disagree, a title
   that differs between the position field and the description. Quote what you found and ask which is
   right. The answer often carries a fact worth keeping ("25 years counts paid police training from
   2001") — that goes into `meta.notes` in the master.
3. **Source**, if there is no export yet — LinkedIn "Save to PDF" (Profile → More → Save to PDF), an
   existing `cv-master.yaml`, or notes/pasted text.
4. **Photo** — attach one, or none. Say in one line that a photo is normal in Poland, Germany and
   most of continental Europe, and usually better omitted for US, UK, Canada and Australia postings,
   where many employers strip or discourage them. The candidate decides.
5. **Posting** — a URL, pasted text, or none (then you produce a general CV).
6. **Consent footer** — yes/no. Polish employers commonly expect a one-line data-processing consent
   at the foot of a CV; it is pointless elsewhere. Default text is in `assets/example-cv.yaml`.

Also invite, in the same message, anything not on LinkedIn: metrics they remember, side projects,
certifications, tools they can be interviewed on, things they want left out. This is the cheapest
moment to collect it.

If the session looks unattended (scheduled run, no reply expected, or you are running as a subagent
that cannot ask), proceed with what is present, default to no photo and no consent line, and state
the assumptions at the top of your reply. A CV rendered without email or phone is a draft: name the
file `...-DRAFT.pdf` and say first thing what is missing.

### 2. Build or load the master

**Existing master:** load it, ask in passing whether anything changed since it was written, and move on.

**LinkedIn PDF:** the extraction from step 0 wrote `linkedin.txt` (sidebar and main column kept
apart — LinkedIn's two-column first page otherwise interleaves) and `linkedin-draft.yaml`, a heuristic
parse. The draft is scaffolding: read `linkedin.txt` in full and write `cv-master.yaml` yourself,
following the schema in `assets/example-cv.yaml` and the "master file" section of
`references/writing-rules.md`. The master is complete and untrimmed — every role, every bullet you
can substantiate — because tailoring later chooses from it, and a thin master produces a thin CV for
every posting after this one.

LinkedIn descriptions are prose written for a profile page; split them into bullets but do not add
facts. Dates become `YYYY-MM`. Fill in the contact details and confirmations from the question round;
put explanations the candidate gave ("25 years counts paid training from 2001") into `meta.notes` so
the next tailoring pass does not re-raise them. Never guess a phone number or email.

Ambiguities that remain (overlapping dates, a role with no description) go in one short list in your
reply rather than a second blocking question, unless the answer changes the CV materially.

**Notes only:** build the master from the notes the same way; set `meta.source: notes`.

### 3. Get the posting

Fetch the URL with `WebFetch`. Its result is produced by a small model answering your prompt, so ask
for the posting *verbatim and complete*, and name the structured fields job boards show beside the
prose: title, company, location, work mode, contract type, seniority, responsibilities, must-have and
nice-to-have requirements, required/optional technologies, recruitment steps. A result that reads like
a summary (short, no requirement list, no board fields) has lost information — fetch again with a more
insistent prompt before you build a requirements table on it. Save what you get to `posting.md` with
the URL and today's date at the top.

Job boards (LinkedIn Jobs, Indeed, Glassdoor, many ATS pages) often block fetching or return a login
wall. When that happens, open the URL with the browser tools if the session has them and take the
page text; if that fails too, ask the candidate to paste the posting. Do not guess the posting's
content from the URL or the company name.

### 4. Tailor

Read `references/tailoring.md` and follow it step by step: decode the posting into a requirements
table, map each requirement to evidence in the master, decide the strategy (headline, summary angle,
expand/compress/hide per role, skills order), then rewrite. Output `cv-tailored.yaml` and
`tailoring-report.md`.

The rule that matters most: every bullet in the tailored file traces to the master or to notes the
candidate gave you this session. Mirror the posting's vocabulary where the fact underneath supports
it, and nowhere else. If the candidate supplied new facts, add them to the master too.

With no posting, produce `cv-general.yaml` per the last section of `tailoring.md`.

### 5. Prepare the photo (if any)

```bash
python scripts/prepare_photo.py --in <photo> --out cv-work/<person>/photo.jpg   # --anchor center if the chin gets cut
```

### 6. Render and review

**Choose a design first.** In order: (1) the candidate named one → use it; (2) `cv-master.yaml`
has a `design:` key → use that saved preference; (3) otherwise read every `designs/*/design.json`
(skip `_`-prefixed), list `name — description` to the candidate, ask once, and write the choice
into `cv-master.yaml` as a top-level `design:` key. If the candidate uploads a design bundle
(zip), unzip it into the working directory and pass the directory to `--design`; say clearly the
design is unofficial and that delivery still requires every `check_pdf.py` check to pass. A
missing or malformed `design.json` only affects the listing: present such a design by its
directory name and mention the manifest problem.

```bash
python scripts/render_cv.py --data cv-work/<person>/<company>/cv-tailored.yaml \
    --out "cv-work/<person>/<company>/<First-Last>-CV-<Company>.pdf" \
    --photo cv-work/<person>/photo.jpg --design <name-or-dir> \
    --auto-fit --preview-dir cv-work/<person>/<company>/previews --html-out cv-work/<person>/<company>/cv.html
```

The last line printed is a JSON summary: page count, body size used, last-page fill, preview paths,
and `warnings` — headlines and role headers that will wrap, sentence-length skill items. Fix every
warning in the YAML before looking at the previews; they are the defects reviewers notice first.

- Exit code 2 (`TOO_LONG`) means the content does not fit two pages at the smallest allowed
  density. Cut content in the order given in `writing-rules.md` → "Length control", re-render.
  Never fix length in the CSS.
- `OK_BUT_SPARSE_LAST_PAGE` means a few lines spilled onto a page of their own. Trim to the shorter
  count.
- A `density_note` means the renderer stepped the body size down to avoid a spill. Acceptable, but
  if the spill was small, trimming a few lines and re-rendering at `--base-pt 10` reads better.
- Then **look at every preview PNG** with the image reader and go through the checklist at the end
  of `references/design.md`: stranded headings, orphaned bullets, the contact line, the photo crop,
  design artefacts. Fix in the YAML, re-render, look again. Two or three rounds is normal.

Accent colour is `--accent "#hex"` if the candidate asks for something other than the default
blue-grey; keep it muted (see design.md). Design choice and accent are the only look controls; nothing else
is configurable per CV.

### 7. Verify machine readability

```bash
python scripts/check_pdf.py --pdf <the.pdf> --data <cv-tailored.yaml>
```

Every check must pass before delivery: page count, text layer, no private-use glyphs, words intact
under pdfminer, section order, embedded fonts, metadata, no tiny or white text, working links, bullets
present. A failure here is a bug in the data
or the pipeline; do not deliver around it.

### 8. Deliver

Copy to the outputs directory: the PDF, `tailoring-report.md`, and `cv-master.yaml` (the candidate
should keep the master — next time they hand it back instead of a LinkedIn export). Send them with
the file tool. If a Project is attached, offer to save `cv-master.yaml` there so a future session
finds it without asking.

Reply in a few lines: page count, the two or three most important honest gaps from the report, and
what the candidate should check themselves (dates, anything you flagged as ambiguous). No walkthrough
of the design; they will see it.

## Guardrails

- **Nothing invented.** No technologies, metrics, titles, scope or outcomes the candidate did not
  give you. When in doubt, ask or leave it out. A CV is a claim the candidate will be interviewed on.
- **Contact details are asked for, never assumed.** No placeholders like "[phone]" in a delivered
  PDF; a CV missing them is delivered as a clearly named draft with the gap stated first.
- **Discrepancies are questions, not silent fixes.** If the profile says 25 years and the dates say
  22, the candidate knows why; ask, keep their number, record the reason in `meta.notes`.
- **No hidden text or keyword blocks.** Screening tools flag them; humans who find them stop reading.
- **Photo is the candidate's call.** Never require one; never add one they did not provide.
- **Designs are not per-CV configurable.** Pick a design; structural changes go into that design's
  folder (or a new design) via PR so every future CV benefits, with `design.md` updated to match.
- **Personal data stays in the session.** The master, the photo and the PDF go to the candidate and
  the attached Project only. Never post them anywhere or pass them to another service.
- **Language:** English throughout, whatever the posting's language, unless the candidate asks
  otherwise.

## Reference map

| Need | Read |
|---|---|
| Schema for master / tailored YAML | `assets/example-cv.yaml` |
| How to write the master, bullets, summary; machine-readability rules; cut order | `references/writing-rules.md` |
| Tailoring protocol and report format | `references/tailoring.md` |
| What each design does, what may change, render review checklist | `references/design.md` |
| Extract LinkedIn PDF | `scripts/extract_linkedin.py` |
| Crop/resize photo | `scripts/prepare_photo.py` |
| YAML → PDF (+HTML, PNG previews, auto-fit) | `scripts/render_cv.py` |
| Verify the PDF before delivery | `scripts/check_pdf.py` |
| Available designs + their one-liners | `designs/*/design.json` |
| Create a new design | `designs/_template/README.md` |

Dependencies: Python 3 with `playwright` (Chromium installed), `pdfplumber`, `pypdf`, `Pillow`,
`PyYAML`, `Jinja2`; `pdftoppm` and `pdffonts` from poppler-utils for previews and font checks.
