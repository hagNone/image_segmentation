from __future__ import annotations

from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedArticle


class AlJazeeraScraper(BaseScraper):
    source_name = "Al Jazeera"
    base_url = "https://www.aljazeera.com/news/"
    rate_limit_seconds = 1.0

    def list_article_urls(self) -> Iterable[str]:
        if not self.is_allowed(self.base_url):
            return []
        resp = self.session.get(self.base_url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []
        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href:
                continue
            if href.startswith("/news/") and href.count("/") > 3:
                full = "https://www.aljazeera.com" + href
                if self.is_allowed(full):
                    urls.append(full)
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
            paragraphs = [p.get_text(strip=True) for p in soup.select("article p")]
            text = "\n".join(paragraphs)
            time_el = soup.find("time")
            published_at = self._parse_date(time_el.get("datetime") if time_el else None)
            if not text or len(text) < 400:
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
