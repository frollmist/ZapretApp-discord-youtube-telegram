import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from app.versions import install_zapret_zip
from app.updates import install_components

def zapret_zip(path, malicious=False):
    with zipfile.ZipFile(path, 'w') as z:
        for name, data in {'service.bat': 'set "LOCAL_VERSION=1.10.3"', 'general.bat': 'test',
                           'bin/winws.exe': 'test', 'bin/WinDivert64.sys': 'test', 'bin/WinDivert.dll': 'test'}.items():
            z.writestr('package/' + name, data)
        if malicious:
            z.writestr('package/../../escape', 'bad')

class VersionsTest(unittest.TestCase):
    def test_zapret_archive_is_saved_in_chosen_folder(self):
        repo = 'Flowseal/zapret-discord-youtube'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / 'source.zip'
            zapret_zip(archive)
            data = archive.read_bytes()
            name = 'zapret-discord-youtube-1.10.3.zip'
            release = {'tag_name': '1.10.3', 'assets': [{
                'name': name, 'size': len(data), 'digest': 'sha256:' + hashlib.sha256(data).hexdigest(),
                'browser_download_url': f'https://github.com/{repo}/releases/download/1.10.3/{name}'}]}
            downloads = root / 'Новые загрузки'
            with patch('app.updates._get_json', return_value=release), \
                 patch('app.updates.urllib.request.urlopen', return_value=io.BytesIO(data)) as fetch, \
                 patch('app.versions.install_zapret_zip', side_effect=lambda src, v: install_zapret_zip(src, v, root / 'versions')):
                result, = install_components('zapret', downloads)
                self.assertTrue(result[1], result)
                saved = Path(result[3])
                self.assertEqual(saved.parent, downloads / 'zapret')
                self.assertEqual(saved.read_bytes(), data)
                self.assertTrue((root / 'versions' / '1.10.3' / 'general.bat').is_file())
                repeat, = install_components('zapret', downloads)
                self.assertTrue(repeat[1], repeat)
                self.assertFalse(repeat[4])
                fetch.assert_called_once()

    def test_install_and_keep_existing(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'a.zip'
            zapret_zip(archive)
            target = install_zapret_zip(archive, '1.10.3', Path(root) / 'versions')
            (target / 'user.txt').write_text('untouched')
            self.assertEqual(install_zapret_zip(archive, '1.10.3', Path(root) / 'versions'), target)
            self.assertEqual((target / 'user.txt').read_text(), 'untouched')

    def test_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as root:
            archive = Path(root) / 'a.zip'
            zapret_zip(archive, True)
            with self.assertRaises(ValueError):
                install_zapret_zip(archive, '1.10.3', Path(root) / 'versions')
            self.assertFalse((Path(root) / 'escape').exists())

    def test_tg_source_pinned_commit(self):
        sha = 'a' * 40
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            z.comment = sha.encode('ascii')
            for name, content in {'proxy/__init__.py': '__version__ = "1.99.0"',
                                  'proxy/tg_ws_proxy.py': 'x = 1', 'ui/i18n/ru.json': '{}',
                                  'utils/logging_setup.py': 'x = 1', 'LICENSE': 'MIT'}.items():
                z.writestr(f'tg-ws-proxy-{sha}/{name}', content)
        release = {'tag_name': 'v1.99.0'}
        ref = {'object': {'type': 'commit', 'sha': sha}}
        with tempfile.TemporaryDirectory() as root, patch('app.versions.TG_VERSIONS', Path(root)), patch('app.versions.tg_version_path', return_value=None), patch('app.updates._get_json', side_effect=[release, ref]), patch('app.versions.urllib.request.urlopen', return_value=io.BytesIO(buffer.getvalue())):
            downloads = Path(root) / 'Новые загрузки'
            result, = install_components('tg', downloads)
            self.assertTrue(result[1], result)
            _, _, version, _, fresh = result
            saved, = (downloads / 'telegram').glob('*.zip')
            self.assertEqual(saved.read_bytes(), buffer.getvalue())
            self.assertEqual(version, '1.99.0')
            self.assertTrue(fresh)
            self.assertTrue((Path(root) / version / 'proxy' / '__init__.py').is_file())

if __name__ == '__main__': unittest.main()
