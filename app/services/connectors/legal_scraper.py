# app/services/connectors/legal_scraper.py
import asyncio
import re
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


async def fetch_text(url: str, timeout: int = 10) -> Optional[str]:
    """Récupère le texte d’une page web."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False, timeout=timeout) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text(separator=' ', strip=True)
                    return text[:10000]
    except Exception:
        return None
    return None


async def find_legal_pages(base_url: str) -> Dict[str, Optional[str]]:
    """Cherche les pages légales (privacy, gdpr, terms, soc2)."""
    legal_urls = {
        "privacy": None,
        "gdpr": None,
        "terms": None,
        "soc2": None,
    }
    patterns = {
        "privacy": re.compile(r'privacy|confidentialité', re.I),
        "gdpr": re.compile(r'gdpr|general data protection regulation|rgpd', re.I),
        "terms": re.compile(r'terms|conditions|legal', re.I),
        "soc2": re.compile(r'soc\s*2|service organization control', re.I),
    }

    html = await fetch_text(base_url, timeout=10)
    if not html:
        return legal_urls

    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href'].strip()
        if not href.startswith('http'):
            href = urljoin(base_url, href)
        if '#' in href or len(href) > 200:
            continue
        text = link.get_text().lower()
        for key, pattern in patterns.items():
            if pattern.search(text) and legal_urls[key] is None:
                if urlparse(href).netloc == urlparse(base_url).netloc:
                    legal_urls[key] = href
                    break



    if not legal_urls["privacy"]:
        for path in ["/privacy", "/privacy-policy", "/trust/privacy", "/legal/privacy"]:
            test_url = base_url.rstrip('/') + path
            if await url_exists(test_url):   # fonction à écrire
                legal_urls["privacy"] = test_url
                break

    return legal_urls


async def analyze_legal_text(text: str) -> Dict:
    """Analyse le texte légal pour détecter GDPR, SOC2, droits."""
    results = {
        "gdpr_compliant": False,
        "soc2_detected": False,
        "has_privacy_policy": False,
        "rights_mentions": False,
        "confidence": 0.0,
    }
    if not text:
        return results

    text_lower = text.lower()

    # GDPR
    gdpr_keywords = [
        "gdpr", "general data protection regulation", "rgpd",
        "article 17", "right to erasure", "data protection officer",
        "data processing agreement"
    ]
    gdpr_score = sum(1 for kw in gdpr_keywords if kw in text_lower)
    results["gdpr_compliant"] = gdpr_score >= 2

    # SOC2
    soc2_keywords = ["soc 2", "soc2", "service organization control", "type 2", "security trust"]
    soc2_score = sum(1 for kw in soc2_keywords if kw in text_lower)
    results["soc2_detected"] = soc2_score >= 1

    # Droits des utilisateurs
    rights_keywords = [
        "access your data", "rectification", "erasure", "object", "data portability",
        "accéder", "rectifier", "effacement", "opposition", "portabilité"
    ]
    rights_score = sum(1 for kw in rights_keywords if kw in text_lower)
    results["rights_mentions"] = rights_score >= 2

    results["has_privacy_policy"] = True
    word_count = len(text.split())
    results["confidence"] = min(1.0, word_count / 500)

    return results


async def collect_legal_insights(service_url: str) -> Dict:
    """Point d’entrée principal."""
    legal_urls = await find_legal_pages(service_url)
    print(f"[DEBUG] legal_urls = {legal_urls}")
    insights = {
        "features": {
            "has_privacy_policy": False,
            "gdpr_compliant": False,
            "soc2_detected": False,
            "rights_mentions": False,
            "legal_confidence": 0.0,
        },
        "raw_pages": {}
    }

    privacy_url = legal_urls.get("privacy") or legal_urls.get("gdpr")
    if privacy_url:
        text = await fetch_text(privacy_url)
        if text:
            analysis = await analyze_legal_text(text)
            insights["features"]["has_privacy_policy"] = True
            insights["features"]["gdpr_compliant"] = analysis["gdpr_compliant"]
            insights["features"]["soc2_detected"] = analysis["soc2_detected"]
            insights["features"]["rights_mentions"] = analysis["rights_mentions"]
            insights["features"]["legal_confidence"] = analysis["confidence"]
            insights["raw_pages"]["privacy_policy"] = text[:2000]

            if legal_urls.get("soc2"):
                soc2_text = await fetch_text(legal_urls["soc2"])
                if soc2_text:
                    insights["raw_pages"]["soc2_page"] = soc2_text[:2000]
                    if "soc 2" in soc2_text.lower():
                        insights["features"]["soc2_detected"] = True
    else:
        insights["features"]["legal_confidence"] = 0.0

    if legal_urls.get("terms"):
        terms_text = await fetch_text(legal_urls["terms"])
        if terms_text:
            insights["raw_pages"]["terms"] = terms_text[:2000]

    print(f"[DEBUG] insights = {insights}")

    return insights