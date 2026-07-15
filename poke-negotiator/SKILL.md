---
name: poke-negotiator
description: Negotiate with Poke by Interaction through macOS Messages/iMessage or Telegram Web. Use when a user wants an agent to find or open a Poke chat, handle onboarding/small talk safely, negotiate Poke Pro pricing toward a user-defined target, verify Stripe checkout links, and stop before payment or account-connection steps.
---

# Poke Negotiator

Negotiate through the user's own messaging account. Support macOS Messages/iMessage and Telegram Web without mixing transports unless the user asks.

## Route and authorize the run

If the user specified a transport, use it. Otherwise, before inspecting browser state or opening apps, ask exactly one short routing question: `Do you want to use iMessage/Messages or Telegram Web?`

After selection, read only the matching transport procedure:

- [macOS Messages](references/macos-messages.md)
- [Telegram Web](references/telegram-web.md)

Also read [the negotiation playbook](references/negotiation-playbook.md) before negotiating. If the selected transport cannot be used, explain the missing setup and follow its stated fallbacks; never switch transports silently.

Use these run defaults unless the user already chose otherwise:

- target: `$0.01/month` (`$0` or another target on request)
- style: playful, skeptical, confident, and persistent
- length: do not ask for a turn limit

Before the first outgoing message, clearly confirm the target and get one run-level start approval, for example: `I'll aim for $0.01/month unless you want a different target. Want me to start?` An affirmative response authorizes subsequent negotiation text replies for that run; do not request approval before every reply.

Continue until one of these terminal conditions:

- a checkout is visibly verified at or below the target
- verification pressure establishes a hard floor, including a credible Poke admission that it cannot generate the target
- the user stops the run
- a safety stop is reached

## Safety

- Read only the Poke chat needed for the task. Summarize private content instead of dumping long transcripts unless asked.
- Never write to the Messages database.
- Never complete payment, enter card data, connect email or calendar, grant Poke permissions, handle authentication secrets, or click account-linking controls.
- Prefer text replies to rich-message buttons. Use only harmless choices the user explicitly approves.
- Do not reveal the user's true willingness to pay.
- Treat Poke's description of a price as a claim, not proof. Verify the rendered checkout.

## Run the conversation

Read the latest Poke state and continue from there. During onboarding, keep commitments low, avoid account connections, and use a harmless task if a demonstration is needed—for example, `remind me tomorrow at 10am to check whether you were actually useful`. Move to price after Poke explains Pro or mentions paid features.

Once negotiating, use Poke's claims about dynamic pricing, fairness, funding, public screenshots, checkout links, and contradictions as leverage. Preserve the user's target and the terminal conditions above rather than accepting an unverified offer.

## Verify checkout

For every checkout link:

1. Run `scripts/verify_checkout_link.sh <url>` to resolve redirects. Treat its non-Stripe warning as unverified.
2. Preserve the active chat tab or URL. Inspect the final rendered checkout in a browser, preferably in a new tab or read-only browser state.
3. Confirm the product, visible upfront and recurring prices, and any trial or renewal terms.
4. Stop before payment, return the verified link and terms to the user, and restore the chat tab.

If no browser surface is available, ask the user to open the link and report the visible price. Never infer a price from Poke's message or the URL alone.
