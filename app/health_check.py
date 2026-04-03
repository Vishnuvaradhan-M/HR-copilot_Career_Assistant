import urllib.request
import urllib.error
import json
from typing import Tuple

DEFAULT_OLLAMA_BASE = "http://localhost:11434"


def check_ollama(base_url: str = DEFAULT_OLLAMA_BASE, timeout: float = 2.0) -> Tuple[bool, str]:
    """Return (is_up, message). Uses a lightweight GET to the models endpoint.

    This function does not raise on failures; callers should handle the boolean.
    """
    # Ollama exposes /v1/models or root; try /v1/models first
    endpoints = ["/v1/models", "/v1", "/"]
    for ep in endpoints:
        url = base_url.rstrip("/") + ep
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                code = r.getcode()
                if 200 <= code < 300:
                    # attempt to parse body for helpful info
                    try:
                        body = r.read(4096)
                        info = json.loads(body.decode("utf-8", errors="ignore"))
                        return True, f"OK: {url} responded with {code}."
                    except Exception:
                        return True, f"OK: {url} responded with {code}."
        except urllib.error.HTTPError as he:
            return False, f"HTTP error contacting {url}: {he.code}"
        except Exception as e:
            # continue to try other endpoints
            last = str(e)
            continue
    return False, f"No successful response from Ollama ({base_url}). Last error: {last}"


if __name__ == "__main__":
    up, msg = check_ollama()
    print(up, msg)
