import json
import re

from . import ssh
from .server import API_ADDR

STAT_RE = re.compile(r"^user>>>(.+)>>>traffic>>>(uplink|downlink)$")


def fetch(reset: bool = False) -> dict[str, dict[str, int]]:
    flag = " -reset" if reset else ""
    out = ssh.run(f"xray api statsquery -s {API_ADDR} -pattern 'user>>>'{flag}")
    result: dict[str, dict[str, int]] = {}
    for s in json.loads(out or "{}").get("stat", []):
        m = STAT_RE.match(s["name"])
        if m:
            result.setdefault(m[1], {"uplink": 0, "downlink": 0})[m[2]] = int(s.get("value", 0))
    return result


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"
