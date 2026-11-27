"""Check the public HTTPS endpoints displayed on the home page."""
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


SITES = {
    "Discord": "https://discord.com/api/v10/gateway",
    "YouTube": "https://www.youtube.com/generate_204",
    "Telegram Web": "https://web.telegram.org/",
}


def _check(url):
    request = Request(url, headers={"User-Agent": "ZapretApp"})
    try:
        with urlopen(request, timeout=5) as response:
            expected = 204 if url == SITES["YouTube"] else 200
            remote = urlsplit(response.geturl())
            return (response.status == expected and remote.scheme == "https"
                    and remote.hostname == urlsplit(url).hostname)
    except HTTPError:
        return False
    except (OSError, HTTPException):
        return None


def check_sites():
    with ThreadPoolExecutor(max_workers=len(SITES)) as pool:
        return dict(zip(SITES, pool.map(_check, SITES.values())))
