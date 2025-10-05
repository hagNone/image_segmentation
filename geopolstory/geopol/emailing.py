from __future__ import annotations

from dataclasses import dataclass
from typing import List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@dataclass
class EpisodeEmail:
    conflict_name: str
    summary: str
    narrative: str
    confidence: float
    sources: List[dict]


def send_daily_digest(to_email: str, date_str: str, episodes: List[EpisodeEmail]) -> None:
    subject = f"GeopolStory — Daily Digest ({date_str})"
    html = render_to_string("email/daily_digest.html", {"date": date_str, "episodes": episodes})
    msg = EmailMultiAlternatives(subject=subject, body="", from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email])
    msg.attach_alternative(html, "text/html")
    msg.send()
