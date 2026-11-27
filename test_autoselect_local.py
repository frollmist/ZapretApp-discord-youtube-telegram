import unittest
from unittest.mock import patch
from app.zapret import ZapretManager


class Config:
    def __init__(self):
        self.values = {"strategy": "old.bat", "engine_version": "default"}

    def get(self, section, key, default=None):
        return self.values.get(key, default)

    def set(self, section, key, value):
        self.values[key] = value


class Response:
    status = 204
    def __init__(self, url): self.url = url
    def __enter__(self): return self
    def __exit__(self, *args): pass


class Opener:
    def open(self, request, timeout): return Response(request.full_url)


class TestSelection(unittest.TestCase):
    def test_success(self):
        manager = ZapretManager(Config())
        manager.service_state = lambda: None
        manager.is_running_app = lambda: True
        manager.strategies = lambda: ["good.bat"]
        manager.start = lambda name: (manager.cfg.set("zapret", "strategy", name) or True, "")
        progress = []
        with patch("app.zapret.urllib.request.build_opener", return_value=Opener()):
            ok, _ = manager.auto_select_strategy(lambda *event: progress.append(event))
        self.assertTrue(ok)
        self.assertEqual(manager.cfg.get("zapret", "strategy"), "good.bat")
        self.assertEqual(manager.cfg.get("zapret", "undo_selection")["strategy"], "old.bat")
        self.assertEqual([entry[3] for entry in progress], ["", "YouTube", "Discord"])
        self.assertTrue(all(entry[:2] == (1, 1) for entry in progress))

    def test_failure_restores_prior_strategy(self):
        manager = ZapretManager(Config())
        manager.service_state = lambda: None
        manager.is_running_app = lambda: True
        manager.strategies = lambda: ["bad.bat"]
        manager.start = lambda name: (manager.cfg.set("zapret", "strategy", name) or True, "")
        manager.stop = lambda: (True, "")
        with patch("app.zapret.urllib.request.build_opener", side_effect=None) as build:
            build.return_value.open.side_effect = OSError("offline")
            ok, _ = manager.auto_select_strategy()
        self.assertFalse(ok)
        self.assertEqual(manager.cfg.get("zapret", "strategy"), "old.bat")
        self.assertIsNone(manager.cfg.get("zapret", "undo_selection"))


if __name__ == "__main__": unittest.main()
