"""Operations on the remote Xray host. Every config write is preceded by a backup."""
import json
import secrets
import shlex
import subprocess
import time
from enum import Enum

from . import config, ssh

CONFIG_PATH = "/usr/local/etc/xray/config.json"
BACKUP_DIR = "/usr/local/etc/xray/backups"
API_ADDR = "127.0.0.1:10085"
KEEP_BACKUPS = 20


def read_config() -> dict:
    return json.loads(ssh.run(f"cat {CONFIG_PATH}"))


def backup() -> str:
    """Copy current config to BACKUP_DIR, prune old ones, return backup path."""
    name = f"{BACKUP_DIR}/config.{time.strftime('%Y%m%d-%H%M%S')}.json"
    ssh.run(f"mkdir -p {BACKUP_DIR} && cp -p {CONFIG_PATH} {name} && "
            f"ls -1t {BACKUP_DIR}/config.*.json | tail -n +{KEEP_BACKUPS + 1} | xargs -r rm --")
    return name


def list_backups() -> list[str]:
    out = ssh.run(f"ls -1t {BACKUP_DIR}/config.*.json 2>/dev/null || true")
    return [l for l in out.splitlines() if l]


def write_config(cfg: dict) -> str:
    """Backup, validate with `xray run -test`, then atomically replace. Returns backup path."""
    bak = backup()
    tmp = f"{CONFIG_PATH}.new.json"  # xray picks the format by extension
    ssh.run(f"cat > {tmp}", input=json.dumps(cfg, indent=2) + "\n")
    try:
        ssh.run(f"xray run -test -c {tmp}")
    except ssh.SSHError:
        ssh.run(f"rm -f {tmp}")
        raise
    ssh.run(f"chmod --reference={CONFIG_PATH} {tmp} && mv {tmp} {CONFIG_PATH}")
    return bak


def restore(backup_path: str) -> None:
    """Restore a backup (after backing up the current config) and restart xray."""
    ssh.run(f"xray run -test -c {shlex.quote(backup_path)}")
    backup()
    ssh.run(f"cp -p {shlex.quote(backup_path)} {CONFIG_PATH}")
    restart()


def restart(wait: int = 90) -> None:
    """Restart xray detached on the server, then poll over fresh SSH connections.

    The restart can drop our own SSH session if the client's traffic goes through
    this very VPN, so the command must not depend on the connection staying up.
    """
    try:
        ssh.run("nohup sh -c 'sleep 1; systemctl restart xray' >/dev/null 2>&1 &", timeout=15)
    except (ssh.SSHError, subprocess.TimeoutExpired):
        pass
    time.sleep(3)
    deadline = time.time() + wait
    while time.time() < deadline:
        try:
            if ssh.run("systemctl is-active xray", timeout=10).strip() == "active":
                return
        except (ssh.SSHError, subprocess.TimeoutExpired):
            pass
        time.sleep(3)
    raise ssh.SSHError(f"xray not active {wait}s after restart")


def api_enabled(cfg: dict) -> bool:
    return any(i.get("tag") == "api" for i in cfg.get("inbounds", []))


def _check_count(out: str, verb: str) -> None:
    # xray api exits 0 even when it failed, so the summary line is the only signal
    if f"{verb} 1 user(s) in total" not in out:
        raise ssh.SSHError(out.strip() or f"xray api {verb} no output")


def api_add(client: dict) -> None:
    # adu builds a full inbound, so port/listen are required even though only users are added
    payload = {"inbounds": [{"tag": config.INBOUND_TAG, "protocol": "vless",
                             "listen": "0.0.0.0", "port": 443,
                             "settings": {"clients": [client], "decryption": "none"}}]}
    out = ssh.run(f"f=$(mktemp --suffix=.json) && cat > $f && xray api adu -s {API_ADDR} $f 2>&1;"
                  " r=$?; rm -f $f; exit $r", input=json.dumps(payload))
    _check_count(out, "Added")


def api_remove(email: str) -> None:
    out = ssh.run(f"xray api rmu -s {API_ADDR} -tag={config.INBOUND_TAG} {shlex.quote(email)} 2>&1")
    _check_count(out, "Removed")


def public_key(cfg: dict) -> str:
    priv = config.inbound(cfg)["streamSettings"]["realitySettings"]["privateKey"]
    out = ssh.run(f"xray x25519 -i {shlex.quote(priv)}")
    for line in out.splitlines():
        k, _, v = line.partition(":")
        if k.strip().lower().startswith(("password", "public key", "publickey")):
            return v.strip()
    raise ssh.SSHError("public key not found in `xray x25519` output")


# ---- first-time installation -------------------------------------------------

INSTALL_URL = "https://github.com/XTLS/Xray-install/raw/main/install-release.sh"
DEFAULT_PORT = 443
DEFAULT_SNI = "www.microsoft.com"


class Status(Enum):
    NOT_INSTALLED = "not_installed"        # no xray binary / no config / config without inbounds
    NO_VLESS_INBOUND = "no_vless_inbound"  # xray configured, but not by us
    OK = "ok"


def status() -> Status:
    out = ssh.run(f"command -v xray >/dev/null 2>&1 && echo bin; test -f {CONFIG_PATH} && echo cfg; true")
    if "bin" not in out.split() or "cfg" not in out.split():
        return Status.NOT_INSTALLED
    try:
        cfg = read_config()
    except json.JSONDecodeError:
        return Status.NO_VLESS_INBOUND
    if not cfg.get("inbounds"):
        return Status.NOT_INSTALLED  # e.g. the empty default config left by the installer
    try:
        config.inbound(cfg)
    except config.ConfigError:
        return Status.NO_VLESS_INBOUND
    return Status.OK


def port_busy(port: int) -> bool:
    return bool(ssh.run(f'ss -ltnH "sport = :{int(port)}"').strip())


def install_xray() -> None:
    """Install Xray with the official XTLS/Xray-install script (needs GitHub access)."""
    ssh.run(
        "command -v curl >/dev/null 2>&1 || { apt-get update -qq && apt-get install -y -qq curl "
        "|| dnf install -y curl || yum install -y curl; } >/dev/null 2>&1; "
        f"f=$(mktemp) && curl -fsSL {INSTALL_URL} -o $f && bash $f install 2>&1; r=$?; rm -f $f; exit $r",
        timeout=300)
    ssh.run("xray version")


def generate_keys() -> tuple[str, str]:
    """Return (private_key, short_id). The public key is derived later by `public_key`."""
    out = ssh.run("xray x25519")
    for line in out.splitlines():
        k, _, v = line.partition(":")
        if k.strip().lower().replace(" ", "") == "privatekey":
            return v.strip(), secrets.token_hex(8)
    raise ssh.SSHError("private key not found in `xray x25519` output")


def open_firewall(port: int) -> str:
    port = int(port)
    return ssh.run(
        f"if command -v ufw >/dev/null 2>&1 && ufw status | grep -q 'Status: active'; then "
        f"ufw allow {port}/tcp >/dev/null && echo 'ufw: opened {port}/tcp'; "
        "elif command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then "
        f"firewall-cmd --permanent --add-port={port}/tcp >/dev/null && firewall-cmd --reload >/dev/null "
        f"&& echo 'firewalld: opened {port}/tcp'; "
        "else echo 'no active firewall found'; fi").strip()


def enable_bbr() -> str:
    return ssh.run(
        "if [ \"$(sysctl -n net.ipv4.tcp_congestion_control)\" = bbr ]; then echo 'BBR already enabled'; "
        "else printf 'net.core.default_qdisc=fq\\nnet.ipv4.tcp_congestion_control=bbr\\n' "
        "> /etc/sysctl.d/99-bbr.conf && sysctl --system >/dev/null && echo 'BBR enabled'; fi").strip()


def initial_install(port: int, sni: str, email: str, say=print) -> tuple[dict, dict]:
    """Install Xray if needed and write a fresh VLESS+Reality config. Returns (cfg, client).

    The previous config is an empty installer default, so a failed restart is not rolled
    back: the new config stays on the server for inspection.
    """
    if port_busy(port):
        raise ssh.SSHError(f"port {port} is already in use on the server")
    if ssh.run("command -v xray >/dev/null 2>&1 && echo yes; true").strip() != "yes":
        say("Устанавливаю Xray (официальный скрипт XTLS/Xray-install)...")
        install_xray()
    ssh.run(f"mkdir -p {CONFIG_PATH.rsplit('/', 1)[0]} && "
            f"test -f {CONFIG_PATH} || echo '{{}}' > {CONFIG_PATH}")
    say("Генерирую ключи Reality...")
    priv, short_id = generate_keys()
    cfg, client = config.build_initial_config(port, sni, priv, short_id, email)
    say("Открываю порт в файрволе...")
    say(open_firewall(port))
    try:
        say(enable_bbr())
    except ssh.SSHError as e:  # nice to have, not essential
        say(f"BBR пропущен: {e}")
    say("Записываю конфиг и перезапускаю Xray...")
    write_config(cfg)
    ssh.run("systemctl enable xray >/dev/null 2>&1; true")
    restart()
    return cfg, client
