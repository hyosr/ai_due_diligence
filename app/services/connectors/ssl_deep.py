import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse


def ssl_deep_scan(service_url: str) -> dict:
    """
    Best-effort SSL scan:
    - ssl_valid
    - cert expiry days
    - issuer
    - protocol version
    """
    result = {
        "ssl_valid": None,
        "cert_expiry_days": None,
        "cert_issuer": None,
        "tls_version": None,
        "errors": []
    }

    try:
        hostname = urlparse(service_url).hostname
        if not hostname:
            result["errors"].append("No hostname parsed from URL.")
            return result

        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=6) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                result["tls_version"] = ssock.version()
                result["ssl_valid"] = True

                # issuer
                issuer = cert.get("issuer", ())
                issuer_parts = []
                for part in issuer:
                    for k, v in part:
                        issuer_parts.append(f"{k}={v}")
                result["cert_issuer"] = ", ".join(issuer_parts) if issuer_parts else None

                # expiry
                not_after = cert.get("notAfter")
                if not_after:
                    # Example format: 'Jun 15 12:00:00 2026 GMT'
                    exp_dt = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    delta = exp_dt - datetime.utcnow()
                    result["cert_expiry_days"] = int(delta.days)

    except Exception as e:
        result["ssl_valid"] = False
        result["errors"].append(str(e))

    return result