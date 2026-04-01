import re

class RedFlagsSignal:
    key = "red_flags"
    weight = 20.0

    PATTERNS = [
        r"guaranteed\s+returns",
        r"100%\s+accurate",
        r"risk[- ]?free",
        r"instant\s+rich",
        r"military[- ]?grade\s+ai",
        r"no\s+questions\s+asked\s+refund"
    ]

    async def extract(self, company: dict, context: dict) -> dict:
        text = (context.get("website_text") or "").lower()
        hits = []

        for p in self.PATTERNS:
            if re.search(p, text):
                hits.append(p)

        if len(hits) == 0:
            norm = 1.0
        elif len(hits) <= 2:
            norm = 0.5
        else:
            norm = 0.1

        return {
            "key": self.key,
            "passed": len(hits) == 0,
            "numeric_value": norm,
            "value": {"matches": hits, "count": len(hits)},
            "rationale": f"Found {len(hits)} red-flag pattern(s)."
        }