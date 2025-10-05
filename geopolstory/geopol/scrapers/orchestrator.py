from __future__ import annotations

from typing import Iterable, List

from django.db import IntegrityError

from .base import ScrapedArticle
from .reuters import ReutersScraper
from .aljazeera import AlJazeeraScraper
from ..models import RawNews


def scrape_all_sources(max_per_source: int = 10) -> int:
    """Scrape both sources and persist unique RawNews rows.

    Respects robots.txt through individual scrapers. De-duplicates via
    `source_url` and `fingerprint` unique constraints.
    Returns number of new rows saved.
    """
    scrapers = [ReutersScraper(), AlJazeeraScraper()]
    new_count = 0

    for s in scrapers:
        urls = []
        for i, url in enumerate(s.list_article_urls()):
            if i >= max_per_source:
                break
            urls.append(url)
        for url in urls:
            s.sleep()
            art = s.fetch_article(url)
            if not art:
                continue
            try:
                RawNews.objects.create(
                    source_name=art.source_name,
                    source_url=art.source_url,
                    title=art.title,
                    text=art.text,
                    published_at=art.published_at,
                    byline=art.byline,
                    fingerprint=art.fingerprint,
                    language=art.language,
                )
                new_count += 1
            except IntegrityError:
                # already exists
                pass
    return new_count
