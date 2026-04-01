import ssl
import socket
from datetime import datetime
from urllib.parse import urlparse

class SSLSignal:
    key = "ssl_certificate"
    weight = 10.0

    async def extract(self, company: dict, context: dict) -> dict:
        host = urlparse(company["website"]).netloc.replace("www.", "")
        try:
            context_ssl = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=8) as sock:
                with context_ssl.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()

            not_after = cert.get("notAfter")
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            remaining_days = (expiry - datetime.utcnow()).days

            norm = 1.0 if remaining_days > 30 else (0.4 if remaining_days > 0 else 0.0)

            return {
                "key": self.key,
                "passed": remaining_days > 0,
                "numeric_value": norm,
                "value": {"host": host, "expires_in_days": remaining_days},
                "rationale": f"SSL certificate expires in {remaining_days} days."
            }
        except Exception as e:
            return {
                "key": self.key,
                "passed": False,
                "numeric_value": 0.0,
                "value": {"host": host, "error": str(e)},
                "rationale": "SSL validation failed."
            }