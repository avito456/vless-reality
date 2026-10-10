from urllib.parse import quote

from . import config, ssh


def build_link(cfg: dict, client: dict, pbk: str, host: str | None = None) -> str:
    ib = config.inbound(cfg)
    rs = ib["streamSettings"]["realitySettings"]
    host = host or ssh.Target().host
    q = (f"encryption=none&security=reality&sni={rs['serverNames'][0]}&fp=chrome"
         f"&pbk={pbk}&sid={rs['shortIds'][0]}&type=tcp&flow={client.get('flow', config.FLOW)}")
    return f"vless://{client['id']}@{host}:{ib['port']}?{q}#{quote(client.get('email', 'xray'))}"


def link_params(cfg: dict, client: dict, pbk: str, host: str | None = None) -> dict:
    ib = config.inbound(cfg)
    rs = ib["streamSettings"]["realitySettings"]
    return {
        "protocol": "vless",
        "address": host or ssh.Target().host,
        "port": ib["port"],
        "uuid": client["id"],
        "flow": client.get("flow", config.FLOW),
        "encryption": "none",
        "security": "reality",
        "sni": rs["serverNames"][0],
        "fingerprint": "chrome",
        "public key": pbk,
        "short id": rs["shortIds"][0],
        "network": "tcp",
    }
