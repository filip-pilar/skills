# Telegram Web Transport

Use this reference when the user chooses Telegram instead of iMessage/Messages.

## Requirement

Telegram Web negotiation requires a browser automation surface in the current agent host. In Codex desktop, force the in-app Browser path first: open or reuse the in-app Browser, load Telegram Web, wait for the user to authenticate manually if needed, then operate on the visible Poke chat. Do not ask the user to paste messages unless browser automation is unavailable after attempting to use it.

Only run this Telegram flow after the user chooses Telegram or explicitly asks for Telegram. On a bare slash-menu invocation, the skill should ask `iMessage/Messages or Telegram Web?` before inspecting browser tabs.

Known-good target:

```text
https://web.telegram.org/k/#@interaction_poke_bot
```

Codex desktop may expose an in-app Browser that can open and inspect Telegram Web. Use it directly through the Browser plugin runtime. Other agents such as Claude Code may work only if they expose a browser/preview automation tool. Do not claim Telegram Web is supported in an environment unless a browser tool is actually available.

## Availability Check

After the user chooses Telegram, before telling the user Telegram Web automation is unavailable:

1. Check whether the prompt or app context says the in-app browser is open.
2. Check whether Browser / in-app Browser plugin capabilities are listed.
3. If Browser is listed, open and follow `browser:control-in-app-browser`.
4. Attempt the Browser bootstrap/control path once:
   - run the Node REPL `js` tool
   - import the Browser plugin's `scripts/browser-client.mjs` by absolute path
   - call `setupBrowserRuntime({ globals: globalThis })`
   - set `browser = await agent.browsers.get("iab")`
   - list tabs or inspect the current tab
5. If the `js` tool is not exposed and tool discovery is available, search for `node_repl js`, then retry step 4.
6. Only then fall back.

In Codex desktop, after Telegram has been chosen, a current URL like `https://web.telegram.org/k/#@interaction_poke_bot` should be treated as enough reason to try Browser control immediately.

Do not conclude `Browser plugin listed, but no callable browser navigation/inspection tools are exposed` just because no direct browser tool appears in the visible tool list. Codex desktop Browser control is normally exposed through the Node REPL `js` runtime.

## Login

The user must authenticate Telegram manually.

Do not:

- request or handle one-time codes
- approve login prompts
- type passwords or 2FA secrets
- scan QR codes on the user's behalf

If Telegram Web is not logged in, tell the user to log in and return.

## Finding Poke

Preferred:

1. Open or navigate the browser to `https://web.telegram.org/k/#@interaction_poke_bot`.
2. If the current in-app Browser is already on that URL, reuse it; do not reload unnecessarily.
3. Confirm the visible chat title is Poke or otherwise clearly the intended Interaction/Poke chat.
4. If the URL does not open the chat after login, then ask the user to open the Poke chat manually.

Fallback:

- Use Telegram Web search only if the user explicitly asks and there is no risk of messaging the wrong contact.
- Do not send messages until the visible chat is confirmed.

## Reading Messages

Use the browser's DOM/snapshot/visible text tools to read the current chat.

Keep extraction scoped to the visible Poke chat. Avoid scraping unrelated chat lists or private conversations. If the visible chat history is insufficient, ask the user to scroll or authorize scrolling within the Poke chat.

## Sending

Default negotiation settings:

- target price: `$0.01/month`, unless the user asks for `$0` or another price
- tone: playful, skeptical, confident, and persistent
- max turns: do not ask; continue until success, a verified hard floor, user stop, or safety stop

Before the first outgoing message, ask a concise start question with the suggested target, such as: `I'll aim for $0.01/month unless you want a different target. Want me to start?`

After the user starts the run, send text replies through the Telegram Web composer. Prefer text over buttons. Do not click buttons that connect accounts, start payments, grant permissions, or perform external side effects.

## Checkout Links

Open checkout links without replacing the Telegram chat tab.

Preferred flow:

1. Save the Telegram/Poke tab id and URL.
2. Open the checkout link or final Stripe URL in a new browser tab/window or controlled read-only browser state.
3. Verify visible price and recurring terms.
4. Stop before payment.
5. Return focus to the Telegram/Poke tab.

If the host cannot open a new tab/window, record the Telegram URL before navigating, verify Stripe, then navigate back to `https://web.telegram.org/k/#@interaction_poke_bot`.

Stop before:

- payment
- card entry
- account connection
- Telegram permission prompts

## Fallback If Browser Automation Is Missing

If no browser automation surface exists, do not pretend to run Telegram. Say this host cannot run the Telegram Web transport directly. Then offer one of:

- use the iMessage transport instead
- ask the user to paste Poke's latest Telegram messages and manually paste back drafted replies
- run the skill in Codex desktop or another host with a browser tool
