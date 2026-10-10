"""Pure functions over the Xray config dict (no I/O)."""
import copy
import re
import uuid as uuidlib

INBOUND_TAG = "vless-reality"
FLOW = "xtls-rprx-vision"
SNI_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class ConfigError(ValueError):
    pass


def inbound(cfg: dict, tag: str = INBOUND_TAG) -> dict:
    for ib in cfg.get("inbounds", []):
        if ib.get("tag") == tag:
            return ib
    raise ConfigError(f"inbound with tag {tag!r} not found")


def clients(cfg: dict) -> list[dict]:
    return inbound(cfg)["settings"]["clients"]


def add_client(cfg: dict, email: str, uid: str | None = None) -> tuple[dict, dict]:
    """Return (new_cfg, new_client). Input cfg is not mutated."""
    if not EMAIL_RE.match(email):
        raise ConfigError("email must match [A-Za-z0-9._-]{1,64}")
    uid = uid or str(uuidlib.uuid4())
    uuidlib.UUID(uid)  # validates
    new = copy.deepcopy(cfg)
    lst = clients(new)
    if any(c.get("email") == email for c in lst):
        raise ConfigError(f"client {email!r} already exists")
    if any(c.get("id") == uid for c in lst):
        raise ConfigError("UUID already in use")
    client = {"id": uid, "flow": FLOW, "email": email}
    lst.append(client)
    return new, client


def enable_api(cfg: dict, addr_port: int = 10085) -> dict:
    """Return cfg with gRPC API, stats and per-user traffic counters enabled."""
    new = copy.deepcopy(cfg)
    new["api"] = {"tag": "api", "services": ["HandlerService", "StatsService"]}
    new["stats"] = {}
    new.setdefault("policy", {}).setdefault("levels", {}).setdefault("0", {}).update(
        {"statsUserUplink": True, "statsUserDownlink": True})
    if not any(i.get("tag") == "api" for i in new["inbounds"]):
        new["inbounds"].append({"tag": "api", "listen": "127.0.0.1", "port": addr_port,
                                "protocol": "dokodemo-door",
                                "settings": {"address": "127.0.0.1"}})
    rules = new.setdefault("routing", {}).setdefault("rules", [])
    if not any(r.get("outboundTag") == "api" for r in rules):
        rules.insert(0, {"type": "field", "inboundTag": ["api"], "outboundTag": "api"})
    return new


def build_initial_config(port: int, sni: str, private_key: str, short_id: str,
                         email: str) -> tuple[dict, dict]:
    """Fresh server config: one VLESS+Reality inbound, API enabled, one first client.

    Returns (cfg, first_client).
    """
    cfg = {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "tag": INBOUND_TAG,
            "listen": "0.0.0.0",
            "port": port,
            "protocol": "vless",
            "settings": {"clients": [], "decryption": "none"},
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "show": False,
                    "dest": f"{sni}:443",
                    "xver": 0,
                    "serverNames": [sni],
                    "privateKey": private_key,
                    "shortIds": [short_id],
                },
            },
            "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]},
        }],
        "outbounds": [{"protocol": "freedom", "tag": "direct"},
                      {"protocol": "blackhole", "tag": "block"}],
    }
    cfg, client = add_client(cfg, email)
    return enable_api(cfg), client


def remove_client(cfg: dict, email: str) -> dict:
    new = copy.deepcopy(cfg)
    lst = clients(new)
    left = [c for c in lst if c.get("email") != email]
    if len(left) == len(lst):
        raise ConfigError(f"client {email!r} not found")
    if not left:
        raise ConfigError("refusing to remove the last client")
    lst[:] = left
    return new
