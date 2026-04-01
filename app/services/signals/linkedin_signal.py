from urllib.parse import urljoin

class LinkedInSignal:
    key = "linkedin_public_footprint"
    weight = 10.0

    async def extract(self, company: dict, context: dict) -> dict:
        links = context.get("links", []) or []
        linkedin_links = []

        for l in links:
            full = urljoin(company["website"], l)
            if "linkedin.com/company/" in full.lower():
                linkedin_links.append(full)

        linkedin_links = list(set(linkedin_links))
        if not linkedin_links:
            return {
                "key": self.key,
                "passed": None,
                "numeric_value": 0.4,
                "value": {"linkedin_links": []},
                "rationale": "No LinkedIn company page found."
            }

        return {
            "key": self.key,
            "passed": True,
            "numeric_value": 1.0,
            "value": {"linkedin_links": linkedin_links},
            "rationale": f"Detected {len(linkedin_links)} LinkedIn company link(s)."
        }