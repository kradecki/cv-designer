# Writing rules — content that reads well to humans and parses cleanly for machines

Two audiences read a CV today, usually in this order: a screening model or ATS that extracts and
matches, then a human who spends about thirty seconds on the first pass. The rules below serve both.
Where they pull in different directions, the human wins — a CV that parses perfectly but reads like a
keyword list is discarded at the human step.

## The master file

`cv-master.yaml` is the candidate's complete professional record, not a CV. It is allowed to be
long. It contains every role, every bullet you can substantiate, every skill, all certifications.
It never contains anything the candidate has not done. Trimming is a property of tailored copies.

When building the master from a LinkedIn export:

- Keep LinkedIn's facts, fix its form. LinkedIn descriptions are often paragraphs written for a
  profile page; split them into bullets, but do not add anything.
- Normalise dates to `YYYY-MM` when the month is known, `YYYY` otherwise. LinkedIn gives months.
- Where LinkedIn shows several titles at one company, keep them as separate roles with the same
  company (promotion trail is a positive signal) unless they are trivially similar.
- LinkedIn's "Top Skills" are three items chosen by an algorithm. Build proper skill groups from the
  experience descriptions and the full skills list if the candidate provides one. Ask if unsure.
- Contact details: LinkedIn exports include the profile URL (wrapped over two lines, so confirm it)
  and sometimes email, never a phone. Ask for both; never guess, never leave a placeholder.
- When the profile's own claims disagree with its dates ("25 years" vs. roles from 2004), ask. The
  candidate usually has a reason (paid training, an earlier employer left off LinkedIn). Keep their
  figure, record the reason in `meta.notes`, and add the earlier period to `earlier_experience` or
  education if they give you enough to state it.
- Location is city and country. Never a street address, never a postcode; nobody posts a CV.
- Do not include date of birth, nationality, marital status or a personal statement about hobbies
  unless the candidate explicitly asks. They add nothing and in several markets they create legal
  exposure for the employer.

## Headline

One line under the name — at most about 60 characters at the rendered width. The role the candidate
is (or is applying to be), optionally with one specialisation: "Senior Backend Engineer · Distributed
systems". Not a slogan, not a list of three things joined by dots; years of experience and languages
belong in the summary. The renderer warns when a headline is likely to wrap.

## Summary

Three or four lines, rendered as one paragraph. Structure that works:

1. Identity and years: "Backend engineer with 9 years building payment systems"
2. Where and at what scale: "most recently leading a four-person platform team at a fintech scale-up"
3. Two or three distinctive strengths, chosen for the target: "Strong on distributed-systems
   correctness, observability and cloud cost control"
4. Optional: how they work, if the role cares: "Comfortable owning a service end to end"

Kill on sight: "passionate", "results-driven", "dynamic", "proven track record", "team player",
"detail-oriented", "seasoned", "leveraging", "synergy". These words carry no information and mark
the text as template-generated. Say what the person did instead.

No first person ("I", "my") anywhere in the CV. No third person either ("Anna is…"). Implied subject.

## Bullets

The shape: **action verb + what + how or at what scale + outcome**. Not every bullet has all four,
but every bullet has the first two and most have an outcome.

- "Led the migration of the settlement ledger from a monolith to five Go services on Kubernetes,
  cutting p99 settlement latency from 4.2 s to 380 ms." — all four, good.
- "Responsible for backend development." — no verb of action, no outcome, no content. Rewrite or cut.
- "Worked on Kubernetes." — verb without substance. What did they *do* with it?

Length: two rendered lines maximum (about 180 characters at the default density). One line is
often better. If a bullet needs three lines, it is two bullets or it has padding.

Tense: past for past roles, present for the current role's ongoing responsibilities, past for the
current role's completed achievements. Mixed tense within the current role is normal and correct.

Numbers: keep every real metric. Prefer absolute to relative when both are available ("from 4.2 s to
380 ms" beats "by 91 %"). Use the candidate's own approximations honestly ("roughly 60 %", "~20").
Never invent a number to make a bullet feel concrete.

Verbs that carry weight: led, designed, built, migrated, introduced, reduced, cut, owned, shipped,
scaled, automated, replaced, negotiated, mentored, defined, consolidated. Verbs that do not:
"helped", "assisted", "participated in", "was involved in", "worked on", "responsible for".
Weak verbs are sometimes honest — a junior *did* assist. Keep them then, but tighten the rest.

Bullet count by role treatment (see tailoring.md): Expand 4–6, Standard 2–4, Compress 1–2,
Collapse 0.

## Role headers

Title, company and location share one line with the date on the right. Keep each short enough that
the line does not wrap: a title of up to ~45 characters, a company name without parentheticals. An
employer whose name is in another language keeps its official name in `company`; the English gloss
("Hesse State Criminal Police Office") goes in the role's one-liner, where it also does more work.
The renderer warns about headers likely to wrap.

## Company one-liner (`summary` on a role)

Optional. One line, grey, under the role header. Use it when the company is not widely known and its
domain or scale matters for the target: "Payments infrastructure for 2M+ merchants across the
Nordics." Skip it for household names and for compressed roles.

## Stack line (`tech` on a role)

Six to ten items. The technologies that were actually central to the role, not everything touched.
Order: the ones matching the posting first. This line is where literal keyword matchers find their
matches, so use canonical names: "PostgreSQL" not "Postgres", "Kubernetes" not "k8s", "TypeScript"
not "TS", "Amazon Web Services (AWS)" once in skills and "AWS" thereafter.

## Skills section

Three to six groups. Group names are plain: "Languages", "Cloud & infrastructure", "Data",
"Practices", "Leadership". Items comma-separated, most relevant first, canonical names, one to four
words each — "Incident response", not "Incident response coordination with corporate IT and security
teams (ransomware, data breaches)". The detail lives in the bullets; the skills block is the index. No
proficiency bars, percentages or star ratings — they are unverifiable, they parse as noise, and they
invite the question "why only 80 % on Python?".

Do not list a technology in Skills that appears nowhere in Experience unless the candidate confirms
they can be interviewed on it today.

## Education, certifications, languages

Education: degree, field, institution, years. No grades unless recent graduate and strong. Thesis
only if directly relevant.

Certifications: official name, issuer, year. Expired certifications: drop or mark the year honestly.

Languages: language and level. Use CEFR (A1–C2) or "Native"/"Fluent". Not "Good".

## Machine readability

What screening systems and AI parsers actually do: extract the text layer in reading order, look for
standard section headings, split experience into roles by date patterns, and match terms against the
posting. The template already handles most of this. What remains your responsibility:

- Keep the standard headings the template renders: Summary, Experience, Skills, Education,
  Certifications, Languages. Do not rename them to "My journey" or "Toolbox".
- Keep dates in the data as `YYYY-MM`; the template renders "Mar 2021 – Present", which every parser
  understands. Do not write "Spring 2021".
- Put contact details in the data fields, never in the photo or a graphic.
- Do not put text in images. The photo is the only image.
- Never add hidden text: white-on-white keywords, 1-pt text, keyword blocks "for the ATS". Modern
  screening tools flag it, and a human who finds it stops reading. `check_pdf.py` looks for it.
- One column. The template is single-column for this reason; do not change the CSS to add a
  sidebar.
- Special characters that extract cleanly: en dash (–), middle dot (·), ampersand. Avoid emoji,
  arrows, and icon fonts entirely.

## Length control — cut order

When the renderer reports too many pages, cut in this order and re-render after each step:

1. Stack lines on compressed roles
2. Third-and-later bullets on standard roles
3. Company one-liners except on expanded roles
4. Optional sections carrying no evidence for the target
5. Collapse the oldest visible roles to a header line; move roles older than ~15 years into
   `earlier_experience`
6. Bullets on expanded roles — last resort

Never fix length with the CSS. The renderer's density floor (9.2 pt body) is already the smallest
that reads comfortably on paper.

When the renderer reports a nearly empty last page, cut to the shorter page count rather than
padding. A page and a half reads as a page with an appendix.
