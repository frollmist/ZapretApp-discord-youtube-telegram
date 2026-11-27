import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.migration import migrate_data, migrate_on_startup
from app.versions import install_zapret_zip


class MigrationTests(unittest.TestCase):
    def test_full_install_uses_its_own_disk_and_imports_previous_settings_once(self):
        from app import paths
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            previous = base / 'Program Files' / paths.APP_NAME
            selected = base / 'selected disk' / paths.APP_NAME
            (previous / 'settings').mkdir(parents=True)
            (previous / 'settings' / 'config.json').write_text('{"app":{"language":"en"}}')
            lists = previous / 'components' / 'zapret' / 'default' / 'lists'
            lists.mkdir(parents=True)
            (lists / 'list-general-user.txt').write_text('user.example')
            with patch.dict(os.environ, {'ProgramW6432': str(previous.parent)}), \
                 patch.object(paths, 'INSTALLED_LAYOUT', True), patch.object(paths, 'DATA_DIR', selected), \
                 patch.object(sys, 'executable', str(selected / 'app.exe')):
                os.environ.pop('ZAPRETTG_DATA', None)
                self.assertEqual(paths._data_root(), selected)
                self.assertTrue(migrate_on_startup())
                self.assertEqual((selected / lists.relative_to(previous) / 'list-general-user.txt').read_text(), 'user.example')
                settings = selected / 'settings' / 'config.json'
                settings.write_text('{"app":{"language":"ru"}}')
                self.assertFalse(migrate_on_startup())
                self.assertIn('"ru"', settings.read_text())

    def test_startup_uses_program_files_and_imports_programdata(self):
        from app import paths
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            old = root / 'ProgramData' / 'ZapretTG'
            old.mkdir(parents=True)
            (old / 'config.json').write_text('{"copied":true}')
            program_files = root / 'Program Files'
            with patch.object(paths, 'IS_WINDOWS', True), \
                 patch.dict(os.environ, {'ProgramData': str(old.parent), 'ProgramFiles': str(program_files)}, clear=False):
                os.environ.pop('ZAPRETTG_DATA', None)
                os.environ.pop('ProgramW6432', None)
                target = paths._data_root()
                self.assertEqual(target, program_files / paths.APP_NAME)
                with patch.object(paths, 'DATA_DIR', target):
                    self.assertTrue(migrate_on_startup())
                self.assertEqual((target / 'settings' / 'config.json').read_text(), '{"copied":true}')

    def test_organises_existing_data_and_preserves_originals(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            old = Path(directory) / 'ProgramData' / 'ZapretTG'
            new = Path(directory) / 'Program Files' / 'ZapretApp-discord-youtube-telegram'
            old.mkdir(parents=True)
            shutil.copytree('resources/zapret', old / 'zapret')
            (old / 'zapret' / 'lists' / 'list-general-user.txt').write_text('my-custom-domain.example\n', encoding='utf-8')
            (old / 'config.json').write_text(json.dumps({'tg': {'engine_version': '1.12.0'}, 'zapret': {'engine_version': '1.10.3', 'strategy': 'general.bat'}}), encoding='utf-8')
            (old / 'updates').mkdir()
            (old / 'updates' / 'zapret-v1.zip').write_bytes(b'archive')
            (old / 'updates' / 'tg-v1.exe').write_bytes(b'proxy')
            (old / 'versions' / 'zapret' / '1.2.3').mkdir(parents=True)
            (old / 'versions' / 'zapret' / '1.2.3' / 'keep.txt').write_text('version', encoding='utf-8')
            install_zapret_zip('resources/zapret-versions/1.10.3.zip', '1.10.3', old / 'versions' / 'zapret')
            shutil.copytree('resources/tgws/1.12.0', old / 'versions' / 'tg' / '1.12.0')
            (old / 'logs').mkdir()
            (old / 'logs' / 'app.log').write_text('old log', encoding='utf-8')
            self.assertTrue(migrate_data(old, new))
            self.assertEqual((new / 'downloads' / 'zapret' / 'zapret-v1.zip').read_bytes(), b'archive')
            self.assertEqual((new / 'downloads' / 'telegram' / 'tg-v1.exe').read_bytes(), b'proxy')
            self.assertEqual((new / 'components' / 'zapret' / 'versions' / '1.2.3' / 'keep.txt').read_text(), 'version')
            self.assertEqual((new / 'logs' / 'app.log').read_text(), 'old log')
            self.assertEqual((new / 'components' / 'zapret' / 'default' / 'lists' / 'list-general-user.txt').read_text(), 'my-custom-domain.example\n')
            self.assertTrue((old / 'config.json').is_file())
            # A second launch must not overwrite settings saved in the new location.
            config = new / 'settings' / 'config.json'
            config.write_text(config.read_text(encoding='utf-8').replace('general.bat', 'general (ALT).bat'), encoding='utf-8')
            self.assertFalse(migrate_data(old, new))
            self.assertIn('general (ALT).bat', config.read_text(encoding='utf-8'))
            env = os.environ.copy()
            env['ZAPRETTG_DATA'] = str(new)
            script = r'''
import json, subprocess, sys
from app.config import Config
from app.versions import configure_tg_imports
c = Config()
assert c.get('tg','engine_version') == '1.12.0'
configure_tg_imports(c)
from app.tgproxy import TGWS_VERSION
assert TGWS_VERSION == '1.12.0'
from app.zapret import ZapretManager
z = ZapretManager(c)
z.prepare_versions()
assert c.get('zapret', 'engine_version') == '1.10.3'
assert z.local_version() == '1.10.3'
args = z.build_args('general.bat')
assert 'Program Files' in args
if sys.platform == 'win32':
    prefix = subprocess.list2cmdline([sys.executable, '-c', 'import json,sys;print(json.dumps(sys.argv[1:]))'])
    actual = json.loads(subprocess.check_output(prefix + ' ' + args, text=True))
    assert any(a.startswith('--hostlist=') and 'Program Files' in a and a.endswith('list-general.txt') for a in actual), actual
print('MIGRATED_COMPONENTS_OK')
'''
            result = subprocess.run([sys.executable, '-c', script], env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('MIGRATED_COMPONENTS_OK', result.stdout)

    def test_copy_failure_can_be_retried_and_never_resets_config(self):
        with tempfile.TemporaryDirectory() as directory:
            old, new = Path(directory) / 'old', Path(directory) / 'new'
            (old / 'zapret').mkdir(parents=True)
            (old / 'zapret' / 'important.txt').write_text('content')
            (old / 'config.json').write_text('{"keep":true}')
            from app import migration
            original = migration._copy_file
            def fail_on_config(source, target):
                if source.name == 'config.json':
                    raise OSError('simulated interruption')
                return original(source, target)
            with patch('app.migration._copy_file', side_effect=fail_on_config):
                with self.assertRaises(OSError):
                    migrate_data(old, new)
            self.assertFalse((new / 'settings' / '.migration-v1').exists())
            self.assertTrue(migrate_data(old, new))
            self.assertEqual((new / 'settings' / 'config.json').read_text(), '{"keep":true}')

    def test_different_existing_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            old, new = Path(directory) / 'old', Path(directory) / 'new'
            old.mkdir()
            (old / 'config.json').write_text('old')
            (new / 'settings').mkdir(parents=True)
            (new / 'settings' / 'config.json').write_text('new')
            with self.assertRaises(FileExistsError):
                migrate_data(old, new)
            self.assertEqual((new / 'settings' / 'config.json').read_text(), 'new')
            self.assertEqual((old / 'config.json').read_text(), 'old')


if __name__ == '__main__':
    unittest.main()
