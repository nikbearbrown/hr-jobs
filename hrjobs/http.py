"""One polite HTTP GET: names itself, times out, spaces requests per host, retries 429/5xx, obeys a long Retry-After."""
import json
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

UA = "job-listings-reader/0.1 (reads public job boards once a day)"

# Minimum seconds between requests to one host, across all threads.
MIN_INTERVAL = {"api.lever.co": 0.1, "boards-api.greenhouse.io": 0.05, "api.ashbyhq.com": 0.1,
                "data.usajobs.gov": 1.0, "api.adzuna.com": 1.0}
_last, _lock = {}, threading.Lock()
_blocked_until = {}   # host -> epoch seconds, set when a host answers 429 with a long Retry-After
LONG_RETRY = 300


def _throttle(host):
    gap = MIN_INTERVAL.get(host, 0.5)
    with _lock:
        now = time.monotonic()
        wait = _last.get(host, 0.0) + gap - now
        _last[host] = max(now, _last.get(host, 0.0) + gap)
    if wait > 0:
        time.sleep(wait)


def get_json(url, headers=None, timeout=60, retries=2):
    """Returns (status, data). status is the HTTP code or a short error name. data is None unless 200 and JSON."""
    host = urlparse(url).netloc
    if _blocked_until.get(host, 0) > time.time():
        return 429, None   # told to stay away; do not ask again until the Retry-After has passed
    last = "error"
    for attempt in range(retries + 1):
        try:
            _throttle(host)
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json", **(headers or {})})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                try:
                    return r.status, json.loads(r.read())
                except ValueError:
                    return r.status, None
        except urllib.error.HTTPError as e:
            last = e.code
            ra = str(e.headers.get("Retry-After", ""))
            ra = int(ra) if ra.isdigit() else 0
            if e.code == 429 and ra > LONG_RETRY:
                _blocked_until[host] = time.time() + ra
                return 429, None
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(min(ra or 5 * (attempt + 1), 60))
                continue
            return e.code, None
        except Exception as e:   # DNS failure, timeout, reset
            last = type(e).__name__
            if attempt < retries:
                time.sleep(1 + attempt)
    return last, None
