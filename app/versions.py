"""Side-by-side component versions; existing installations are never overwritten."""
from __future__ import annotations
import hashlib
import ast
import io
import os
import re
import shutil
import stat
import tempfile
import zipfile
import sys
import urllib.request
from pathlib import Path, PurePosixPath
from .paths import DATA_DIR, RESOURCE_DIR

VERSION_RE = re.compile(r'\d+(?:\.\d+){1,3}\Z')
ZAPRET_VERSIONS = DATA_DIR / 'components' / 'zapret' / 'versions'
TG_VERSIONS = DATA_DIR / 'components' / 'telegram' / 'versions'
BUNDLED_ZIP_SHA256 = '244314ae1c24538a0d751601da8e0c925c843371eec4456eb15f14c4fd6b7058'

def valid_version(version):
    return bool(VERSION_RE.fullmatch(str(version)))

def tg_version_path(version):
    if not valid_version(version) or version == '1.11.4':
        return None
    for root in (TG_VERSIONS / version, RESOURCE_DIR / 'tgws' / version):
        if all((root / p).is_file() for p in ('proxy/__init__.py', 'proxy/tg_ws_proxy.py', 'ui/i18n/ru.json', 'utils/logging_setup.py')):
            return root
    return None

def tg_versions():
    found = {'1.11.4'}
    for base in (TG_VERSIONS, RESOURCE_DIR / 'tgws'):
        if base.is_dir():
            for path in base.iterdir():
                if path.is_dir() and valid_version(path.name) and tg_version_path(path.name):
                    found.add(path.name)
    return sorted(found, key=lambda v: tuple(map(int, v.split('.'))), reverse=True)

def configure_tg_imports(cfg):
    version = cfg.get('tg', 'engine_version', '1.11.4')
    if version == '1.11.4':
        return None
    root = tg_version_path(version)
    if root is None:
        raise ValueError(f'Версия TG WS Proxy {version} не найдена')
    sys.path.insert(0, str(root))
    return str(root)

def clear_tg_imports(root):
    if root and root in sys.path:
        sys.path.remove(root)
    for name in list(sys.modules):
        if name == 'app.tgproxy' or name in ('proxy', 'ui', 'utils') or name.startswith(('proxy.', 'ui.', 'utils.')):
            sys.modules.pop(name, None)

def install_zapret_zip(archive, version, versions_dir=ZAPRET_VERSIONS):
    if not valid_version(version):
        raise ValueError('Некорректный номер версии')
    versions_dir = Path(versions_dir)
    versions_dir.mkdir(parents=True, exist_ok=True)
    target = versions_dir / version
    if target.is_dir():
        required = ('service.bat', 'general.bat', 'bin/winws.exe', 'bin/WinDivert64.sys', 'bin/WinDivert.dll')
        if target.is_symlink() or not all((target / name).is_file() for name in required):
            raise ValueError(f'Папка версии {version} повреждена; выберите другую версию')
        service = (target / 'service.bat').read_bytes().decode('utf-8', errors='replace')
        match = re.search(r'set\s+"LOCAL_VERSION=([^"]+)"', service, re.I)
        if not match or match.group(1).strip() != version:
            raise ValueError('Версия в существующей папке не совпадает')
        return target
    if target.exists():
        raise FileExistsError(f'Версия {version} уже существует и не является папкой')
    temporary = Path(tempfile.mkdtemp(prefix='.install-', dir=str(versions_dir)))
    try:
        with zipfile.ZipFile(archive) as z:
            entries = z.infolist()
            if len(entries) > 3000 or sum(x.file_size for x in entries) > 100 * 1024 * 1024:
                raise ValueError('Архив слишком большой')
            roots = {PurePosixPath(x.filename).parts[0] for x in entries if x.filename}
            if len(roots) != 1:
                raise ValueError('Неожиданная структура архива')
            for entry in entries:
                p = PurePosixPath(entry.filename)
                if p.is_absolute() or '..' in p.parts or '\\' in entry.filename or ':' in entry.filename or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError('Недопустимый путь в архиве')
                parts = p.parts[1:]
                if not parts:
                    continue
                dst = temporary.joinpath(*parts)
                if entry.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(entry) as src, open(dst, 'xb') as out:
                        shutil.copyfileobj(src, out)
        for name in ('service.bat', 'general.bat', 'bin/winws.exe', 'bin/WinDivert64.sys', 'bin/WinDivert.dll'):
            if not (temporary / name).is_file():
                raise ValueError(f'В архиве отсутствует {name}')
        service = (temporary / 'service.bat').read_bytes().decode('utf-8', errors='replace')
        match = re.search(r'set\s+"LOCAL_VERSION=([^"]+)"', service, re.I)
        if not match or match.group(1).strip() != version:
            raise ValueError('Версия внутри архива не совпадает')
        os.rename(temporary, target)
        return target
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

def install_bundled_zapret():
    archive = RESOURCE_DIR / 'zapret-versions' / '1.10.3.zip'
    if not archive.is_file():
        return
    if hashlib.sha256(archive.read_bytes()).hexdigest() != BUNDLED_ZIP_SHA256:
        raise ValueError('Не совпадает контрольная сумма встроенного архива Zapret')
    install_zapret_zip(archive, '1.10.3')

def install_latest_tg(download_dir=None):
    """Install upstream source at the immutable release commit, never over existing versions."""
    from .updates import _get_json, save_download
    repo = 'Flowseal/tg-ws-proxy'
    release = _get_json(f'https://api.github.com/repos/{repo}/releases/latest')
    tag = str(release.get('tag_name', ''))
    version = tag.lstrip('vV')
    if not valid_version(version) or tag not in (version, 'v' + version, 'V' + version):
        raise ValueError('Недопустимая версия Telegram-прокси')
    if tg_version_path(version) or version == '1.11.4':
        return version, False
    ref = _get_json(f'https://api.github.com/repos/{repo}/git/ref/tags/{tag}')
    obj = ref.get('object') or {}
    sha, kind = obj.get('sha', ''), obj.get('type', '')
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Не удалось определить коммит версии')
    if kind == 'tag':
        obj = (_get_json(f'https://api.github.com/repos/{repo}/git/tags/{sha}').get('object') or {})
        sha, kind = obj.get('sha', ''), obj.get('type', '')
    if kind != 'commit' or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Тег не указывает на коммит')
    req = urllib.request.Request(f'https://codeload.github.com/{repo}/zip/{sha}', headers={'User-Agent': 'Zapret-TG-DS-DNS'})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read(24 * 1024 * 1024 + 1)
    if len(data) > 24 * 1024 * 1024:
        raise ValueError('Архив Telegram-прокси слишком велик')
    TG_VERSIONS.mkdir(parents=True, exist_ok=True)
    target = TG_VERSIONS / version
    if target.exists():
        raise FileExistsError('Папка версии уже существует')
    temporary = Path(tempfile.mkdtemp(prefix='.tg-install-', dir=str(TG_VERSIONS)))
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if z.comment.decode('ascii', errors='replace') != sha:
                raise ValueError('Коммит архива не совпадает с релизом')
            entries = z.infolist()
            if len(entries) > 4000 or sum(i.file_size for i in entries) > 100 * 1024 * 1024:
                raise ValueError('Архив Telegram-прокси слишком велик')
            for entry in entries:
                p = PurePosixPath(entry.filename)
                if p.is_absolute() or '..' in p.parts or '\\' in entry.filename or ':' in entry.filename or stat.S_ISLNK(entry.external_attr >> 16):
                    raise ValueError('Недопустимый путь в архиве')
                if not p.parts or p.parts[0] != f'tg-ws-proxy-{sha}':
                    raise ValueError('Неожиданная структура архива')
                parts = p.parts[1:]
                if not parts or entry.is_dir():
                    continue
                if not ((parts[0] in ('proxy', 'ui', 'utils') and p.suffix.lower() in ('.py', '.json')) or parts == ('LICENSE',)):
                    continue
                dst = temporary.joinpath(*parts)
                dst.parent.mkdir(parents=True, exist_ok=True)
                content = z.read(entry)
                if dst.suffix == '.py':
                    compile(content, str(dst), 'exec')
                with open(dst, 'xb') as out:
                    out.write(content)
        for name in ('proxy/__init__.py', 'proxy/tg_ws_proxy.py', 'ui/i18n/ru.json', 'utils/logging_setup.py'):
            if not (temporary / name).is_file():
                raise ValueError(f'Не найден файл {name}')
        tree = ast.parse((temporary / 'proxy' / '__init__.py').read_text(encoding='utf-8'))
        version_values = [n.value.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets) and isinstance(n.value, ast.Constant)]
        if version_values != [version]:
            raise ValueError('Версия в исходниках не совпадает с релизом')
        if download_dir is not None:
            save_download(Path(download_dir) / f'tg-ws-proxy-{version}-{sha[:12]}.zip', data)
        os.rename(temporary, target)
        return version, True
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
