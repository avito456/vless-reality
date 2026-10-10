"""Interactive text menu; reuses the CLI command functions."""
import subprocess

import typer
from rich.prompt import Confirm, IntPrompt, Prompt

from . import cli, config, server, ssh

ITEMS = [
    ("Список клиентов", "list"),
    ("Добавить клиента", "add"),
    ("Удалить клиента", "remove"),
    ("Ссылка / QR клиента", "link"),
    ("Статистика трафика", "stats"),
    ("Создать бэкап конфига", "backup"),
    ("Откатить конфиг из бэкапа", "rollback"),
    ("Включить API (bootstrap, один рестарт xray)", "bootstrap"),
]


def pick_client() -> str | None:
    emails = [c.get("email", "-") for c in config.clients(server.read_config())]
    for i, e in enumerate(emails, 1):
        cli.console.print(f"  {i}. {e}")
    n = IntPrompt.ask("Номер клиента (0 - отмена)", default=0)
    return emails[n - 1] if 1 <= n <= len(emails) else None


def pick_backup() -> str | None:
    bl = server.list_backups()
    for i, b in enumerate(bl, 1):
        cli.console.print(f"  {i}. {b.rsplit('/', 1)[-1]}")
    n = IntPrompt.ask("Номер бэкапа (0 - отмена)", default=0)
    return bl[n - 1] if 1 <= n <= len(bl) else None


def pick_format() -> tuple[bool, bool]:
    """Returns (qr, params). The vless:// string is always printed."""
    cli.console.print("  1. QR + строка\n  2. Только строка\n  3. Строка + параметры подключения")
    n = IntPrompt.ask("Формат вывода", choices=["1", "2", "3"], default=1, show_choices=False)
    return n == 1, n == 3


def action(key: str) -> None:
    if key == "list":
        cli.list_clients()
    elif key == "add":
        email = Prompt.ask("Имя клиента (email, A-Z a-z 0-9 . _ -)").strip()
        if email:
            qr, params = pick_format()
            cli.add(email, qr=qr, params=params)
    elif key == "remove":
        email = pick_client()
        if email and Confirm.ask(f"Удалить клиента {email}?", default=False):
            cli.remove(email)
    elif key == "link":
        email = pick_client()
        if email:
            qr, params = pick_format()
            cli.link(email, qr=qr, params=params)
    elif key == "stats":
        cli.stats_cmd(reset=Confirm.ask("Сбросить счётчики после показа?", default=False))
    elif key == "backup":
        cli.backup()
    elif key == "rollback":
        path = pick_backup()
        if path and Confirm.ask("Откат перезапустит xray. Продолжить?", default=False):
            cli.rollback(path, yes=True)
    elif key == "bootstrap":
        if Confirm.ask("Это перезапустит xray (сессии переподключатся). Продолжить?", default=False):
            cli.bootstrap(yes=True)


def run() -> None:
    cli.console.print(f"Сервер: {ssh.Target().host}")
    while True:
        cli.console.print()
        for i, (title, _) in enumerate(ITEMS, 1):
            cli.console.print(f"  {i}. {title}")
        cli.console.print("  0. Выход")
        try:
            n = IntPrompt.ask("Выберите пункт", default=0)
        except (KeyboardInterrupt, EOFError):
            cli.console.print()
            return
        if n == 0:
            return
        if not 1 <= n <= len(ITEMS):
            cli.console.print("[red]нет такого пункта[/red]")
            continue
        try:
            action(ITEMS[n - 1][1])
        except typer.Exit:
            pass  # error already printed by cli.fail
        except (ssh.SSHError, subprocess.TimeoutExpired, OSError) as e:
            cli.console.print(f"[red]error:[/red] {e}")
        except (KeyboardInterrupt, EOFError):
            cli.console.print("\nотменено")
