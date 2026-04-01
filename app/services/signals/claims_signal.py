import re

class ClaimsSignal:
    key = "product_claims_quality"
    weight = 23.0

    CLAIM_KEYWORDS = [
        "ai", "machine learning", "automation", "accuracy", "security",
        "compliance", "gdpr", "soc 2", "iso 27001", "uptime", "sla"
    ]

    async def extract(self, company: dict, context: dict) -> dict:
        text = (context.get("website_text") or "").lower()
        if not text:
            return {
                "key": self.key,
                "passed": None,
                "numeric_value": None,
                "value": {"claims": []},
                "rationale": "No website text available for claims extraction."
            }

        found = []
        for kw in self.CLAIM_KEYWORDS:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                found.append(kw)

        found = sorted(list(set(found)))
        n = len(found)

        # Normalize by expected signal richness
        if n >= 8:
            norm = 1.0
        elif n >= 5:
            norm = 0.75
        elif n >= 3:
            norm = 0.55
        elif n >= 1:
            norm = 0.35
        else:
            norm = 0.15

        return {
            "key": self.key,
            "passed": n >= 3,
            "numeric_value": norm,
            "value": {"claims": found, "count": n},
            "rationale": f"Extracted {n} credibility-related product claims/keywords."
        }