"""
Feature collector for SaaS security assessment.
Collects TLS version, HTTP security headers, authentication hints, compliance keywords,
and (optionally) external reputation from Shodan.
"""

import asyncio
import re
import ssl
import socket
from urllib.parse import urlparse

import aiohttp
import certifi
import OpenSSL
from aiohttp import ClientTimeout, ClientSession


async def get_http_headers(url: str) -> dict:
    """Fetch HTTP headers (follows redirects, uses HTTPS if possible)."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    timeout = ClientTimeout(total=10)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url, allow_redirects=True, ssl=False) as resp:
                return dict(resp.headers)
        except Exception:
            return {}


async def check_tls_version(hostname: str, port: int = 443) -> dict:
    """Get TLS version and certificate info."""
    result = {
        "tls_version": None,
        "cert_valid": False,
        "cert_issuer": None,
        "cert_san": [],
    }
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                version = ssock.version()
                result["tls_version"] = version
                # Certificate
                cert = ssock.getpeercert()
                if cert:
                    result["cert_valid"] = True
                    result["cert_issuer"] = dict(x[0] for x in cert.get("issuer", []))
                    result["cert_san"] = cert.get("subjectAltName", [])
    except Exception:
        pass
    return result


def check_hsts(headers: dict) -> bool:
    return "strict-transport-security" in headers


def check_csp(headers: dict) -> bool:
    return "content-security-policy" in headers


def check_xframe(headers: dict) -> bool:
    return "x-frame-options" in headers


def check_xcontenttype(headers:dict) -> bool:
    return "x-content-type-options" in headers


def check_referrer_policy(headers: dict) -> bool:
    return "referrer-policy" in headers


def check_permissions_policy(headers: dict) -> bool:
    return "permissions-policy" in headers


async def detect_oauth_support(url: str) -> dict:
    """Try to discover OAuth endpoints via well‑known URLs."""
    base = url.rstrip("/")
    well_known_paths = [
        "/.well-known/openid-configuration",
        "/.well-known/oauth-authorization-server",
        "/.well-known/webfinger",
    ]
    result = {"oauth_supported": False, "discovery_url": None}
    async with ClientSession() as session:
        for path in well_known_paths:
            try:
                async with session.get(base + path, ssl=False, timeout=5) as resp:
                    if resp.status == 200:
                        result["oauth_supported"] = True
                        result["discovery_url"] = base + path
                        break
            except Exception:
                continue
    return result


async def detect_auth_methods(headers: dict, text: str = "") -> dict:
    """Guess authentication methods from headers and page content."""
    auth = {
        "basic": False,
        "oauth2": False,
        "api_key": False,
        "mfa_available": False,
        "password_policy": None,
    }
    # WWW-Authenticate header
    www_auth = headers.get("www-authenticate", "").lower()
    if "basic" in www_auth:
        auth["basic"] = True
    if "bearer" in www_auth:
        auth["oauth2"] = True
    # Look for API key hints in text
    if text:
        if "api key" in text.lower() or "apikey" in text.lower():
            auth["api_key"] = True
        if "mfa" in text.lower() or "two-factor" in text.lower() or "2fa" in text.lower():
            auth["mfa_available"] = True
    return auth


async def check_compliance_from_website(text: str) -> dict:
    """Simple keyword search for compliance statements."""
    compliance = {
        "gdpr": bool(re.search(r"gdpr|general data protection regulation", text, re.I)),
        "iso27001": bool(re.search(r"iso 27001|iso27001", text, re.I)),
        "soc2": bool(re.search(r"soc 2|soc2", text, re.I)),
        "hipaa": bool(re.search(r"hipaa", text, re.I)),
    }
    return compliance


async def external_reputation_shodan(hostname: str, api_key: str = None) -> dict:
    """Use Shodan to get reputation (requires API key)."""
    if not api_key:
        return {"score": None, "vulns": []}
    try:
        import shodan
        api = shodan.Shodan(api_key)
        info = api.host(hostname)
        return {
            "score": info.get("vulns", 0) / 100.0,  # rough normalisation
            "vulns": list(info.get("vulns", {}).keys()),
        }
    except Exception:
        return {"score": None, "vulns": []}


async def collect_all_features(service_url: str, shodan_api_key: str = None) -> dict:
    """
    Main entry point: collect all features for a given service URL.
    Returns a dictionary with the enriched features.
    """
    parsed = urlparse(service_url)
    hostname = parsed.hostname
    if not hostname:
        hostname = service_url.split("/")[0]

    # 1. HTTP headers
    headers = await get_http_headers(service_url)
    # 2. TLS / certificate
    tls_info = await check_tls_version(hostname)
    # 3. Security headers
    features = {
        "has_https": service_url.startswith("https"),
        "tls_version": tls_info["tls_version"],
        "cert_valid": tls_info["cert_valid"],
        "hsts_enabled": check_hsts(headers),
        "csp_enabled": check_csp(headers),
        "xframe_enabled": check_xframe(headers),
        "xcontenttype_enabled": check_xcontenttype(headers),
        "referrer_policy_enabled": check_referrer_policy(headers),
        "permissions_policy_enabled": check_permissions_policy(headers),
        "www_authenticate": headers.get("www-authenticate", ""),
    }

    # 4. Authentication & OAuth
    oauth = await detect_oauth_support(service_url)
    features["oauth_supported"] = oauth["oauth_supported"]

    # 5. Try to fetch a small page text for keyword analysis
    try:
        async with ClientSession() as session:
            async with session.get(service_url, timeout=5, ssl=False) as resp:
                text = await resp.text()
    except Exception:
        text = ""

    auth_methods = await detect_auth_methods(headers, text)
    features["auth_basic"] = auth_methods["basic"]
    features["auth_oauth2"] = auth_methods["oauth2"]
    features["auth_api_key"] = auth_methods["api_key"]
    features["mfa_available"] = auth_methods["mfa_available"]

    compliance = await check_compliance_from_website(text)
    features["gdpr_compliant"] = compliance["gdpr"]
    features["iso27001_compliant"] = compliance["iso27001"]
    features["soc2_compliant"] = compliance["soc2"]

    # 6. External reputation (optional)
    ext_rep = await external_reputation_shodan(hostname, shodan_api_key)
    features["external_reputation_score"] = ext_rep["score"] if ext_rep["score"] is not None else 0.5
    features["known_vulnerabilities_count"] = len(ext_rep["vulns"])

    # 7. Rate limiting / API security – not easily detected; placeholder
    features["rate_limiting_detected"] = False  # could be checked via headers like `x-ratelimit-*`
    features["api_key_rotation_supported"] = False

    return features