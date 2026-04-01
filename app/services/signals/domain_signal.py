from urllib.parse import urlparse
from datetime import datetime, timezone
import whois

class DomainAgeSignal:
    key = "domain_age"
    weight = 12.0

    async def extract(self, company: dict, context: dict) -> dict:
        domain = urlparse(company["website"]).netloc.replace("www.", "")
        try:
            w = whois.whois(domain)
            creation = w.creation_date
            if isinstance(creation, list):
                creation = creation[0]
            if creation is None:
                return {
                    "key": self.key,
                    "passed": None,
                    "numeric_value": None,
                    "value": {"domain": domain},
                    "rationale": "WHOIS creation date unavailable."
                }

            age_days = (datetime.now(timezone.utc).date() - creation.date()).days
            if age_days < 180:
                norm = 0.2
            elif age_days < 365:
                norm = 0.5
            elif age_days < 3 * 365:
                norm = 0.8
            else:
                norm = 1.0

            return {
                "key": self.key,
                "passed": age_days >= 365,
                "numeric_value": norm,
                "value": {"domain": domain, "age_days": age_days, "created_at": str(creation)},
                "rationale": f"Domain age is {age_days} days."
            }
        except Exception as e:
            return {
                "key": self.key,
                "passed": None,
                "numeric_value": None,
                "value": {"domain": domain, "error": str(e)},
                "rationale": "WHOIS lookup failed."
            }