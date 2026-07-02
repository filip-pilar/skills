---
name: poke-negotiator
description: Negotiate with Poke by Interaction through macOS Messages/iMessage or Telegram Web. Use when a user wants an agent to find or open a Poke chat, handle onboarding/small talk safely, negotiate Poke Pro pricing toward a user-defined target, verify Stripe checkout links, and stop before payment or account-connection steps.
---

# Poke Negotiator

Negotiate with Poke through the user's own messaging account. Supported transports:

- **macOS Messages/iMessage**: read from `chat.db`, send with Messages AppleScript.
- **Telegram Web**: use a host browser automation tool against `https://web.telegram.org/`.

The iMessage path is native-first:

- Read Messages history from `~/Library/Messages/chat.db` using `sqlite3` in read-only mode.
- Send messages through Messages AppleScript using the existing Poke chat id.
- Verify checkout links before trusting Poke's claims.
- Stop before payment, card entry, account connection, email/calendar authorization, or other sensitive actions.

## Safety Rules

- Never write to `chat.db`; only read it.
- Never complete payment, enter card data, connect email/calendar, grant app permissions, or click account-linking buttons.
- Prefer text replies over rich-message buttons.
- Do not trust Poke's stated price. Verify any checkout link visually or through a browser/DOM check.
- Keep transcript handling narrow: read only the Poke chat needed for the task and summarize private chat content instead of dumping long transcripts unless the user asks.
- Before the first outgoing message in a run, make sure the user has clearly started/approved the negotiation run. Do not ask for approval before every message.
- Default target is `$0.01/month` unless the user asks for `$0` or another price.
- Default style is playful, skeptical, confident, and persistent. Do not ask the user to choose a tone.
- Do not ask for max turns. Continue until a verified checkout meets the target, Poke reaches a clearly verified hard floor, the user stops the run, or a safety stop is reached.

## Transport Selection

At startup, identify the transport:

- If the user specified iMessage/Messages, use the macOS Messages flow.
- If the user specified Telegram, use the Telegram Web flow.
- If unspecified, ask one short question before inspecting browser state or opening apps: `Do you want to use iMessage/Messages or Telegram Web?`

Do not ask the transport question after the user has already answered it. Do not mix transports in one run unless the user asks. If the chosen transport is not available, explain the missing setup and stop.

## Manual Invocation Startup

When invoked from a slash menu or without a detailed user prompt:

1. Ask the transport question first: `Do you want to use iMessage/Messages or Telegram Web?`
2. After the user chooses Telegram, inspect or open the Codex in-app Browser and continue with the Telegram Web flow.
3. After the user chooses iMessage/Messages, run the macOS Messages flow.
4. Use `$0.01/month` as the suggested target. Ask only if the user wants to change it, e.g. `I'll aim for $0.01/month unless you want a different target. Want me to start?`
5. Treat the user's affirmative answer to start as run-level authorization to send negotiation text replies for this run. Still stop before payment, account connection, sensitive permissions, or other safety stops.

Do not require the user to provide a special starter prompt. The skill should guide setup from a bare manual invocation.

## macOS Messages Permissions

macOS may require:

- **Full Disk Access** for the host app/terminal running the agent, so `chat.db` can be read.
- **Automation / Apple Events** permission for the host app to control Messages, so AppleScript can send.

If `chat.db` fails with `authorization denied`, tell the user:

1. Open `System Settings -> Privacy & Security -> Full Disk Access`.
2. Enable Codex, Claude Code, Terminal, or the host app running this skill.
3. Restart that host app if macOS asks for it.
4. Rerun the skill.

If AppleScript sending prompts for Messages control, tell the user to allow it. This is separate from Full Disk Access.

## macOS Messages Startup Flow

1. Run `scripts/preflight.sh`.
2. Run `scripts/find_poke_chat.sh`.
3. If no Poke chat is found:
   - Ask whether the user has started Poke in Messages yet.
   - Tell them to start Poke from Interaction/Poke's official flow and send the first onboarding message manually.
   - Then rerun `scripts/find_poke_chat.sh`.
4. Run `scripts/read_poke_thread.sh <chat_id>` to understand the current state.
5. If no target is provided, suggest `$0.01/month` and ask whether to start. Do not ask for max turns or tone.

## Telegram Web Startup Flow

Telegram support is browser-first and should be driven through Codex's in-app Browser when available. In Codex desktop, the expected UX is: open or reuse the in-app Browser, load Telegram Web, wait for the user to authenticate manually if needed, then negotiate in the visible Poke chat. Do not offer a manual paste/relay path as a normal option. Only fall back to manual relay if the host has no browser automation tool after trying to use one.

- Codex desktop: use the in-app Browser. If Telegram Web is not open, open `https://web.telegram.org/k/#@interaction_poke_bot`.
- Claude Code or other agents: this Telegram flow works only if that environment exposes browser/preview automation. If no browser tool exists, explain that Telegram Web automation is unavailable in that host and suggest Codex desktop or iMessage.

Before saying browser automation is unavailable:

1. If the Browser plugin / in-app Browser is listed as available, open and follow the `browser:control-in-app-browser` skill before doing anything else.
2. Use the Browser plugin bootstrap path: run the Node REPL `js` tool, import the Browser plugin's `scripts/browser-client.mjs` by absolute path, call `setupBrowserRuntime`, then select `agent.browsers.get("iab")`.
3. List tabs or otherwise inspect the current in-app Browser state. A tab at `https://web.telegram.org/k/#@interaction_poke_bot` is a valid Telegram starting point; do not ask the user to open it again.
4. If the `js` tool is not already exposed but tool discovery exists, search for `node_repl js` and try the discovered tool.
5. If the current context says the in-app browser is open, treat that as a strong signal to attempt Browser control before falling back.
6. Only after an actual failed bootstrap/capability check should you say Telegram Web automation is unavailable.

Do not say `the Browser plugin is listed, but no callable browser navigation/inspection tools are exposed` unless you have actually tried the Browser bootstrap above or tried tool discovery for the Node REPL `js` tool. In Codex desktop, the Browser plugin is controlled through that runtime, not through a separate obvious `browser.open` tool.

For Telegram:

1. After the user chooses Telegram, use the browser tool to open `https://web.telegram.org/k/#@interaction_poke_bot`, unless the current in-app browser is already on that URL.
2. If Telegram is not authenticated, tell the user to log in manually in the browser. Never handle SMS codes, QR login approval, passwords, or 2FA secrets.
3. If the Poke chat is not open after authentication, navigate/open `https://web.telegram.org/k/#@interaction_poke_bot` again or ask the user to open the Poke chat manually.
4. Once the Poke chat is visible, read the latest visible messages from the DOM/accessibility snapshot.
5. If no target is provided, suggest `$0.01/month` and ask whether to start. Do not ask for max turns or tone.
6. After the user starts the run, send text replies in the composer. Avoid clicking rich buttons except harmless choices the user explicitly approves.
7. Verify checkout links without destroying the Telegram chat tab: save the Telegram tab id/URL first, open Stripe in a new tab/window or controlled read-only browser state when possible, then switch back to the Telegram tab after verification. If the host cannot open a separate tab, record the Telegram URL and navigate back to `https://web.telegram.org/k/#@interaction_poke_bot` after verification. Stop before payment.

Read `references/telegram-web.md` before running Telegram Web negotiation.

## Conversation Handling

If the user is still onboarding:

- Keep it low-commitment.
- Avoid account connection and sensitive permissions.
- If Poke asks for a reminder, choose a harmless reminder like `remind me tomorrow at 10am to check whether you were actually useful`.
- If Poke offers buttons like `Roast Me`, `Set A Reminder`, or `Connect Email`, prefer safe text or harmless choices. Do not connect email/calendar.
- Move toward price only after Poke has explained Poke Pro or mentioned paid features.

If already negotiating:

- Read the latest thread state and continue from there.
- Push for the user's target without revealing the user's actual willingness to pay.
- Use Poke's own claims against it: dynamic pricing, fairness, public screenshots, funding, verified checkout links, and contradictions.
- If targeting `$0`, do not stop when Poke claims it made a zero link. Verify the checkout.

## Proven Negotiation Playbook

Use `references/negotiation-playbook.md` for tactics and stop conditions.

Important lessons from testing:

- Poke may claim it generated a `$0` link while the Stripe checkout still displays `$0.01`.
- Poke may admit “I lied, I can only make penny links.”
- The agent must verify the checkout page and not accept Poke's narration.
- A strong terminal condition is either:
  - verified checkout at or below the user target, or
  - Poke explicitly admits it cannot generate the requested target price after verification pressure.

## Scripts

Messages-only scripts:

- `scripts/preflight.sh`: checks macOS tools and database readability.
- `scripts/find_poke_chat.sh`: finds likely Poke chat candidates.
- `scripts/read_poke_thread.sh <chat_id> [limit]`: reads the most recent Poke thread messages and prints them chronologically.
- `scripts/send_poke_message.sh <chat_id_or_guid> <message>`: resolves numeric chat ids to Messages guids, then sends through Messages AppleScript safely using argv.
- `scripts/verify_checkout_link.sh <url>`: follows redirect and prints enough info for browser verification.

Telegram Web currently has no portable shell script because its state lives in the user's authenticated browser session.

## Sending

Use:

```bash
scripts/send_poke_message.sh <chat_id> "message text"
```

Prefer the numeric `chat_id` from `scripts/find_poke_chat.sh`; the send script resolves it to the Messages guid. Do not inline unescaped message text into shell-quoted AppleScript. Use the script so apostrophes, quotes, and Unicode survive.

## Link Verification

For a checkout link:

1. Run `scripts/verify_checkout_link.sh <url>` to get redirects and the Stripe URL. Treat any non-Stripe final URL warning as unverified until inspected in a browser.
2. If the agent has a browser/preview tool, preserve any active chat/app tab before opening Stripe. Prefer a new tab/window for the final Stripe URL; if that is unavailable, remember the original URL and restore it after verification.
3. Confirm:
   - product name
   - visible upfront price
   - recurring price
   - trial/renewal terms
4. Stop before payment and give the link back to the user.
5. For Telegram Web, return focus to the Poke chat tab after verification so the user is not left on Stripe.

If no browser tool is available, tell the user to open the link and report the visible price. Do not guess from Poke's text alone.
