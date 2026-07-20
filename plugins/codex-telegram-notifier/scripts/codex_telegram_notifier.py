#!/usr/bin/env python3
"""CLI and Codex Stop-hook entry point."""
from __future__ import annotations
import argparse, getpass, json, logging, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from codex_telegram_notifier.core import Config, data_dir, delete_config, discover_chats, format_message, load_config, save_config, send_message, telegram

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("command", nargs="?", default="hook", choices=["hook", "setup", "test", "status", "disable", "remove"]); args = parser.parse_args()
    data_dir().mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=data_dir() / "notifier.log", level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
    if args.command == "setup":
        print("Создайте бота через @BotFather (/newbot), затем отправьте ему /start.")
        token = getpass.getpass("Telegram Bot Token (не отображается): ").strip(); bot = telegram(token, "getMe")
        chats = discover_chats(token) if bot else []
        if not bot or len(chats) != 1: print("Не найден один чат. Используйте локальный мастер setup_server.py."); return 1
        config = Config(token, chats[0]["id"], bot.get("username", ""), datetime.now(timezone.utc).isoformat()); save_config(config); ok, _ = send_message(config, "✅ Codex Telegram Notifier успешно подключён")
        print("Тест отправлен." if ok else "Настройки сохранены, но тест не отправлен."); return 0
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
