import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app.updates import stage_latest, check_component_versions

class UpdateTest(unittest.TestCase):
    def release(self, digest):
        return {'tag_name': 'v1.2.3', 'assets': [{
            'name': 'TgWsProxy_windows.exe', 'digest': 'sha256:' + digest, 'size': 4,
            'browser_download_url': 'https://github.com/Flowseal/tg-ws-proxy/releases/download/v1.2.3/TgWsProxy_windows.exe'}]}

    def test_verified_download_and_reuse(self):
        digest = hashlib.sha256(b'test').hexdigest()
        with tempfile.TemporaryDirectory() as folder, patch('app.updates._get_json', return_value=self.release(digest)), patch('app.updates.urllib.request.urlopen', side_effect=lambda *a, **k: io.BytesIO(b'test')):
            _, path, fresh = stage_latest('tg', 'Flowseal/tg-ws-proxy', 'exe', folder)
            self.assertTrue(fresh)
            self.assertEqual(path.read_bytes(), b'test')
            _, _, fresh = stage_latest('tg', 'Flowseal/tg-ws-proxy', 'exe', folder)
            self.assertFalse(fresh)

    def test_bad_checksum_does_not_publish(self):
        with tempfile.TemporaryDirectory() as folder, patch('app.updates._get_json', return_value=self.release('0' * 64)), patch('app.updates.urllib.request.urlopen', side_effect=lambda *a, **k: io.BytesIO(b'test')):
            with self.assertRaises(ValueError):
                stage_latest('tg', 'Flowseal/tg-ws-proxy', 'exe', folder)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_network_error_is_unknown_not_current(self):
        with patch('app.updates._get_json', side_effect=OSError('offline')):
            results = check_component_versions('1.10.4', '1.11.4')
        self.assertTrue(all(row[3] is None for row in results))

    def test_reports_up_to_date_and_available_versions(self):
        with patch('app.updates._get_json', side_effect=[{'tag_name': '1.10.4'}, {'tag_name': 'v1.12.0'}]):
            results = check_component_versions('1.10.4', '1.11.4')
        self.assertTrue(results[0][3])
        self.assertFalse(results[1][3])
        self.assertEqual(results[1][2], '1.12.0')

if __name__ == '__main__': unittest.main()
