#!/usr/bin/env python3
"""CLI and Codex Stop-hook entry point."""
from __future__ import annotations
import argparse, json, logging, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from codex_telegram_notifier.core import Config, data_dir, delete_config, format_message, load_config, save_config, send_message

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("command", nargs="?", default="hook", choices=["hook", "setup", "test", "status", "disable", "remove"]); args = parser.parse_args()
    data_dir().mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=data_dir() / "notifier.log", level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    if args.command == "setup":
        print("Создайте бота: Telegram → @BotFather → /newbot. Затем отправьте боту сообщение и откройте https://api.telegram.org/bot<TOKEN>/getUpdates, чтобы найти chat.id.")
        save_config(Config(input("TELEGRAM_BOT_TOKEN: ").strip(), input("TELEGRAM_CHAT_ID: ").strip())); ok, _ = send_message(load_config(), "✅ Codex Telegram Notifier настроен") # type: ignore[arg-type]
        print("Тест отправлен." if ok else "Не удалось отправить тест. Проверьте токен, chat_id и интернет."); return 0
    if args.command == "remove": print("Конфигурация удалена." if delete_config() else "Конфигурация не найдена."); return 0
    config = load_config()
    if args.command == "status": print("Настроено." if config else "Не настроено."); return 0
    if args.command == "disable": print("Отключение: удалите плагин через Plugins или /plugins."); return 0
    if not config: return 0
    if args.command == "test": ok, _ = send_message(config, "✅ Тест Codex Telegram Notifier"); print("Отправлено." if ok else "Не отправлено."); return 0
    try: event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError): event = {}
    send_message(config, format_message(str(event.get("cwd") or Path.cwd()), event.get("session_id"))); return 0
if __name__ == "__main__": raise SystemExit(main())
