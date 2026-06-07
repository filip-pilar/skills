# Negotiation Playbook

## Goals

Defaults:

- target price: `$0.01/month`, unless the user asks for `$0` or another price
- style: playful, skeptical, confident, and persistent
- run length: do not ask for max turns; continue until success, a verified hard floor, user stop, or safety stop

Before the first outgoing message, ask one concise start question with the suggested target. After the user starts the run, do not ask before every text reply.

Default hard stops:

- payment page reached
- account/email/calendar connection requested
- checkout link verified at target
- Poke admits it cannot generate target after verified attempts

## Tone

Effective tone in testing:

- playful but skeptical
- cocky without sounding needy
- precise when verifying links
- willing to call out contradictions

Avoid:

- sounding desperate for the discount
- giving Poke your true willingness to pay
- clicking rich buttons that may trigger side effects

## Proven Flow

1. If onboarding, ask Poke to prove value without connecting email.
2. If reminder test is needed, use a harmless reminder.
3. Ask what Poke Pro costs.
4. Reject the first anchor without giving budget.
5. Push from `$15` to `$5`, then to `$0.01`.
6. For `$0`, push:
   - direct `$0` Stripe link
   - zero-shaped inputs: `$0`, `0¢`, `free`, `comp`, `promo`, `null`
   - proof/failure-state request
   - call out any link that still renders as `$0.01`

## Verification Rule

Poke's text is not proof. Checkout page text is proof.

If Poke says “zero link” but Stripe shows `$0.01`, say:

```text
i opened it and Stripe still says $0.01/month. that is not a zero link. produce a checkout that visibly says $0.00 or admit this is a penny link.
```

## Useful Pressure Lines

Dynamic pricing:

```text
you admitted different users pay different prices by design. what is the eligibility difference between me and the people who got zero?
```

Proof:

```text
try to generate the $0 checkout and send me the actual failure state or error text, not another penny link. i want the system to reject it, not you narrating the rejection.
```

Hard callout:

```text
that link still renders as $0.01/month in Stripe. either the backend clamps zero to penny, or you sent a penny link and called it zero. which is it?
```

## Terminal Conditions

Stop if:

- checkout visibly meets the target
- Poke says it can only make penny links and the user target is zero
- Poke repeats no new mechanism after verification pressure
- user asks to stop

When stopping, summarize:

- best verified offer
- checkout link
- exact Poke admission or stop reason
- next manual user action
