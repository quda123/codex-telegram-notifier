---
name: telegram-notifier-setup
description: Safely set up, test, change, or remove local Telegram notifications for Codex without accepting a bot token in chat.
---

Never ask for a Telegram token in chat, a prompt, or a terminal command argument. Check `python scripts/codex_telegram_notifier.py status`. If unconfigured or the user asks to configure/change, explain BotFather and `/start`, then run `python scripts/setup_server.py`; it opens a localhost-only page for the token. After it closes, run status and say `Telegram-уведомления успешно настроены` only if configured. For a test run `python scripts/codex_telegram_notifier.py test`; for removal run `python scripts/codex_telegram_notifier.py remove`.
