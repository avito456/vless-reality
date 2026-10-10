import json

from xrayadm import server


def fake_run(files):
    def run(cmd, *a, **kw):
        if "echo bin" in cmd:
            return files.get("probe", "")
        if cmd.startswith("cat "):
            return files["config"]
        raise AssertionError(cmd)
    return run


def test_status_not_installed(monkeypatch):
    monkeypatch.setattr(server.ssh, "run", fake_run({"probe": ""}))
    assert server.status() is server.Status.NOT_INSTALLED


def test_status_empty_default_config(monkeypatch):
    monkeypatch.setattr(server.ssh, "run", fake_run({"probe": "bin\ncfg\n", "config": "{}"}))
    assert server.status() is server.Status.NOT_INSTALLED


def test_status_foreign_config(monkeypatch):
    cfg = json.dumps({"inbounds": [{"tag": "other"}]})
    monkeypatch.setattr(server.ssh, "run", fake_run({"probe": "bin\ncfg\n", "config": cfg}))
    assert server.status() is server.Status.NO_VLESS_INBOUND


def test_status_ok(monkeypatch):
    cfg = json.dumps({"inbounds": [{"tag": "vless-reality"}]})
    monkeypatch.setattr(server.ssh, "run", fake_run({"probe": "bin\ncfg\n", "config": cfg}))
    assert server.status() is server.Status.OK
