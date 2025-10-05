from datetime import date

import pytest

from geopol.models import Conflict, RawNews
from geopol.pipeline.conflict_detection import ConflictDetector


@pytest.mark.django_db
def test_conflict_creation_and_matching(monkeypatch):
    # Avoid heavy model by mocking embed
    det = ConflictDetector()
    monkeypatch.setattr(det, "_embed", lambda texts: __import__("numpy").array([[1.0, 0.0, 0.0]]))

    a1 = RawNews.objects.create(
        source_name="Test",
        source_url="https://example.com/1",
        title="Border clashes escalate",
        text="Skirmishes near Town A between Force X and Force Y.",
        fingerprint="fp1",
    )

    res1 = det.detect_or_create(a1)
    assert res1.created is True

    a2 = RawNews.objects.create(
        source_name="Test",
        source_url="https://example.com/2",
        title="Further fighting at Town A",
        text="Clashes continue near Town A with same forces.",
        fingerprint="fp2",
    )

    res2 = det.detect_or_create(a2)
    assert res2.created is False
    assert res2.conflict.id == res1.conflict.id
