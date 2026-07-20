# Contributing

Use Python 3.11+, keep the standard-library-only runtime, add a focused test for non-trivial behavior, and run `PYTHONPATH=plugins/codex-telegram-notifier/src python -m unittest discover -s tests` plus `python -m compileall plugins/codex-telegram-notifier/src plugins/codex-telegram-notifier/scripts` before opening a pull request. Never commit credentials or local configuration.
