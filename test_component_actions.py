import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError

from app import connectivity
from app.config import Config
from app.zapret import ZapretManager


class ConnectivityTests(unittest.TestCase):
    def test_independent_site_results(self):
        def request(req, timeout):
            url = req.full_url
            if url == connectivity.SITES["Telegram Web"]:
                raise TimeoutError()
            if url == connectivity.SITES["Discord"]:
                raise HTTPError(url, 403, "Forbidden", {}, None)
            response = MagicMock()
            response.__enter__.return_value = response
            response.status = 204
            response.geturl.return_value = url
            return response

        with patch.object(connectivity, "urlopen", side_effect=request):
            self.assertEqual(connectivity.check_sites(), {"Discord": False, "YouTube": True, "Telegram Web": None})

    def test_captive_portal(self):
        with patch.object(connectivity, "urlopen") as opener:
            response = opener.return_value.__enter__.return_value
            response.status = 200
            response.geturl.return_value = "https://login.example/"
            self.assertFalse(connectivity._check(connectivity.SITES["Discord"]))


class SelectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for target, value in (("app.config.CONFIG_FILE", root / "config.json"),
                              ("app.config.ensure_dirs", lambda: None),
                              ("app.zapret.ZAPRET_DIR", root),
                              ("app.versions.ZAPRET_VERSIONS", root / "versions")):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.cfg = Config()
        self.manager = ZapretManager(self.cfg)
        self.manager.strategies = Mock(return_value=["general.bat", "other.bat"])
        self.manager.service_installed = Mock(return_value=False)

    def test_zapret_undo_survives_restart_and_no_op_selection(self):
        z = self.manager
        self.assertTrue(z.select_strategy("other.bat")[0])
        self.assertTrue(z.select_strategy("other.bat")[0])
        z.cfg = Config()
        self.assertTrue(z.restore_selection()[0])
        self.assertEqual(z.cfg.get("zapret", "strategy"), "general.bat")
        self.assertFalse(z.restore_selection()[0])

    def test_failed_activation_retains_previous_selection_and_undo(self):
        z = self.manager
        z.select_strategy("other.bat")
        checkpoint = self.cfg.get("zapret", "undo_selection")
        z.is_running_app = Mock(return_value=True)
        z.start = Mock(side_effect=[(False, "unavailable"), (True, "running")])
        self.assertFalse(z.restore_selection()[0])
        self.assertEqual(self.cfg.get("zapret", "undo_selection"), checkpoint)
        self.assertEqual(self.cfg.get("zapret", "strategy"), "other.bat")
        self.assertEqual(z.start.call_args.args, ("other.bat",))

    def test_restoring_a_stopped_service_keeps_it_stopped(self):
        z = self.manager
        self.cfg.set("zapret", "mode", "service")
        z.service_installed.return_value = True
        z.service_strategy = Mock(side_effect=["general", "other"])
        z.service_state = Mock(return_value="stopped")
        z.install_service = Mock(return_value=(True, ""))
        self.assertTrue(z.select_strategy("other.bat")[0])
        self.assertTrue(z.restore_selection()[0])
        z.install_service.assert_called_once_with("general.bat", start=False)

    def test_telegram_can_undo_a_pending_or_already_applied_switch(self):
        for running in ("1.11.4", "1.12.0"):
            with self.subTest(running=running), patch("app.versions.tg_versions", return_value=["1.11.4", "1.12.0"]):
                self.cfg.select_tg_version("1.12.0", "1.11.4")
                self.cfg = Config()
                self.assertEqual(self.cfg.previous_tg_selection, "1.11.4")
                self.assertEqual(self.cfg.select_tg_version(None, running, restore=True), "1.11.4")
                self.assertIsNone(Config().previous_tg_selection)

