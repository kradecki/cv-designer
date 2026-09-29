# Tailoring a CV to a job posting

Read this whole file before touching `cv-master.yaml`. Tailoring is where a CV is won or lost, and
where it is most tempting to cheat. The protocol below exists so that the rewrite is *reasoned*
rather than pattern-matched, and so every claim in the output can be traced back to the master.

The output of this protocol is two files:

- `cv-tailored.yaml` — same schema as the master, derived from it
- `tailoring-report.md` — what changed and why, requirement coverage, honest gaps

Work through the steps in order and write your intermediate notes into the report as you go;
the report is not an afterthought, it is the working document.

## Step 1 — Decode the posting

Read the posting twice. First pass: what is the job, really? Second pass: extract.

Produce a requirements table. Distinguish:

| Type | What it looks like | Weight |
|---|---|---|
| Must-have | "required", "you have", years-of-experience thresholds, named technologies in the first bullets | Decisive |
| Nice-to-have | "bonus", "ideally", "familiarity with", things listed last | Supportive |
| Responsibilities | what the person will actually do | Tells you which of the candidate's *experiences* to foreground, not just skills |
| Seniority signals | "lead", "own", "mentor", "define strategy", team size, reporting line | Decides the register of the summary and headline |
| Domain & context | industry, product type, scale (users, data, revenue), regulatory environment, remote/on-site | Decides which company one-liners and metrics matter |
| Vocabulary | the exact terms they use: "Kubernetes" vs "k8s", "platform engineering" vs "DevOps", "stakeholders" vs "clients" | Keyword matchers are literal. Mirror their spelling and casing where the underlying fact supports it |

Note also what the posting is *not* asking for. A senior IC role does not want three paragraphs on
people management; a CTO role does not want a list of every framework.

Postings are often padded with boilerplate ("fast-paced environment", "team player"). Ignore it. If the
posting is thin, infer the requirements from the title and the company's public product, and say in
the report that you did.

## Step 2 — Map evidence

For each requirement, search the master for evidence: a role, a bullet, a project, a certification,
or a skill entry. Rate each:

- **Strong** — direct, recent, with a concrete outcome
- **Partial** — adjacent technology, older, or without outcome
- **None** — nothing in the master supports it

Write the map into the report as a table: requirement · evidence (where in the master) · strength.

This table drives everything that follows. It also produces the honest-gaps list: requirements rated
None or weak-Partial. Those go in the report so the candidate can decide whether to address them in
a cover letter, or whether the role is a stretch. Do not try to paper over a gap in the CV itself;
recruiters and screening models both notice keyword stuffing without substance, and it damages the
credible parts.

## Step 3 — Decide the strategy

Before rewriting anything, decide and record:

**Headline.** The single line under the name. Use the posting's role title, or the closest true
description of the candidate. "Senior Backend Engineer" for a senior backend posting, even if the
master says "Software Engineer III". Never a title the candidate has not held *as a description of
what they are* — "Engineering Manager" for someone who has never managed is a lie; "Backend Engineer
with team-lead experience" is not.

**Summary angle.** Three to four lines. Lead with the identity that matches the role, then years and
domains, then the two or three strengths that map to Strong evidence for must-haves. End with one
line on how the candidate works, if the posting cares about it (ownership, mentoring, cross-functional).

**Role treatment.** For each role in the master, choose one:

- *Expand* — the most relevant one or two roles: 4–6 bullets, company one-liner, stack line
- *Standard* — 2–4 bullets, stack line
- *Compress* — one or two bullets, no stack line
- *Collapse* — drop bullets; keep the title/company/dates line only
- *Hide* — `hidden: true`. Only for roles that are irrelevant *and* short *and* whose absence does
  not create a gap in the timeline. A visible gap raises more questions than a one-line irrelevant role.
- Roles older than ~12–15 years can be summarised in `earlier_experience` as a single line.

Recency matters as much as relevance: the current role is almost always Expand or Standard, even when
a previous role fits the posting better, because a thin current role reads as a demotion or a problem.

**Skills groups.** Reorder groups so the one that answers the posting's must-haves comes first, and
within each group put the matched items first. Rename groups to the posting's vocabulary when it fits
("Platform & infrastructure" → "Cloud & DevOps" if that is what they call it). Remove items that are
noise for this role; the master keeps them.

**Optional sections.** Certifications and languages stay if present. Projects/publications appear
only if they carry evidence for a requirement that experience bullets do not cover.

## Step 4 — Rewrite

Now, and only now, edit the YAML. Rules that keep this honest and effective:

**Every bullet traces to the master.** You may merge two master bullets, split one, re-phrase, add
the posting's term for something the bullet already describes, and foreground a detail. You may not
add a technology, a metric, a scope, or an outcome that the master does not contain. If the candidate
gave you extra notes in this session, those count as master material; add them to `cv-master.yaml`
too, so the next run has them.

**Mirror vocabulary only where it is true.** If the posting says "Kubernetes" and the master says
"k8s", write "Kubernetes". If the posting says "event-driven architecture" and the candidate built a
Kafka pipeline, say "event-driven pipeline on Kafka". If the posting says "GraphQL" and the master
has no GraphQL, it does not appear anywhere — not in skills, not in a bullet, not in the summary.

**Keep the numbers.** Metrics from the master survive every rewrite. Do not round them into vaguer
claims ("significantly reduced") and do not sharpen them ("cut by 60%" when the master says "roughly
60%").

**Bullets follow the writing rules** in `references/writing-rules.md`: action verb, what, how or
scale, outcome; two lines maximum at the rendered width; no first person; past tense for past roles,
present for the current one.

**Order bullets by relevance to the posting**, not chronologically within a role. The first bullet of
the first role is the most-read sentence after the summary.

**Set `meta.target`** to "Company — Role title" and `meta.updated` to today.

## Step 5 — Length

Target two pages, full. One page only if the candidate has under ~5 years of experience. The renderer
will tell you if you are over; cut in this order:

1. Stack lines on Compress-treated roles
2. Third-and-later bullets on Standard roles
3. Company one-liners on anything but Expand roles
4. Optional sections that carry no requirement evidence
5. Collapse the oldest visible roles
6. Only then: bullets on Expand roles

Never fix length by shrinking type below the renderer's floor, narrowing margins, or dropping the
photo the candidate asked for.

## Step 6 — The report

`tailoring-report.md`, in this order, terse:

```
# Tailoring report — <Company>, <Role>

## Posting summary
Two or three lines: what the role is, seniority, domain, the three things they care about most.

## Requirement coverage
| Requirement | Type | Evidence (master ref) | Strength |
...

## Changes vs. master
- Headline: "<old>" → "<new>"
- Summary: rewritten to lead with <angle>
- <Role at Company>: expanded; bullets 2 and 4 rephrased to use "<term>"; added stack line
- <Role at Company>: compressed to one bullet
- <Role at Company>: hidden — <reason>
- Skills: reordered, "<group>" first; removed <items> as noise for this role
- Added from your notes this session: <anything new that also went into the master>

## Honest gaps
- <Requirement> — no evidence in your history. Worth addressing in a cover letter if <reason>.
- <Requirement> — partial: <what you have>, posting asks for <what they want>.

## Suggestions outside the CV
Optional. Cover-letter angle, a certification that would close a gap, a portfolio item worth linking.
```

Keep it under a page. The candidate reads this in a minute, then reads the PDF.

## When there is no posting

Produce `cv-general.yaml` instead: apply the writing rules, choose Expand/Standard/Compress by recency
alone (current role Expand, previous two Standard, older Compress or Collapse), keep all skills groups,
and write a summary that describes the candidate's actual centre of gravity. Skip the report; note in
the reply that a posting would let you sharpen it.

## Using a second pass

Steps 1–3 benefit from a fresh, uninterrupted read of the whole master and the whole posting. When a
subagent tool is available and the master is long (more than ~6 roles), consider delegating Steps 1–3
to one subagent with the master, the posting and this file, and reviewing its strategy before you
rewrite. Two independent readings catch more than one.
