# Changelog

## 0.2.3 — 2026-07-20

- Stop setup-page polling and return to the safe status page when test delivery fails or setup expires.

## 0.2.2 — 2026-07-20

- Fix setup polling loop with explicit setup states and automatic completion for one chat.

## 0.2.1 — 2026-07-20

- Keep a verified token only in setup-server memory while polling Telegram every 2.5 seconds for `/start`.
- Add in-page chat selection for multiple chats and stricter localhost request validation.

## 0.2.0 — 2026-07-20

- Add a localhost-only browser setup wizard that keeps the Telegram token out of Codex chat.
- Add the `telegram-notifier-setup` skill and simplified setup prompts.

## 0.1.1 — 2026-07-20

- Fix GitHub distribution: add the official repo marketplace manifest and move the plugin to `plugins/codex-telegram-notifier`.

## 0.1.0 — 2026-07-20

- Initial local Telegram notification plugin using the official Codex `Stop` hook.
