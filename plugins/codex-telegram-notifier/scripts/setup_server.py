#!/usr/bin/env python3
"""One-time localhost Telegram setup with an explicit state machine."""
from __future__ import annotations
import html, json, secrets, sys, threading, time, webbrowser
from datetime import datetime, timezone
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from codex_telegram_notifier.core import Config, discover_chats, save_config, send_message, telegram
class State(str, Enum): ENTER_TOKEN="enter_token"; WAITING_FOR_CHAT="waiting_for_chat"; CHOOSE_CHAT="choose_chat"; SAVING="saving"; COMPLETED="completed"; EXPIRED="expired"; ERROR="error"
def serve(lifetime: int = 120) -> None:
    state={"phase":State.ENTER_TOKEN,"key":secrets.token_urlsafe(32),"token":None,"bot":{},"chats":[],"used":False,"started":0.0,"error":""}
    def save(chat: dict) -> bool:
        state["phase"]=State.SAVING; token=state["token"]; config=Config(token, chat["id"], state["bot"].get("username",""), datetime.now(timezone.utc).isoformat())
        if not send_message(config,"✅ Codex Telegram Notifier успешно подключён")[0]: state["phase"]=State.ERROR; state["error"]="Тестовое сообщение не отправлено. Начните настройку заново."; return False
        save_config(config); state.update(phase=State.COMPLETED, used=True, token=None); return True
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_:object)->None: pass
        def local(self)->bool: return self.headers.get("Host","").split(":")[0] in {"127.0.0.1","localhost"}
        def out(self,body:str,status:int=200,typ:str="text/html; charset=utf-8")->None:
            self.send_response(status); self.send_header("Content-Type",typ); self.send_header("Cache-Control","no-store"); self.end_headers(); self.wfile.write(body.encode())
        def page(self,body:str)->None: self.out(f'<!doctype html><meta charset="utf-8"><title>Настройка Codex Telegram Notifier</title><h1>Настройка Codex Telegram Notifier</h1>{body}')
        def do_GET(self)->None:
            if not self.local(): self.send_error(403); return
            if self.path=="/poll":
                if time.monotonic()-state["started"]>lifetime and state["phase"]==State.WAITING_FOR_CHAT: state["phase"]=State.EXPIRED
                if state["phase"]==State.WAITING_FOR_CHAT:
                    state["chats"]=discover_chats(state["token"])
                    if len(state["chats"])==1: save(state["chats"][0])
                    elif len(state["chats"])>1: state["phase"]=State.CHOOSE_CHAT
                redirect={State.COMPLETED:"/complete",State.CHOOSE_CHAT:"/choose"}.get(state["phase"])
                self.out(json.dumps({"status":state["phase"].value,"redirect":redirect}),typ="application/json"); return
            if self.path=="/complete":
                self.page("<h2>✅ Telegram-уведомления успешно настроены</h2><p>Можно закрыть это окно.</p>"); threading.Thread(target=self.server.shutdown,daemon=True).start(); return
            if self.path=="/choose":
                if state["phase"]!=State.CHOOSE_CHAT: self.send_error(404); return
                rows=''.join(f'<button name="chat" value="{html.escape(c["id"],quote=True)}">{html.escape(c["name"])} · {html.escape(c.get("username", ""))} · {html.escape(c["type"])} · {html.escape(c["id"])}</button>' for c in state["chats"])
                self.page(f'<p>Выберите чат:</p><form method="post"><input type="hidden" name="setup" value="{state["key"]}">{rows}</form>'); return
            if state["phase"]==State.EXPIRED: self.page("<p>Время настройки истекло. Запустите настройку ещё раз.</p>"); return
            if state["phase"]==State.ERROR: self.page(f'<p>{html.escape(state["error"])}</p>'); return
            if state["phase"]==State.WAITING_FOR_CHAT: self.page('<p>Теперь откройте Telegram и отправьте вашему боту <b>/start</b>.</p><script>const poll=setInterval(async()=>{let d=await(await fetch("/poll")).json();if(d.redirect||d.status==="error"||d.status==="expired"){clearInterval(poll);location=d.redirect||"/"}},2500)</script>'); return
            self.page(f'<form method="post" autocomplete="off"><input type="hidden" name="setup" value="{state["key"]}"><label>Telegram Bot Token <input type="password" name="token" required autocomplete="new-password"></label><button>Проверить</button></form>')
        def do_POST(self)->None:
            if not self.local() or self.headers.get("Origin")!=f"http://127.0.0.1:{self.server.server_port}": self.send_error(403); return
            data=parse_qs(self.rfile.read(int(self.headers.get("Content-Length","0"))).decode(),keep_blank_values=True); key=data.get("setup",[""])[0]
            if state["used"] or not secrets.compare_digest(key,state["key"]): self.send_error(403); return
            choice=data.get("chat",[""])[0]
            if choice and state["phase"]==State.CHOOSE_CHAT:
                chat=next((c for c in state["chats"] if c["id"]==choice),None)
                if chat and save(chat): self.send_response(303); self.send_header("Location","/complete"); self.end_headers()
                else: self.send_response(303); self.send_header("Location","/"); self.end_headers()
                return
            if state["phase"]!=State.ENTER_TOKEN: self.send_error(409); return
            token=data.get("token",[""])[0]; bot=telegram(token,"getMe")
            if not bot: state.update(phase=State.ERROR,error="Токен не проверен. Проверьте его и интернет."); self.send_response(303); self.send_header("Location","/"); self.end_headers(); return
            state.update(token=token,bot=bot,started=time.monotonic(),phase=State.WAITING_FOR_CHAT); self.send_response(303); self.send_header("Location","/"); self.end_headers()
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler); threading.Timer(lifetime,server.shutdown).start(); webbrowser.open(f"http://127.0.0.1:{server.server_port}/"); server.serve_forever()
if __name__=="__main__": serve()
