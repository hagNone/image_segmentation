from __future__ import annotations

from datetime import date
from typing import List

from celery import shared_task
from django.utils import timezone

from .models import Episode, RawNews
from .scrapers.orchestrator import scrape_all_sources
from .emailing import EpisodeEmail, send_daily_digest
from .pipeline.conflict_detection import ConflictDetector
from .pipeline.story_generation import ArticleRef, render_prompt, openai_generate


@shared_task
def run_daily_pipeline() -> int:
    """Basic pipeline to cluster yesterday's articles and create episodes.

    For MVP: group all RawNews from last 24h into conflicts; generate one episode
    per conflict; email all subscribed users. Returns number of episodes.
    """
    now = timezone.now()
    # Step 0: Scrape fresh articles first
    try:
        scrape_all_sources(max_per_source=10)
    except Exception:
        pass
    since = now - timezone.timedelta(days=1)
    articles = list(RawNews.objects.filter(created_at__gte=since).order_by("-created_at"))
    detector = ConflictDetector()

    conflict_to_articles: dict = {}
    for art in articles:
        det = detector.detect_or_create(art)
        conflict_to_articles.setdefault(det.conflict, []).append(art)

    created = 0
    for conflict, arts in conflict_to_articles.items():
        # Build context bullets from previous episodes (simple heuristic)
        past = list(conflict.episodes.order_by("-date")[:3])
        context_bullets = [ep.summary for ep in past]
        refs: List[ArticleRef] = [
            ArticleRef(title=a.title, source_name=a.source_name, url=a.source_url, snippet=a.text[:240])
            for a in arts
        ]
        prompt = render_prompt(conflict.name, now.date().isoformat(), refs, context_bullets)
        narrative = openai_generate(prompt)
        summary = narrative.splitlines()[0][:240] if narrative else (
            arts[0].title if arts else conflict.name
        )
        ep, _ = Episode.objects.get_or_create(
            conflict=conflict,
            date=now.date(),
            defaults={
                "summary": summary,
                "narrative": narrative,
                "confidence": 0.6,
                "meta": {"num_articles": len(arts)},
            },
        )
        if not _:
            # Update existing
            ep.summary = summary
            ep.narrative = narrative
            ep.meta = {"num_articles": len(arts)}
            ep.save()
        ep.sources.set(arts)
        created += 1

    # Email all subscribed users
    from django.contrib.auth import get_user_model

    User = get_user_model()
    for user in User.objects.filter(is_subscribed=True):
        eps = Episode.objects.filter(date=now.date()).select_related("conflict").prefetch_related("sources")
        payload = [
            EpisodeEmail(
                conflict_name=e.conflict.name,
                summary=e.summary,
                narrative=e.narrative,
                confidence=e.confidence,
                sources=[{"title": s.title, "source_name": s.source_name, "url": s.source_url} for s in e.sources.all()],
            )
            for e in eps
        ]
        send_daily_digest(user.email, now.date().isoformat(), payload)

    return created
