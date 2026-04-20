import os
import base64
import httpx


VT_BASE = "https://www.virustotal.com/api/v3"


def _vt_url_id(url: str) -> str:
    # VT URL ID = urlsafe base64 without trailing '='
    return base64.urlsafe_b64encode(url.encode()).decode().strip("=")


async def reputation_lookup(service_url: str) -> dict:
    api_key = os.getenv("VIRUSTOTAL_API_KEY", "").strip()

    fallback = {
        "source": "fallback",
        "reputation_score_external": 0.5,
        "blacklist_flag": False,
        "malicious_votes": 0,
        "suspicious_votes": 0,
        "harmless_votes": 0,
        "details": "No VirusTotal API key configured."
    }
    if not api_key:
        return fallback

    headers = {"x-apikey": api_key}
    out = {
        "source": "virustotal",
        "reputation_score_external": 0.5,
        "blacklist_flag": False,
        "malicious_votes": 0,
        "suspicious_votes": 0,
        "harmless_votes": 0,
        "details": ""
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            # URL object
            uid = _vt_url_id(service_url)
            r = await client.get(f"{VT_BASE}/urls/{uid}", headers=headers)
            if r.status_code == 200:
                data = r.json().get("data", {}).get("attributes", {})
                stats = data.get("last_analysis_stats", {})
                mal = int(stats.get("malicious", 0))
                sus = int(stats.get("suspicious", 0))
                harmless = int(stats.get("harmless", 0))
                total = max(1, mal + sus + harmless + int(stats.get("undetected", 0)))

                # reputation score normalized [0..1]
                # more malicious/suspicious => lower score
                risk = (mal * 1.0 + sus * 0.6) / total
                rep = max(0.0, min(1.0, 1.0 - risk))

                out.update({
                    "reputation_score_external": round(rep, 4),
                    "blacklist_flag": mal > 0,
                    "malicious_votes": mal,
                    "suspicious_votes": sus,
                    "harmless_votes": harmless,
                    "details": "Computed from VirusTotal URL analysis."
                })
                return out

            out["details"] = f"VirusTotal URL lookup failed status={r.status_code}"
            return out

    except Exception as e:
        fallback["details"] = f"VT exception: {e}"
        return fallback