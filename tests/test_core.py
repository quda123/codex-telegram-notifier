import logging
import unittest
from pathlib import Path
from unittest.mock import patch
from codex_telegram_notifier.core import Config, format_message, load_config, save_config, send_message, truncate

class CoreTests(unittest.TestCase):
    def test_truncate(self):
        self.assertTrue(truncate("x" * 5000).endswith("…")); self.assertEqual(len(truncate("x" * 5000)), 4096)
    def test_escape(self):
        with patch("codex_telegram_notifier.core.git_info", return_value=("<p>", "a&b", None)):
            self.assertIn("&lt;p&gt;", format_message(".")); self.assertIn("a&amp;b", format_message("."))
    def test_config_and_missing_token(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp, patch("codex_telegram_notifier.core.config_path", return_value=Path(temp) / "c.json"):
            save_config(Config("secret", "42")); self.assertEqual(load_config(), Config("secret", "42"))
            Path(temp, "c.json").write_text('{"bot_token":""}', encoding="utf-8"); self.assertIsNone(load_config())
    def test_network_error_redacts_token(self):
        with self.assertLogs("codex_telegram_notifier", logging.WARNING) as logs, patch("urllib.request.urlopen", side_effect=OSError):
            self.assertFalse(send_message(Config("secret-token", "42"), "x")[0])
        self.assertNotIn("secret-token", "\n".join(logs.output))
    def test_github_remote(self):
        from codex_telegram_notifier.core import git_info
        with patch("subprocess.run") as run:
            run.side_effect = [type("X", (), {"stdout":"main\n"})(), type("X", (), {"stdout":"git@github.com:a/b.git\n"})()]
            self.assertEqual(git_info("."), ("b", "main", "https://github.com/a/b"))
    def test_discover_chats_and_no_updates(self):
        from codex_telegram_notifier.core import discover_chats
        with patch("codex_telegram_notifier.core.telegram", return_value=[]): self.assertEqual(discover_chats("secret"), [])
        updates = [{"message": {"chat": {"id": 1, "first_name": "A", "type": "private"}}}, {"message": {"chat": {"id": 2, "title": "Team", "type": "group"}}}]
        with patch("codex_telegram_notifier.core.telegram", return_value=updates): self.assertEqual(len(discover_chats("secret")), 2)

if __name__ == "__main__": unittest.main()
