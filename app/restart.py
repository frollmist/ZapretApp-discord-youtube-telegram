"""Перезапуск с ожиданием полного завершения предыдущего экземпляра."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def launch_restart(zapret_active: bool, tg_active: bool) -> None:
    args = [f'--restart-after-pid={os.getpid()}',
            f'--restart-zapret={int(zapret_active)}', f'--restart-tg={int(tg_active)}']
    if getattr(sys, 'frozen', False):
        command = [sys.executable, *args]
    else:
        command = [sys.executable, str(Path(__file__).resolve().parent.parent / 'run.py'), *args]
    env = os.environ.copy()
    # One-file PyInstaller must extract a fresh copy before the old one is removed.
    env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    flags = 0
    if sys.platform == 'win32':
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    subprocess.Popen(command, env=env, close_fds=True, creationflags=flags)


def wait_for_previous(args: list[str]) -> bool:
    value = next((arg.partition('=')[2] for arg in args if arg.startswith('--restart-after-pid=')), '')
    if not value:
        return True
    if not value.isdecimal() or int(value) <= 0 or int(value) == os.getpid():
        return False
    import psutil
    try:
        psutil.Process(int(value)).wait(timeout=90)
    except psutil.NoSuchProcess:
        pass
    except (psutil.TimeoutExpired, psutil.AccessDenied):
        return False
    return True


def restart_component_state(args: list[str], component: str, default: bool) -> bool:
    # Only accept one-shot state flags on a genuine restart invocation.
    if not any(arg.startswith('--restart-after-pid=') for arg in args):
        return default
    value = next((arg.partition('=')[2] for arg in args if arg.startswith(f'--restart-{component}=')), '')
    return value == '1' if value in ('0', '1') else default
