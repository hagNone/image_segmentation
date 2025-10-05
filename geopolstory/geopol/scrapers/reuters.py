from __future__ import annotations

from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedArticle


class ReutersScraper(BaseScraper):
    source_name = "Reuters"
    base_url = "https://www.reuters.com/world/"
    rate_limit_seconds = 1.0

    def list_article_urls(self) -> Iterable[str]:
        # Respect robots.txt: Reuters allows crawling news pages with rate limits
        if not self.is_allowed(self.base_url):
            return []
        resp = self.session.get(self.base_url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Reuters uses article tags with links under h2
        urls = []
        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href:
                continue
            if href.startswith("/world/") or href.startswith("/business/"):
                full = "https://www.reuters.com" + href
                if self.is_allowed(full):
                    urls.append(full)
        # De-duplicate while preserving order
        seen = set()
        for u in urls:
            if u not in seen:
                seen.add(u)
                yield u

    def fetch_article(self, url: str) -> Optional[ScrapedArticle]:
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            title_el = soup.find("h1")
            title = title_el.get_text(strip=True) if title_el else url
            # Reuters article body paragraphs are within article tag
            paragraphs = [p.get_text(strip=True) for p in soup.select("article p")]
            text = "\n".join(paragraphs)
            # Published time often in time tag
            time_el = soup.find("time")
            published_at = self._parse_date(time_el.get("datetime") if time_el else None)
            if not text or len(text) < 400:
                # fallback to newspaper3k for cleaner extraction
                fallback = self._fallback_newspaper(url)
                if fallback:
                    return fallback
            return ScrapedArticle(
                source_name=self.source_name,
                source_url=url,
                title=title,
                text=text,
                published_at=published_at,
            )
        except Exception:
            return self._fallback_newspaper(url)
