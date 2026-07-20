#!/usr/bin/env python3
"""One-time localhost-only Telegram setup page."""
from __future__ import annotations
import json, secrets, sys, threading, time, webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from codex_telegram_notifier.core import Config, discover_chats, save_config, send_message, telegram

def serve(lifetime: int = 120) -> None:
    """Run a one-time setup server; credentials exist only in this process until saved."""
    state = {"key": secrets.token_urlsafe(32), "token": None, "bot": None, "chats": [], "used": False, "started": 0.0}
    def page(body: str) -> bytes:
        return f'<!doctype html><meta charset="utf-8"><meta http-equiv="Cache-Control" content="no-store"><title>Настройка Codex Telegram Notifier</title><h1>Настройка Codex Telegram Notifier</h1>{body}'.encode()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: object) -> None: pass
        def local(self) -> bool:
            return self.headers.get("Host", "").split(":")[0] in {"127.0.0.1", "localhost"}
        def reply(self, body: str, status: int = 200) -> None:
            self.send_response(status); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(page(body))
        def do_GET(self) -> None:
            if not self.local(): self.send_error(403); return
            if self.path == "/poll":
                if state["token"] and time.monotonic() - state["started"] < lifetime:
                    state["chats"] = discover_chats(state["token"])
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(json.dumps({"count": len(state["chats"])}).encode()); return
            if state["token"]:
                self.reply(f'<p>Теперь откройте Telegram и отправьте вашему боту <b>/start</b>.</p><p id="s">Ожидание…</p><script>setInterval(async()=>{{let r=await fetch("/poll");let d=await r.json();if(d.count)location.reload()}},2500)</script>'); return
            self.reply(f'<p>Откройте Telegram → @BotFather → /newbot, затем отправьте боту /start.</p><form method="post" autocomplete="off"><input type="hidden" name="setup" value="{state["key"]}"><label>Telegram Bot Token <input type="password" name="token" required autocomplete="new-password"></label><button>Проверить</button></form>')
        def do_POST(self) -> None:
            if not self.local() or self.headers.get("Origin") != f"http://127.0.0.1:{self.server.server_port}": self.send_error(403); return
            data = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode(), keep_blank_values=True)
            key, choice = data.get("setup", [""])[0], data.get("chat", [""])[0]
            if state["used"] or not secrets.compare_digest(key, state["key"]): self.send_error(403); return
            if choice and state["token"]:
                chat = next((c for c in state["chats"] if c["id"] == choice), None)
                if not chat: self.reply("Выберите чат из списка.", 400); return
                state["used"] = True; config = Config(state["token"], chat["id"], state["bot"].get("username", ""), datetime.now(timezone.utc).isoformat()); save_config(config); send_message(config, "✅ Codex Telegram Notifier успешно подключён"); state["token"] = None
                self.reply("<h2>✅ Telegram-уведомления успешно настроены</h2><p>Можно закрыть это окно.</p>"); threading.Thread(target=self.server.shutdown, daemon=True).start(); return
            token = data.get("token", [""])[0]
            bot = telegram(token, "getMe")
            if not bot: self.reply("Токен не проверен. Проверьте его и интернет.", 400); return
            state.update(token=token, bot=bot, started=time.monotonic()); state["chats"] = discover_chats(token)
            if len(state["chats"]) == 1:
                chat = state["chats"][0]; self.reply(f'<form method="post"><input type="hidden" name="setup" value="{state["key"]}"><input type="hidden" name="chat" value="{chat["id"]}"><button>Подключить {chat["name"]}</button></form>'); return
            if len(state["chats"]) > 1:
                buttons = ''.join(f'<button name="chat" value="{c["id"]}">{c["name"]} · {c["type"]} · {c["id"]}</button>' for c in state["chats"]); self.reply(f'<p>Выберите чат:</p><form method="post"><input type="hidden" name="setup" value="{state["key"]}">{buttons}</form>'); return
            self.reply('<p>Теперь откройте Telegram и отправьте вашему боту <b>/start</b>. Эта страница проверяет обновления каждые 2.5 секунды до двух минут.</p><script>setInterval(async()=>{let r=await fetch("/poll");let d=await r.json();if(d.count)location.reload()},2500)</script>')
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler); threading.Timer(lifetime, server.shutdown).start(); webbrowser.open(f"http://127.0.0.1:{server.server_port}/"); server.serve_forever()
if __name__ == "__main__": serve()
