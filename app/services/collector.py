from typing import Dict, Any
from urllib.parse import urlparse
import httpx
import ssl
import socket


async def collect_runtime_data(service_url: str, api_endpoint: str | None = None) -> Dict[str, Any]:
    """Best-effort collector. Never crash the whole assessment."""
    out: Dict[str, Any] = {
        "dns_ok": None,
        "https_ok": None,
        "ssl_valid": None,
        "headers": {},
        "endpoint_status_code": None,
        "collection_errors": []
    }

    try:
        parsed = urlparse(service_url)
        host = parsed.hostname
        out["dns_ok"] = bool(host)
        out["https_ok"] = parsed.scheme == "https"

        if host:
            try:
                ctx = ssl.create_default_context()
                with socket.create_connection((host, 443), timeout=5) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host):
                        out["ssl_valid"] = True
            except Exception:
                out["ssl_valid"] = False

        target = api_endpoint or service_url
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(target)
            out["endpoint_status_code"] = r.status_code
            # keep few headers only
            for k in ["server", "strict-transport-security", "content-security-policy"]:
                if k in r.headers:
                    out["headers"][k] = r.headers.get(k)

    except Exception as e:
        out["collection_errors"].append(str(e))

    return out