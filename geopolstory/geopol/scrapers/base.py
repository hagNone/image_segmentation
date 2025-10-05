from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from newspaper import Article

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0 Safari/537.36"
)


@dataclass
class ScrapedArticle:
    source_name: str
    source_url: str
    title: str
    text: str
    published_at: Optional[str]
    byline: str = ""
    language: str = "en"

    @property
    def fingerprint(self) -> str:
        key = f"{self.source_name.lower().strip()}::{self.title.lower().strip()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:64]


class BaseScraper:
    source_name: str = "base"
    base_url: str = ""
    rate_limit_seconds: float = 1.0

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._robots: Optional[RobotFileParser] = None

    def sleep(self) -> None:
        time.sleep(self.rate_limit_seconds)

    def list_article_urls(self) -> Iterable[str]:  # pragma: no cover
        raise NotImplementedError

    def fetch_article(self, url: str) -> Optional[ScrapedArticle]:  # pragma: no cover
        raise NotImplementedError

    def _fallback_newspaper(self, url: str) -> Optional[ScrapedArticle]:
        try:
            article = Article(url)
            article.download()
            article.parse()
            published_at = None
            if article.publish_date:
                published_at = article.publish_date.isoformat()
            return ScrapedArticle(
                source_name=self.source_name,
                source_url=url,
                title=article.title or url,
                text=article.text or "",
                published_at=published_at,
                byline=", ".join(article.authors or []),
            )
        except Exception:
            return None

    @staticmethod
    def _parse_date(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        try:
            return dateparser.parse(text).isoformat()
        except Exception:
            return None

    # robots.txt handling
    def _ensure_robots(self) -> None:
        if self._robots is not None:
            return
        try:
            root = urlparse(self.base_url)
            robots_url = f"{root.scheme}://{root.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            self._robots = rp
        except Exception:
            self._robots = None

    def is_allowed(self, url: str) -> bool:
        self._ensure_robots()
        if not self._robots:
            return True
        try:
            return self._robots.can_fetch(USER_AGENT, url)
        except Exception:
            return True
