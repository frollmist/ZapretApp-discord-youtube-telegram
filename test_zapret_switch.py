import logging
import os
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as root:
    os.environ['ZAPRETTG_DATA'] = root
    from app.config import Config
    from app.zapret import ZapretManager
    from app.versions import ZAPRET_VERSIONS, install_zapret_zip
    cfg = Config()
    manager = ZapretManager(cfg)
    manager.install_files()
    old_root = manager.root
    install_zapret_zip('resources/zapret-versions/1.10.3.zip', '1.10.3', ZAPRET_VERSIONS)
    manager.service_installed = lambda: False
    manager.is_running_app = lambda: False
    ok, message = manager.select_version('1.10.3')
    assert ok, message
    assert manager.local_version() == '1.10.3'
    assert cfg.get('zapret', 'engine_version') == '1.10.3'
    for strategy in manager.strategies():
        args = manager.build_args(strategy)
        assert '%' not in args, strategy
    manager.cfg = Config()
    ok, message = manager.restore_selection()
    assert ok, message
    assert manager.root == old_root
    assert manager.local_version() == '1.10.4'
    assert manager.cfg.get('zapret', 'engine_version') == 'default'
    assert manager.cfg.get('zapret', 'undo_selection') is None
    logging.shutdown()
    print('ZAPRET_SWITCH_OK')
