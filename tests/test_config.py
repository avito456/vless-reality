import pytest

from xrayadm import config

from xrayadm.config import ConfigError, add_client, clients, remove_client

UID1 = "11111111-1111-4111-8111-111111111111"
UID2 = "22222222-2222-4222-8222-222222222222"


def make():
    return {"inbounds": [{"tag": "vless-reality", "settings": {"clients": [
        {"id": UID1, "flow": "xtls-rprx-vision", "email": "a"}]}}]}


def test_add_does_not_mutate_and_sets_flow():
    cfg = make()
    new, c = add_client(cfg, "b", UID2)
    assert len(clients(cfg)) == 1
    assert [x["email"] for x in clients(new)] == ["a", "b"]
    assert c["flow"] == "xtls-rprx-vision"


def test_add_duplicates_and_bad_email():
    with pytest.raises(ConfigError):
        add_client(make(), "a")
    with pytest.raises(ConfigError):
        add_client(make(), "b", UID1)
    with pytest.raises(ConfigError):
        add_client(make(), "bad email")


def test_remove():
    cfg, _ = add_client(make(), "b", UID2)
    assert [x["email"] for x in clients(remove_client(cfg, "b"))] == ["a"]
    with pytest.raises(ConfigError):
        remove_client(cfg, "zzz")


def test_cannot_remove_last():
    with pytest.raises(ConfigError):
        remove_client(make(), "a")


def test_enable_api_idempotent_and_routing_first():
    from xrayadm.config import enable_api
    cfg = make()
    cfg["routing"] = {"rules": [{"type": "field", "outboundTag": "block"}]}
    once = enable_api(cfg)
    twice = enable_api(once)
    assert once == twice
    assert once["routing"]["rules"][0]["outboundTag"] == "api"
    assert sum(i.get("tag") == "api" for i in once["inbounds"]) == 1
    assert once["policy"]["levels"]["0"]["statsUserUplink"] is True
    assert "api" not in cfg and len(cfg["inbounds"]) == 1


def test_build_initial_config():
    cfg, client = config.build_initial_config(443, "www.microsoft.com", "PRIV", "abcd1234abcd1234", "first")
    ib = config.inbound(cfg)
    assert ib["port"] == 443
    assert ib["streamSettings"]["realitySettings"]["serverNames"] == ["www.microsoft.com"]
    assert ib["streamSettings"]["realitySettings"]["privateKey"] == "PRIV"
    assert config.clients(cfg) == [client]
    assert client["email"] == "first" and client["flow"] == config.FLOW
    assert any(i["tag"] == "api" for i in cfg["inbounds"])
