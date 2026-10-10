import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ENV_FILES = (Path.cwd() / ".env", Path.home() / ".config" / "xrayadm" / ".env")


def load_env(files=ENV_FILES) -> None:
    """Load KEY=VALUE lines from .env files into os.environ (real env vars win)."""
    for f in files:
        if not f.is_file():
            continue
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.removeprefix("export ").strip()
            val = val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            os.environ.setdefault(key, val)


class SSHError(RuntimeError):
    pass


def _host() -> str:
    load_env()
    host = os.environ.get("XRAYADM_HOST")
    if not host:
        raise SSHError("XRAYADM_HOST is not set; copy .env.example to .env and fill it in")
    return host


@dataclass(frozen=True)
class Target:
    host: str = field(default_factory=_host)
    port: int = field(default_factory=lambda: int(os.environ.get("XRAYADM_PORT", "22")))
    user: str = field(default_factory=lambda: os.environ.get("XRAYADM_USER", "root"))


def run(cmd: str, target: Target | None = None, input: str | None = None,
        timeout: int = 30) -> str:
    """Run a shell command on the server, return stdout."""
    target = target or Target()
    args = ["ssh", "-p", str(target.port), "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=10", f"{target.user}@{target.host}", cmd]
    p = subprocess.run(args, input=input, capture_output=True, text=True,
                       timeout=timeout)
    if p.returncode != 0:
        raise SSHError(f"`{cmd}` failed ({p.returncode}): {(p.stderr or p.stdout).strip()}")
    return p.stdout
