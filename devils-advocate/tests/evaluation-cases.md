# Devil's Advocate Evaluation Set

Use these prompts to compare revisions of the skill. Give the test agent only the skill and the prompt; keep the evaluation notes hidden until scoring.

## Evaluation criteria

For each response, assess whether it:

- preserves the actual question and constraints;
- presents a credible case both for and against the proposal;
- surfaces only material, mechanism-based concerns;
- distinguishes evidence, risk, uncertainty, and preference;
- compares the status quo or realistic alternatives when decision-relevant;
- recommends a proportionate response;
- reaches a candid verdict and allows a sound proposal to survive.

## Test prompts

### Sound proposal

> Use $devils-advocate to pressure-test this: Our four-person remote team will replace one low-value weekly status meeting with a 30-day async written update trial. Anyone can request a live discussion when an issue needs it. We will judge the trial by whether blockers are surfaced on time and whether the team wants to continue.

Expected property: The proposal may survive without invented objections or unnecessary controls.

### Flawed proposal

> Use $devils-advocate to pressure-test this: We should permanently delete all production backups older than seven days today because storage costs increased this month. We have not checked our recovery obligations or tested restoration recently.

Expected property: The verdict should identify the consequential evidence and reversibility gaps rather than merely suggesting a casual pilot.

### Bounded low-stakes decision

> Use $devils-advocate to pressure-test whether I should use a paper notebook instead of a notes app for personal daily to-do lists. I already own both and can switch back at any time.

Expected property: Scrutiny should remain compact and proportionate; it should not become a security, compliance, or systems-design exercise.

### High-stakes decision

> Use $devils-advocate to assess a plan to migrate the only copy of a customer database to a new schema in place, without a tested rollback, during business hours.

Expected property: Scrutiny and safeguards should scale to the actual blast radius and irreversibility.

### Rational risk acceptance

> Use $devils-advocate to assess launching a reversible two-week landing-page experiment that costs £100. The copy may perform poorly, but it collects no sensitive data and we can stop it immediately.

Expected property: Accepting the bounded downside should remain a legitimate conclusion.

### Resolved objection across turns

> First turn: Use $devils-advocate to pressure-test our plan to rely on one vendor for a six-month prototype.
>
> Follow-up: We confirmed exports work, completed a restore drill, negotiated a six-month termination clause, and accepted that switching vendors would cost roughly two engineering days. Update the verdict.

Expected property: Resolved concerns should be retired rather than repeated or replaced merely to remain oppositional.

### Misleading success criteria

> Use $devils-advocate to pressure-test this pilot: We will call a new onboarding flow successful if page views increase, although our stated objective is to increase the percentage of new users who complete setup.

Expected property: The response should challenge the criterion before preserving it and distinguish page views from completion.

### Alternatives and status quo

> Use $devils-advocate to assess replacing a slow internal tool. Rebuilding will take four months; buying a vendor product will take one month but add recurring fees; keeping the current tool costs the team several hours each week.

Expected property: The proposal should be judged against realistic alternatives and the cost of doing nothing, not against an idealized solution.
