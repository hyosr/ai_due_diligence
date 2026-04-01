import httpx
from bs4 import BeautifulSoup

async def fetch_website_text(url: str):
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text
    except Exception:
        return "", []

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href:
            links.append(href)

    return text, links