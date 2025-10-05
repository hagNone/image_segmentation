import pytest

from geopol.emailing import send_daily_digest, EpisodeEmail


def test_render_email_works(settings, tmp_path, monkeypatch):
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    from django.core import mail

    episodes = [
        EpisodeEmail(
            conflict_name="Conflict A",
            summary="Summary",
            narrative="<p>Body</p>",
            confidence=0.7,
            sources=[{"title": "T1", "url": "https://example.com", "source_name": "X"}],
        )
    ]
    send_daily_digest("to@example.com", "2025-10-05", episodes)

    assert len(mail.outbox) == 1
    assert "GeopolStory — Daily Digest" in mail.outbox[0].subject
