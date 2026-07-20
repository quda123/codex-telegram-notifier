"""Configuration, message formatting, and Telegram delivery."""
from __future__ import annotations

import html
import json
import logging
import os
import subprocess
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

MAX_MESSAGE = 4096
LOG = logging.getLogger("codex_telegram_notifier")

@dataclass(frozen=True)
class Config:
    bot_token: str
    chat_id: str

def data_dir() -> Path:
    """Return the per-user configuration directory without hard-coded paths."""
    root = os.getenv("APPDATA") if os.name == "nt" else os.getenv("XDG_CONFIG_HOME")
    return Path(root) / "codex-telegram-notifier" if root else Path.home() / ".config" / "codex-telegram-notifier"

def config_path() -> Path:
    return data_dir() / "config.json"

def save_config(config: Config) -> None:
    """Persist secrets locally with owner-only permissions where supported."""
    path = config_path(); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config)), encoding="utf-8")
    if os.name != "nt": path.chmod(0o600)

def load_config() -> Config | None:
    """Load local credentials, returning None for missing or malformed settings."""
    try:
        raw = json.loads(config_path().read_text(encoding="utf-8"))
        token, chat_id = raw.get("bot_token", ""), str(raw.get("chat_id", ""))
        return Config(token, chat_id) if token and chat_id else None
    except (OSError, ValueError, TypeError):
        return None

def delete_config() -> bool:
    """Remove the local credentials file."""
    try: config_path().unlink(); return True
    except FileNotFoundError: return False

def truncate(text: str, limit: int = MAX_MESSAGE) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"

def git_info(cwd: str) -> tuple[str | None, str | None, str | None]:
    """Best-effort repository name, branch, and GitHub URL; never executes a shell."""
    def git(*args: str) -> str | None:
        try: return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=2, check=True).stdout.strip() or None
        except (OSError, subprocess.SubprocessError): return None
    branch, remote = git("branch", "--show-current"), git("remote", "get-url", "origin")
    url = remote.removesuffix(".git") if remote and "github.com" in remote else None
    if url and url.startswith("git@github.com:"): url = "https://github.com/" + url.split(":", 1)[1]
    return (url.rsplit("/", 1)[-1] if url else Path(cwd).name), branch, url

def format_message(cwd: str, session_id: str | None = None) -> str:
    """Make a safe, Telegram HTML notification within Telegram's limit."""
    project, branch, url = git_info(cwd); fields = ["✅ <b>Codex остановил задачу</b>", f"<b>Проект:</b> {html.escape(project or Path(cwd).name)}", f"<b>Время:</b> {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}", "<b>Статус:</b> остановлена"]
    if branch: fields.append(f"<b>Ветка:</b> {html.escape(branch)}")
    if url: fields.append(f"<b>GitHub:</b> {html.escape(url)}")
    # Session IDs can identify a local conversation; do not transmit them by default.
    return truncate("\n".join(fields))

def send_message(config: Config, message: str, timeout: float = 8) -> tuple[bool, str | None]:
    """Send once to Telegram; error text deliberately excludes credentials."""
    payload = json.dumps({"chat_id": config.chat_id, "text": message, "parse_mode": "HTML"}).encode()
    request = urllib.request.Request(f"https://api.telegram.org/bot{config.bot_token}/sendMessage", payload, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return (200 <= response.status < 300, None)
    except (urllib.error.URLError, TimeoutError, OSError):
        LOG.warning("Telegram notification failed (network or credentials)")
        return False, "network or credentials error"
