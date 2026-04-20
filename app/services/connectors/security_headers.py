import httpx


SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy"
]


async def scan_security_headers(service_url: str) -> dict:
    result = {
        "headers_present": {},
        "security_headers_score": 0.0,
        "missing_critical": [],
        "details": ""
    }

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            r = await client.get(service_url)
            h = {k.lower(): v for k, v in r.headers.items()}

            present_count = 0
            for sh in SECURITY_HEADERS:
                ok = sh in h
                result["headers_present"][sh] = ok
                if ok:
                    present_count += 1

            result["security_headers_score"] = round(present_count / len(SECURITY_HEADERS), 4)

            critical = [
                "strict-transport-security",
                "content-security-policy",
                "x-frame-options",
                "x-content-type-options",
            ]
            result["missing_critical"] = [c for c in critical if not result["headers_present"].get(c, False)]
            result["details"] = "Security headers collected."

    except Exception as e:
        result["details"] = f"headers scan failed: {e}"

    return result