from django.conf import settings
from django.db import models


class RawNews(models.Model):
    """Raw scraped article content before processing.

    Always include the canonical `source_url` and `source_name`. `fingerprint`
    uniquely identifies near-duplicate content by normalized title+source.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    source_name = models.CharField(max_length=128)
    source_url = models.URLField(unique=True)
    title = models.CharField(max_length=500)
    published_at = models.DateTimeField(null=True, blank=True)
    byline = models.CharField(max_length=300, blank=True)
    text = models.TextField()
    fingerprint = models.CharField(max_length=256, unique=True)
    language = models.CharField(max_length=16, default="en")
    country_hint = models.CharField(max_length=64, blank=True)
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.source_name}: {self.title[:80]}"


class Conflict(models.Model):
    """Represents an ongoing conflict/topic cluster.

    `entity_signature` is a stable string built from key entities (ORG/LOC/PER)
    derived from NER, sorted and normalized. `embedding` stores vector centroid
    for similarity-based matching. Confidence tracks clustering reliability.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    entity_signature = models.CharField(max_length=512, db_index=True)
    embedding = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(default=0.0)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name


class Episode(models.Model):
    """Narrative episode tied to a conflict for a given day.

    Includes generated narrative, references to source articles, and metadata.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    conflict = models.ForeignKey(Conflict, on_delete=models.CASCADE, related_name="episodes")
    date = models.DateField(db_index=True)
    summary = models.CharField(max_length=500)
    narrative = models.TextField()
    sources = models.ManyToManyField(RawNews, related_name="episodes")
    confidence = models.FloatField(default=0.0)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("conflict", "date")
        ordering = ["-date", "-created_at"]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.conflict.name} — {self.date.isoformat()}"

