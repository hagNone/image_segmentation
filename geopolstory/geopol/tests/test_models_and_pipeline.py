import json
from datetime import date

import pytest
from django.utils import timezone

from geopol.models import Conflict, Episode, RawNews
from geopol.pipeline.processing import Preprocessor, build_entity_signature


@pytest.mark.django_db
def test_rawnews_conflict_episode_models():
    rn = RawNews.objects.create(
        source_name="Test",
        source_url="https://example.com/a",
        title="Title",
        text="Body",
        fingerprint="abc",
    )
    assert rn.id is not None

    c = Conflict.objects.create(name="Conflict", description="d", entity_signature="sig")
    e = Episode.objects.create(conflict=c, date=date.today(), summary="s", narrative="n")
    e.sources.add(rn)
    assert e.sources.count() == 1


def test_entity_signature_stable():
    pre = Preprocessor()
    ner = pre.ner("Joe met ACME in Paris, France")
    sig1 = build_entity_signature(ner)
    sig2 = build_entity_signature(ner)
    assert sig1 == sig2
