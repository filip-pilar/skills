# Telegram Web Transport

Use this procedure only after the user chooses Telegram. Telegram requires browser automation against:

```text
https://web.telegram.org/k/#@interaction_poke_bot
```

## Connect to Telegram

When `browser:control-in-app-browser` is available, load and follow it before any browser action or claim that automation is unavailable. Let that skill own browser selection, bootstrap, documentation, tab control, and recovery; do not duplicate or improvise its runtime mechanics here. In another host, use its documented browser or preview automation. Do not claim Telegram support unless the selected host exposes such a surface. Open or reuse the target URL, reusing an existing Poke tab when present.

The user must authenticate Telegram manually. Never request or handle SMS codes, QR approval, passwords, or 2FA secrets. If authentication is needed, ask the user to complete it in the selected browser and tell you when it is ready.

After authentication, confirm that the visible chat is Poke or clearly the intended Interaction chat before sending. If the target URL does not open it, ask the user to open the chat manually. Use Telegram search only when explicitly requested and there is no risk of messaging the wrong contact.

## Read and send

Read only the visible Poke conversation through the browser's documented page-inspection surface. Do not scrape unrelated chats. If the needed history is not visible, ask the user to scroll or authorize scrolling inside the Poke chat.

After the root run-level start approval, send text through the composer without repeated send confirmations. Avoid rich buttons; never select controls for payments, account connection, permissions, or other side effects.

## Verify and restore

Before opening a checkout, save the Telegram tab id and URL. Follow the root verification flow in a new tab, window, or controlled read-only browser state when possible, then return focus to the Poke tab.

If a separate tab is impossible, record the Telegram URL, navigate to checkout for verification, then return to the target Poke URL. Stop before payment or card entry.

## Browser fallback

Do not offer paste-and-relay as the normal Telegram flow. Only after the applicable Browser-skill or host capability attempt actually fails may you explain that this host cannot automate Telegram Web. Do not pretend to run it. Offer the user these choices:

- use iMessage instead
- manually paste Poke's latest message and paste back drafted replies
- run the skill in Codex desktop or another host with browser automation
