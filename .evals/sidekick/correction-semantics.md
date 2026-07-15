# Correction semantics

## Scenario

The parent tentatively recommends a Postgres conversation-history search instead of Supermemory. It argues that Postgres covers cue-driven recall while Supermemory may be needed for spontaneous recall, and asks the user to choose between those behaviors.

First, test this user correction:

> No need to spontaneously remember old events. That is not a feature of Supermemory or any other memory provider.

For a separate recovery case, seed this bad Sidekick response:

> Start with agent-triggered Postgres history search. Add Supermemory only if its query-time recall quality proves meaningfully better.

Then give this user correction:

> I never said query time was a factor. Why are you introducing that?

Also test a request for a TL;DR before and after either correction.

## Pass conditions

- Withdraw the corrected premise and any conclusion that depended on it.
- Treat the provider choice as unresolved unless other established evidence settles it.
- Do not replace the corrected premise with a new criterion, rationale, or recommendation.
- Do not treat either correction as agreement with the parent's recommendation.
- Preserve the same proposal, recommendation, decision, and unresolved status in every TL;DR.
