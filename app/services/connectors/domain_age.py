from urllib.parse import urlparse
from datetime import datetime, timezone
import whois


def _to_datetime(dt):
    if isinstance(dt, list) and dt:
        dt = dt[0]
    return dt if isinstance(dt, datetime) else None


def get_domain_age_signal(service_url: str) -> dict:
    out = {
        "domain_age_days": None,
        "domain_age_risk": 0.5,  # default unknown
        "domain_creation_date": None,
        "details": ""
    }
    try:
        host = urlparse(service_url).hostname
        if not host:
            out["details"] = "No hostname."
            return out

        w = whois.whois(host)
        creation = _to_datetime(w.creation_date)
        if not creation:
            out["details"] = "WHOIS creation date unavailable."
            return out

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        creation_naive = creation.replace(tzinfo=None)
        days = (now - creation_naive).days
        out["domain_age_days"] = days
        out["domain_creation_date"] = creation_naive.isoformat()

        # risk mapping
        if days < 30:
            risk = 1.0
        elif days < 90:
            risk = 0.8
        elif days < 180:
            risk = 0.6
        elif days < 365:
            risk = 0.4
        elif days < 730:
            risk = 0.2
        else:
            risk = 0.05

        out["domain_age_risk"] = round(risk, 4)
        out["details"] = "WHOIS domain age computed."
        return out

    except Exception as e:
        out["details"] = f"WHOIS failed: {e}"
        return out