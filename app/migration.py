"""Copy existing user data to the new, organised location without deleting it."""
from __future__ import annotations

import filecmp
import os
import shutil
import tempfile
from pathlib import Path


def _link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def _copy_file(source: Path, target: Path) -> None:
    if _link(source) or _link(target):
        raise OSError(f'Нельзя переносить ссылку: {source}')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_file() or not filecmp.cmp(source, target, shallow=False):
            raise FileExistsError(f'В новой папке уже есть другой файл: {target}')
        return
    fd, temp_name = tempfile.mkstemp(prefix='.migration-', dir=target.parent)
    try:
        with source.open('rb') as src, os.fdopen(fd, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        os.rename(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        return
    if _link(source) or _link(target):
        raise OSError(f'Нельзя переносить ссылку: {source}')
    if not source.is_dir():
        raise NotADirectoryError(source)
    target.mkdir(parents=True, exist_ok=True)
    for entry in source.iterdir():
        if entry.name == '__pycache__':
            continue  # Python bytecode caches are regenerated in the new location.
        if _link(entry):
            raise OSError(f'Нельзя переносить ссылку: {entry}')
        if entry.is_dir():
            _copy_tree(entry, target / entry.name)
        elif entry.is_file():
            _copy_file(entry, target / entry.name)
        else:
            raise OSError(f'Неподдерживаемый файл: {entry}')


def migrate_data(old: Path, new: Path) -> bool:
    """Copy old data once, including user lists, without overwriting or deleting it."""
    old, new = Path(old), Path(new)
    if old.resolve() == new.resolve():
        raise ValueError('Старая и новая папки совпадают')
    marker = new / 'settings' / '.migration-v1'
    if marker.is_file():
        return False
    if _link(old) or _link(new):
        raise OSError('Папка данных не должна быть ссылкой')
    if old.exists():
        if _link(old / 'versions'):
            raise OSError('Старая папка версий не должна быть ссылкой')
        for source, destination in (
            ('zapret', 'components/zapret/default'),
            ('versions/zapret', 'components/zapret/versions'),
            ('versions/tg', 'components/telegram/versions'),
            ('logs', 'logs'),
        ):
            _copy_tree(old / source, new / destination)
        updates = old / 'updates'
        if updates.exists():
            if _link(updates) or not updates.is_dir():
                raise OSError(f'Не удалось перенести папку загрузок: {updates}')
            for item in updates.iterdir():
                component = 'telegram' if item.name.lower().startswith('tg-') else 'zapret'
                if item.is_file() and not _link(item):
                    _copy_file(item, new / 'downloads' / component / item.name)
                elif item.is_dir() and not _link(item):
                    _copy_tree(item, new / 'downloads' / component / item.name)
                else:
                    raise OSError(f'Нельзя перенести файл: {item}')
        # Config is copied last: a failed copy must never silently reset settings.
        config = old / 'config.json'
        if _link(config):
            raise OSError(f'Нельзя переносить ссылку: {config}')
        if config.exists():
            _copy_file(config, new / 'settings' / 'config.json')
    for folder in ('components/zapret/versions', 'components/telegram/versions',
                   'downloads/zapret', 'downloads/telegram', 'settings', 'logs', 'cache/ui'):
        (new / folder).mkdir(parents=True, exist_ok=True)
    guide = new / 'Где найти файлы.txt'
    try:
        with guide.open('x', encoding='utf-8') as output:
            output.write('Папки приложения\n\n'
                         'components\\zapret\\default — основная версия Zapret\n'
                         'components\\zapret\\versions — другие версии Zapret\n'
                         'components\\telegram\\versions — скачанные версии Telegram-прокси\n'
                         'downloads\\zapret — скачанные архивы Zapret\n'
                         'downloads\\telegram — сохранённые ранее загрузки Telegram-прокси\n'
                         'settings — настройки приложения\n'
                         'logs — журналы работы\n'
                         'cache — вспомогательные файлы интерфейса\n')
    except FileExistsError:
        pass
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text('Данные перенесены; исходная папка сохранена.\n', encoding='utf-8')
    return old.exists()


def migrate_on_startup() -> bool:
    from .paths import APP_NAME, DATA_DIR, DATA_NAME, INSTALLED_LAYOUT, IS_WINDOWS
    if not IS_WINDOWS or os.environ.get('ZAPRETTG_DATA'):
        return False
    old = Path(os.environ.get('ProgramData') or r'C:\ProgramData') / DATA_NAME
    if INSTALLED_LAYOUT:
        previous = Path(os.environ.get('ProgramW6432') or os.environ['ProgramFiles']) / APP_NAME
        config = DATA_DIR / 'settings' / 'config.json'
        if config.is_file():
            return False
        if previous != DATA_DIR and (previous / 'settings' / 'config.json').is_file():
            for name in ('components/zapret', 'components/telegram/versions', 'downloads', 'logs'):
                _copy_tree(previous / name, DATA_DIR / name)
            _copy_file(previous / 'settings' / 'config.json', config)
            return True
    return migrate_data(old, DATA_DIR)
