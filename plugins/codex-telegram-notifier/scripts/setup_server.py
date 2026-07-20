#!/usr/bin/env python3
"""One-time localhost-only Telegram setup page; secrets never enter Codex chat."""
from __future__ import annotations
import json, secrets, sys, threading, time, webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from codex_telegram_notifier.core import Config, discover_chats, save_config, send_message, telegram

PAGE = '''<!doctype html><meta charset="utf-8"><title>Настройка Codex Telegram Notifier</title><h1>Настройка Codex Telegram Notifier</h1><p>1. Откройте Telegram → @BotFather → /newbot. 2. Скопируйте токен. 3. Напишите созданному боту <b>/start</b>.</p><form method="post" autocomplete="off"><input type="hidden" name="setup" value="{key}"><label>Telegram Bot Token <input type="password" name="token" required autocomplete="new-password"></label><button>Проверить и подключить</button></form><p>{message}</p>'''

def serve(lifetime: int = 600) -> None:
    key, used = secrets.token_urlsafe(32), False
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: object) -> None: pass
        def reply(self, message: str = "") -> None:
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(PAGE.format(key=key, message=message).encode())
        def do_GET(self) -> None:
            if self.headers.get("Host", "").split(":")[0] not in {"127.0.0.1", "localhost"}: self.send_error(403); return
            self.reply()
        def do_POST(self) -> None:
            nonlocal used
            if self.headers.get("Origin") not in {None, f"http://127.0.0.1:{self.server.server_port}"}: self.send_error(403); return
            length = int(self.headers.get("Content-Length", "0")); fields = dict(x.split("=", 1) for x in self.rfile.read(length).decode().split("&") if "=" in x)
            token = fields.get("token", "").replace("%3A", ":")
            if used or not secrets.compare_digest(fields.get("setup", ""), key): self.send_error(403); return
            bot = telegram(token, "getMe")
            if not bot: self.reply("Токен не проверен. Проверьте его и интернет."); return
            chats = discover_chats(token)
            if len(chats) != 1: self.reply("Отправьте боту /start и повторите. Если чатов несколько, используйте резервный CLI."); return
            used = True; config = Config(token, chats[0]["id"], bot.get("username", ""), datetime.now(timezone.utc).isoformat()); save_config(config); send_message(config, "✅ Codex Telegram Notifier успешно подключён")
            self.reply("<b>Настройка завершена. Можно закрыть это окно.</b>"); threading.Thread(target=self.server.shutdown, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler); threading.Timer(lifetime, server.shutdown).start(); webbrowser.open(f"http://127.0.0.1:{server.server_port}/"); server.serve_forever()
if __name__ == "__main__": serve()
