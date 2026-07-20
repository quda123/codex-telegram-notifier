# Codex Telegram Notifier

Локальный open-source плагин для Codex: после события `Stop` отправляет личное уведомление в Telegram.

```text
✅ Codex остановил задачу
Проект: my-project
Время: 2026-07-20 12:00 PDT
Статус: остановлена
Ветка: main
GitHub: https://github.com/me/my-project
```

## Требования

Codex Desktop или Codex CLI с поддержкой Plugins/Hooks, Python 3.11+, Windows 10/11, macOS или Linux и собственный Telegram-бот.

## Установка в Codex

В Codex CLI добавьте именно этот публичный GitHub marketplace, затем откройте браузер плагинов и установите запись из него:

```text
codex plugin marketplace add quda123/codex-telegram-notifier --ref main
codex
/plugins
```

В `/plugins` выберите marketplace **quda123 Codex Plugins**, установите **Codex Telegram Notifier**, начните новый сеанс и введите `/hooks`, чтобы просмотреть и подтвердить hook. В ChatGPT Desktop/Codex добавьте этот GitHub marketplace в **Plugins**, выберите его, установите плагин, затем начните новый чат и подтвердите hook в интерфейсе Plugins/Hooks.

Для обновления используйте `codex plugin marketplace upgrade quda123-codex-plugins`, затем переустановите плагин через `/plugins` и начните новый сеанс.

## Настройка Telegram

1. Откройте `@BotFather`, выполните `/newbot` и сохраните полученный токен.
2. Напишите боту любое сообщение.
3. Откройте `https://api.telegram.org/bot<TOKEN>/getUpdates` и возьмите `message.chat.id` (не публикуйте эту ссылку).
4. В корне плагина запустите:

```text
python scripts/codex_telegram_notifier.py setup
python scripts/codex_telegram_notifier.py test
python scripts/codex_telegram_notifier.py status
python scripts/codex_telegram_notifier.py remove
```

`setup` сохраняет токен только в `%APPDATA%\\codex-telegram-notifier\\config.json` на Windows либо `~/.config/codex-telegram-notifier/config.json` на macOS/Linux. На Unix файлу задаются права `0600`.

## Обновление и удаление

Обновите marketplace через Plugins, переустановите плагин и начните новый чат. Для удаления используйте **Uninstall plugin** в Plugins; `python scripts/codex_telegram_notifier.py remove` также удаляет секреты.

## Ограничения

Официальный hook `Stop` не передаёт надёжный итог «успех/ошибка» и не сообщает ожидание пользовательского ввода. Поэтому плагин уведомляет только о факте остановки и не читает нестабильный формат транскрипта. Итоговый ответ Codex также официально не передаётся в `Stop` payload, поэтому намеренно не отправляется в Telegram.

## Безопасность

Токены не попадают в Git, исходный код, логи или исключения. Запрос к Telegram имеет восьмисекундный тайм-аут, одну попытку и не влияет на работу Codex. Сообщение формируется в HTML с экранированием и ограничено 4096 символами.

## Разработка

```text
set PYTHONPATH=plugins/codex-telegram-notifier/src
python -m unittest discover -s tests
python -m compileall plugins/codex-telegram-notifier/src plugins/codex-telegram-notifier/scripts
```

См. [README_EN.md](README_EN.md), [SECURITY.md](SECURITY.md) и [CONTRIBUTING.md](CONTRIBUTING.md).
