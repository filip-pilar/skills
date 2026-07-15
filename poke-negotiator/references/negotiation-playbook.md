# Negotiation Playbook

## Approach

Be playful and precise without sounding needy. Do not disclose the user's real willingness to pay.

1. During onboarding, ask Poke to demonstrate value without connecting email or calendar. Use a harmless reminder if a test is needed.
2. Ask what Poke Pro costs, reject the first anchor without revealing a budget, and push from `$15` to `$5` to the user's target.
3. Use Poke's dynamic-pricing and fairness claims as leverage. Ask what eligibility distinction separates this user from people shown a lower price.
4. Demand a real checkout or failure state rather than narrated success. The rendered checkout is proof.

For a `$0` target, try a direct zero-dollar checkout and zero-shaped inputs such as `$0`, `0¢`, `free`, `comp`, `promo`, or `null`. If Poke calls a link free but Stripe renders `$0.01`, state the discrepancy and require either a checkout visibly showing `$0.00` or an admission that the backend floors prices at a penny.

Useful verification pressure:

```text
try to generate the $0 checkout and send me the actual failure state or error text, not another penny link. i want the system to reject it, not you narrating the rejection.
```

Do not keep repeating the same demand after Poke supplies no new mechanism under verification pressure; that establishes a hard-floor stopping condition.

## Finish

When a root terminal condition is reached, summarize:

- the best verified offer and checkout link
- the exact admission, verification result, or stop reason
- the next manual action, if any
