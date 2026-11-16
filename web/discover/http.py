import json
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 20


class ServiceError(Exception):
    pass


def request_json(url: str, params: dict | None = None, method: str = "GET", body=None, headers: dict | None = None):
    """Sends a request and returns the decoded JSON reply, raising ServiceError on failure."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Accept": "application/json",
        "User-Agent": "ytmp3-discover",
        **({"Content-Type": "application/json"} if data else {}),
        **(headers or {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            raw = res.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        raise ServiceError(f"{urllib.parse.urlsplit(url).netloc} returned {e.code}: {detail}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise ServiceError(f"{urllib.parse.urlsplit(url).netloc} unreachable: {e}") from e
    return json.loads(raw) if raw else None
