# Codex Telegram Notifier

A dependency-free, local Codex plugin that sends a private Telegram notice when the official `Stop` hook fires. Configure it with `python scripts/codex_telegram_notifier.py setup`, test it with `test`, and erase credentials with `remove`. Credentials remain only in the user's local config directory. See the Russian README for full instructions and the current official-hook limitation: Stop does not reliably expose success/failure, waiting-for-input, a final answer, or a safe transcript schema.
