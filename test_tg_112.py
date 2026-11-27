import logging
import os
import tempfile
import socket
with tempfile.TemporaryDirectory() as directory:
    os.environ['ZAPRETTG_DATA'] = directory
    from app.config import Config
    from app.versions import configure_tg_imports
    cfg = Config()
    cfg.set('tg', 'engine_version', '1.12.0')
    configure_tg_imports(cfg)
    from app.tgproxy import TGWS_VERSION, TgProxyManager
    assert TGWS_VERSION == '1.12.0', TGWS_VERSION
    manager = TgProxyManager(cfg)
    assert manager.validate(cfg.section('tg')) is None
    assert manager._apply()
    assert manager.link().startswith('tg://proxy?')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        cfg.set('tg', 'port', sock.getsockname()[1])
    try:
        ok, message = manager.start()
        assert ok, message
        assert manager.is_running()
    finally:
        manager.stop()
    logging.shutdown()
    print('TG_112_START_STOP_OK')
