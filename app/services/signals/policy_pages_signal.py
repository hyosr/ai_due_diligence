from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

class PolicyPagesSignal:
    key = "policy_pages_presence"
    weight = 15.0

    async def extract(self, company: dict, context: dict) -> dict:
        base = company["website"].rstrip("/")
        targets = {
            "pricing": ["pricing", "plans"],
            "terms": ["terms", "tos", "terms-of-service"],
            "privacy": ["privacy", "privacy-policy"],
        }
        found = {k: False for k in targets}
        matched_urls = {k: None for k in targets}

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.get(base)
                soup = BeautifulSoup(r.text, "html.parser")
                hrefs = [a.get("href", "") for a in soup.find_all("a")]

            for h in hrefs:
                full = urljoin(base + "/", h).lower()
                for k, words in targets.items():
                    if any(w in full for w in words):
                        found[k] = True
                        matched_urls[k] = full

            score = sum(1 for v in found.values() if v) / 3.0
            return {
                "key": self.key,
                "passed": score >= (2 / 3),
                "numeric_value": score,
                "value": {"found": found, "urls": matched_urls},
                "rationale": f"Detected {sum(found.values())}/3 core pages (Pricing/Terms/Privacy)."
            }
        except Exception as e:
            return {
                "key": self.key,
                "passed": None,
                "numeric_value": None,
                "value": {"error": str(e)},
                "rationale": "Failed to inspect policy pages."
            }