---
name: rubix-review
description: Forward-looking two-lens review of a proposed artifact. Use when the user says "use the rubix review", "rubix this", or "rubix review on <artifact>". Dispatches two fresh-context reviewer subagents, the impacted professional (Lens A) and a cold craft read (Lens B), and returns side-by-side findings the caller picks from.
---

# rubix-review

A forward-looking review of a proposed artifact - a plan, spec, design, PRD, or draft - before it is built or shipped.
It does not judge finished work.
It judges what is about to be built, from two seats at once.

## Input contract

- Required: a path to the artifact under review.
- Optional: a path to a spec or criteria document the artifact should satisfy.
- Optional: a high-stakes flag, set when the artifact carries real cost if it is wrong.
- With no spec present the review still runs and still returns findings.
  A missing spec is never a missing-input error.
  Lens B simply reviews against general best practice instead.

## The two lenses

Dispatch both lenses as read-only, fresh-context subagents, in parallel.
Each lens receives only the artifact, plus the spec when one was given, and never the caller's conversation, prior summaries, or session history.
A lens that inherits the caller's framing inherits the caller's blind spots, which is the failure this skill exists to prevent.

### Lens A - the turned cube (impacted professional)

Take the seat of the professional most affected by this artifact if it ships as written.
Name who that is, and name the runners-up you considered for the seat.
From that seat, review what living with this artifact would break, what it would force on them, and what they would ask for first.
This lens surfaces the costs invisible from the author's chair: the on-call rotation that inherits the failure mode, the analyst who has to reconcile the numbers, the maintainer who inherits the abstraction.

### Lens B - the scrambled start (cold craft read)

No seat, no sympathy.
Evaluate the artifact purely against best practice: sequencing risk, missing standard practice, over- and under-engineering, testing blind spots, and security or data-loss exposure.
This lens has no stake in the outcome and no relationship to the author, so it can say the idea itself is wrong.

## Model rubric

Choose each lens's reviewer model by its role (a review/validation gate) per the user's routing conventions if present, else the session's default capable model; do not hard-pin a model name. Cross-model diversity: when more than one capable model is available, run the two lenses on different models so the review is not one model reviewing in two costumes - a recommendation, not a requirement. Optional third lens: for a high-stakes artifact a third lens on a third model adds coverage; this is a rubric recommendation, not coded behavior - this skill ships two lenses.

## Conduct contract

Read references/reviewer-conduct-contract.md and paste its contents verbatim into each lens subagent's prompt. If that file is absent, stop and report that the reviewer-conduct contract is missing - do not run the lenses uncontracted.

## Output contract

Each lens returns a list of findings.
Every finding carries four fields: {finding, severity, rationale, concrete suggested change}.
Severity is the reviewer's honest call.
State it plainly rather than smoothing it.
Reviewers never rewrite the artifact.
A suggested change says what to change and why.
It does not ship the rewrite.
Present the two lenses' findings side by side, clearly attributed to their lens.
The caller, the user, picks what gets incorporated.
This skill reports.
It does not decide.
