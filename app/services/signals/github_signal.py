import re
from urllib.parse import urljoin

class GitHubSignal:
    key = "github_public_footprint"
    weight = 10.0

    async def extract(self, company: dict, context: dict) -> dict:
        links = context.get("links", []) or []
        github_links = []

        for l in links:
            full = urljoin(company["website"], l)
            if "github.com/" in full:
                github_links.append(full)

        github_links = list(set(github_links))
        if not github_links:
            return {
                "key": self.key,
                "passed": None,
                "numeric_value": 0.4,
                "value": {"github_links": []},
                "rationale": "No GitHub organization/repository link detected on website."
            }

        org_like = any(re.search(r"github\.com/[^/]+/?$", g) for g in github_links)
        norm = 1.0 if org_like else 0.7

        return {
            "key": self.key,
            "passed": True,
            "numeric_value": norm,
            "value": {"github_links": github_links},
            "rationale": f"Detected {len(github_links)} GitHub link(s)."
        }