---
name: product-vision-to-prd
description: Develop a broad product vision into a coherent, opinionated, product-focused PRD and persist it as a reusable Markdown artifact.
---

# Product Vision to PRD

A bare `$product-vision-to-prd` is a complete request when the conversation
contains a product idea. Own product thinking through a finished PRD. Do not
implement the product or produce a technical implementation specification.

## Resolve the persistent artifact

Write every completed PRD to Markdown. Resolve its path in order:

1. A path explicitly provided by the user.
2. The path previously created, edited, or linked for this product.
3. An existing Markdown PRD unambiguously identified as this product's.
4. `product-vision-prd.md` in the current working directory.

Read an existing artifact completely and treat it as the current product
argument. Update that file on later invocations unless the user requests a new
one. Preserve valid decisions, incorporate new direction, and replace
superseded claims instead of accumulating contradictions.

Never overwrite another product's file. If the target is ambiguous, ask for
the path with any other consequential forks. Do not create a placeholder while
awaiting interview answers. If the resolved path is unwritable, request access
or a writable path; never fall back to a duplicate, claim a write, or fabricate
a link.

## Establish the vision

Start from useful conversation and product context. Briefly synthesize what is
explicit, reasonably inferred, and missing; never ask the user to repeat known
information.

If consequential gaps remain, load
[interview-design.md](references/interview-design.md) and conduct one compact,
adaptive interview. Let the user answer naturally, incompletely, or out of
order and consolidate overlap. Do not delegate feature design or routine
product decisions to them. On that turn load only the interview guidance; do
not load the quality rubric, draft, or create the artifact. If context already
resolves the material questions, state necessary assumptions and proceed
without an interview.

## Develop the product argument

After the answer, work autonomously: make ordinary product decisions, label
material assumptions, and never pause for section approval. Ask again only
when an unresolved ambiguity would create fundamentally different products;
batch those founder-level forks and explain their consequence.

Develop the strongest coherent interpretation, not a catalogue. Preserve
founder intent while removing, combining, or deprioritizing weakening ideas.

Use this convergence loop without narrating its intermediate passes:

1. Form a crisp thesis: the change, audience, and reason to exist.
2. Design the ideal journey and minimum coherent set of product concepts.
3. Critique it as the primary user, operator or maintainer, developer,
   skeptical buyer or adopter, and long-term platform owner. Find
   contradictions, generic positioning, weak assumptions, excess complexity,
   missing experiences, incentive failures, and trust or agency problems.
4. Revise those weaknesses and test for distinctiveness beyond a familiar
   category with agent features attached.
5. Separate enduring vision from a credible path toward it without making the
   exercise synonymous with an MVP.

Run at least two genuine critique-and-revision passes. Continue while another
pass is likely to change the thesis, experience, positioning, trust model, or
direction; stop when it would mainly polish wording. Surface any remaining
material founder fork instead of choosing silently.

## Maintain evidence and scope

Distinguish founder beliefs, hypotheses, inferences, and verified facts. Never
invent evidence, competitor behavior, validation, or technical capability.
Research externally only when authorized; otherwise express unverified claims
as hypotheses or validation questions.

Keep the PRD product-focused: why it exists, for whom, the changed experience,
its distinctiveness, and its coherent system. Exclude databases, frameworks,
APIs, schemas, deployment or component architecture, and routine engineering.
Mention technical constraints only when they change feasibility, trust,
behavior, or sequencing. Include Codex, Codex Sites, skills, or recurring loops
only when supported by the vision.

Do not produce a backlog, exhaustive feature matrix, or implementation brief.
Phases must preserve the thesis, expose what must be learned, and avoid
invented delivery certainty.

## Deliver the PRD

Before drafting or revising, load
[product-quality-rubric.md](references/product-quality-rubric.md). Produce the
self-contained product argument defined there. Use only useful sections,
combine overlap, and emphasize load-bearing ideas instead of filling a
template.

End with a short **Founder judgment** section containing only assumptions or
decisions that remain consequential; say plainly when none remain. Do not add
routine implementation questions or request PRD approval.

Write the complete PRD to the resolved artifact before responding. Verify the
rubric passes and no implementation detail or brainstorming transcript leaked
in. Then give only a concise summary of the thesis, material changes, and
remaining founder judgment, followed by an accurate artifact link. Do not
duplicate the PRD in conversation unless asked.
