import io

import qrcode
import typer
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from . import PROG_NAME, __version__, config, links, server, ssh, stats

app = typer.Typer(help="Manage Xray VLESS+Reality clients over SSH")
console = Console()


def fail(msg: str):
    console.print(f"[red]error:[/red] {msg}")
    raise typer.Exit(1)


def print_qr(text: str):
    qr = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(text)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(out=buf, invert=True)
    print(buf.getvalue())


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Without a command, opens the interactive menu."""
    # banner goes to stderr so command output (links, tables) stays pipe-friendly
    Console(stderr=True).print(f"[bold]{PROG_NAME}[/bold] v{__version__}")
    try:
        ssh.Target()
    except ssh.SSHError as e:
        fail(str(e))
    if ctx.invoked_subcommand is None:
        try:
            ensure_installed()
        except ssh.SSHError as e:
            fail(str(e))
        from . import menu
        menu.run()


def ensure_installed() -> None:
    """Menu startup check: offer to install VLESS if the server has none."""
    if server.status() is server.Status.NOT_INSTALLED:
        console.print("[yellow]VLESS (Xray) на сервере не найден.[/yellow]")
        if Confirm.ask("Установить сейчас?", default=True):
            install_flow(interactive=True)


def install_flow(interactive: bool, port: int = server.DEFAULT_PORT,
                 sni: str = server.DEFAULT_SNI, email: str = "client1") -> None:
    st = server.status()
    if st is server.Status.OK:
        console.print("VLESS уже установлен")
        return
    if st is server.Status.NO_VLESS_INBOUND:
        fail(f"Xray уже настроен, но inbound {config.INBOUND_TAG!r} не найден; "
             "установка не трогает чужой конфиг")
    if interactive:
        port = IntPrompt.ask("Порт", default=port)
        sni = Prompt.ask("SNI / сайт для маскировки Reality", default=sni).strip()
        email = Prompt.ask("Имя первого клиента", default=email).strip()
    if not 1 <= port <= 65535 or port == ssh.Target().port:
        fail("недопустимый порт (или совпадает с SSH-портом)")
    if not config.SNI_RE.match(sni):
        fail("недопустимый SNI")
    try:
        cfg, client = server.initial_install(port, sni, email, say=console.print)
    except config.ConfigError as e:
        fail(str(e))
    console.print("[green]Установка завершена[/green]")
    show_link(cfg, client, qr=True)


@app.command("install")
def install_cmd(yes: bool = typer.Option(False, "--yes", help="без вопросов, значения по умолчанию"),
                port: int = typer.Option(server.DEFAULT_PORT, help="порт Reality"),
                sni: str = typer.Option(server.DEFAULT_SNI, help="SNI / dest"),
                email: str = typer.Option("client1", help="имя первого клиента")):
    """Install Xray + VLESS+Reality on a fresh server and print the first client's link."""
    try:
        if not yes and server.status() is server.Status.NOT_INSTALLED:
            if not Confirm.ask("Установить VLESS на сервер?", default=True):
                return
        install_flow(interactive=not yes, port=port, sni=sni, email=email)
    except ssh.SSHError as e:
        fail(str(e))


@app.command("list")
def list_clients():
    """Show clients from the server config."""
    table = Table("email", "uuid", "flow")
    for c in config.clients(server.read_config()):
        table.add_row(c.get("email", "-"), c["id"], c.get("flow", ""))
    console.print(table)


@app.command()
def bootstrap(yes: bool = typer.Option(False, "--yes", help="confirm xray restart")):
    """One-time: enable gRPC API + stats in config (backs up, restarts xray once)."""
    cfg = server.read_config()
    if server.api_enabled(cfg):
        console.print("API already enabled")
        return
    if not yes:
        fail("this restarts xray (active sessions reconnect); re-run with --yes")
    bak = server.write_config(config.enable_api(cfg))
    console.print(f"backup: {bak}")
    try:
        server.restart()
    except ssh.SSHError as e:
        console.print(f"[red]restart failed, restoring {bak}[/red]")
        server.restore(bak)
        fail(str(e))
    console.print("API enabled")


@app.command()
def add(email: str, qr: bool = typer.Option(True, help="print QR code"),
        params: bool = typer.Option(False, "--params", help="print connection parameters")):
    """Add a client and print its vless:// link."""
    cfg = server.read_config()
    if not server.api_enabled(cfg):
        fail("API not enabled; run `xrayadm bootstrap --yes` first")
    try:
        new, client = config.add_client(cfg, email)
    except config.ConfigError as e:
        fail(str(e))
    bak = server.write_config(new)
    try:
        server.api_add(client)
    except ssh.SSHError as e:
        console.print(f"[red]API add failed, restoring config {bak}[/red]")
        server.restore(bak)
        fail(str(e))
    show_link(new, client, qr, params)


def show_link(cfg: dict, client: dict, qr: bool, params: bool = False):
    pbk = server.public_key(cfg)
    link = links.build_link(cfg, client, pbk)
    console.print(link, soft_wrap=True, highlight=False)
    if params:
        for k, v in links.link_params(cfg, client, pbk).items():
            console.print(f"{k}: {v}", soft_wrap=True, highlight=False)
    if qr:
        print_qr(link)


@app.command()
def remove(email: str):
    """Remove a client by email."""
    cfg = server.read_config()
    if not server.api_enabled(cfg):
        fail("API not enabled; run `xrayadm bootstrap --yes` first")
    try:
        new = config.remove_client(cfg, email)
    except config.ConfigError as e:
        fail(str(e))
    bak = server.write_config(new)
    try:
        server.api_remove(email)
    except ssh.SSHError as e:
        console.print(f"[red]API remove failed, restoring config {bak}[/red]")
        server.restore(bak)
        fail(str(e))
    console.print(f"removed {email} (backup: {bak})")


@app.command()
def link(email: str, qr: bool = typer.Option(True, help="print QR code"),
         params: bool = typer.Option(False, "--params", help="print connection parameters")):
    """Print vless:// link (and QR) for an existing client."""
    cfg = server.read_config()
    client = next((c for c in config.clients(cfg) if c.get("email") == email), None)
    if not client:
        fail(f"client {email!r} not found")
    show_link(cfg, client, qr, params)


@app.command("stats")
def stats_cmd(reset: bool = typer.Option(False, "--reset")):
    """Per-client traffic counters since xray start (or last reset)."""
    data = stats.fetch(reset)
    table = Table("email", "up", "down")
    for email, v in sorted(data.items()):
        table.add_row(email, stats.human(v["uplink"]), stats.human(v["downlink"]))
    console.print(table)


@app.command()
def backups():
    """List config backups on the server (newest first)."""
    for b in server.list_backups():
        print(b)


@app.command()
def backup():
    """Make a config backup now."""
    print(server.backup())


@app.command()
def rollback(path: str = typer.Argument(None, help="backup path; default newest"),
             yes: bool = typer.Option(False, "--yes", help="confirm xray restart")):
    """Restore a config backup and restart xray."""
    bl = server.list_backups()
    path = path or (bl[0] if bl else None)
    if not path:
        fail("no backups")
    if not yes:
        fail(f"would restore {path} and restart xray; re-run with --yes")
    server.restore(path)
    console.print(f"restored {path}")


if __name__ == "__main__":
    app()
