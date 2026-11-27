"""Stage official releases, verify their SHA-256, and never run them."""
import hashlib
import io
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from .paths import DEFAULT_DOWNLOADS

RELEASES = (
    ('zapret', 'Flowseal/zapret-discord-youtube', 'zip'),
    ('tg', 'Flowseal/tg-ws-proxy', 'exe'),
)
MAX_DOWNLOAD = 64 * 1024 * 1024

def _get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Zapret-TG-DS-DNS', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)

def latest_release(kind):
    repo = next(repo for component, repo, _ in RELEASES if component == kind)
    return _get_json(f'https://api.github.com/repos/{repo}/releases/latest')

def save_download(dest, data):
    """Publish a complete archive, preserving any other file with the same name."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        with dest.open('rb') as existing:
            if existing.read(len(data) + 1) == data:
                return False
        raise FileExistsError(f'Existing file differs: {dest.name}')
    fd, temporary = tempfile.mkstemp(prefix='.download-', suffix='.part', dir=dest.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
        os.rename(temporary, dest)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return True

def _verified_release(kind, repository, suffix, directory, tag=None):
    if (kind, repository, suffix) not in RELEASES:
        raise ValueError('Unknown update source')
    if tag is not None and not re.fullmatch(r'[A-Za-z0-9._-]{1,64}', tag):
        raise ValueError('Invalid release tag')
    selector = f'tags/{tag}' if tag else 'latest'
    release = _get_json(f'https://api.github.com/repos/{repository}/releases/{selector}')
    version = str(release.get('tag_name', ''))
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,64}', version):
        raise ValueError('Invalid version')
    assets = release.get('assets') or []
    if kind == 'zapret':
        asset = next((x for x in assets if x.get('name', '').lower().startswith('zapret-discord-youtube-') and x.get('name', '').lower().endswith('.zip')), None)
    else:
        asset = next((x for x in assets if x.get('name') == 'TgWsProxy_windows.exe'), None)
    if not asset:
        raise ValueError('Official release file not found')
    digest = str(asset.get('digest') or '')
    if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest):
        raise ValueError('Official SHA-256 is unavailable')
    expected = digest[7:].lower()
    size = int(asset.get('size') or 0)
    if size <= 0 or size > MAX_DOWNLOAD:
        raise ValueError('Unexpected update size')
    url = str(asset.get('browser_download_url') or '')
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != 'github.com' or not parsed.path.startswith('/' + repository + '/releases/download/'):
        raise ValueError('Invalid update URL')
    dest = Path(directory) / f'{kind}-{version}-{expected[:12]}.{suffix}'
    cached = dest.exists()
    if cached:
        with dest.open('rb') as existing:
            data = existing.read(size + 1)
    else:
        req = urllib.request.Request(url, headers={'User-Agent': 'Zapret-TG-DS-DNS'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read(size + 1)
    if len(data) != size or hashlib.sha256(data).hexdigest() != expected:
        if cached:
            raise FileExistsError(f'Existing file differs: {dest.name}')
        raise ValueError('Update size or SHA-256 verification failed')
    fresh = not cached and save_download(dest, data)
    return version, dest, fresh, data

def stage_latest(kind, repository, suffix, directory=None, tag=None):
    if directory is None:
        directory = DEFAULT_DOWNLOADS / ('telegram' if kind == 'tg' else kind)
    version, dest, fresh, _ = _verified_release(kind, repository, suffix, directory, tag)
    return version, dest, fresh

def download_updates(download_folder=DEFAULT_DOWNLOADS):
    results = []
    for kind, repo, suffix in RELEASES:
        try:
            directory = Path(download_folder) / ('telegram' if kind == 'tg' else kind)
            version, path, fresh = stage_latest(kind, repo, suffix, directory)
            results.append((kind, True, version, str(path), fresh))
        except Exception as exc:
            results.append((kind, False, '', str(exc), False))
    return results

def install_component(kind, download_folder=DEFAULT_DOWNLOADS):
    """Download and register an official component without overwriting older versions."""
    from .versions import install_latest_tg, install_zapret_zip
    if kind == 'tg':
        version, fresh = install_latest_tg(Path(download_folder) / 'telegram')
        return kind, True, version, '', fresh
    if kind == 'zapret':
        version, path, fresh, data = _verified_release(
            'zapret', 'Flowseal/zapret-discord-youtube', 'zip', Path(download_folder) / 'zapret')
        # The download folder may be shared. Install the bytes we actually verified.
        version = version.lstrip('vV')
        install_zapret_zip(io.BytesIO(data), version)
        return kind, True, version, str(path), fresh
    raise ValueError('Unknown component')

def install_components(kind=None, download_folder=DEFAULT_DOWNLOADS):
    results = []
    for component in ((kind,) if kind else ('zapret', 'tg')):
        try:
            results.append(install_component(component, download_folder))
        except Exception as exc:
            results.append((component, False, '', str(exc), False))
    return results

def check_component_versions(zapret_version, tg_version, enabled=('zapret', 'tg')):
    """Return unknown on network errors, never call them up-to-date."""
    results = []
    for kind, repo, _ in RELEASES:
        current = str(zapret_version if kind == 'zapret' else tg_version)
        if kind not in enabled:
            results.append((kind, current, '', None, 'отключена в настройках'))
            continue
        try:
            latest = str(latest_release(kind).get('tag_name', '')).lstrip('vV')
            if not re.fullmatch(r'\d+(?:\.\d+){1,3}', latest):
                raise ValueError('Некорректный номер релиза')
            def parts(value):
                return tuple(int(x) for x in value.split('.'))
            if not re.fullmatch(r'\d+(?:\.\d+){1,3}', current):
                raise ValueError('Неизвестная текущая версия')
            results.append((kind, current, latest, parts(current) >= parts(latest), ''))
        except Exception as exc:
            results.append((kind, current, '', None, str(exc)))
    return results
