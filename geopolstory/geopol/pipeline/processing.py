from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from pydantic import BaseModel


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_title(title: str) -> str:
    return normalize_whitespace(title).lower()


class NERResult(BaseModel):
    persons: List[str] = []
    orgs: List[str] = []
    gpes: List[str] = []  # countries, cities
    locs: List[str] = []


class Preprocessor:
    """Wraps spaCy NER; fallback to regex if model isn't present.

    For local dev we avoid forcing model download at import time. The first call
    to `ensure()` lazily loads en_core_web_sm if available.
    """

    def __init__(self) -> None:
        self._nlp = None

    def ensure(self) -> None:
        if self._nlp is None:
            try:
                import spacy

                try:
                    self._nlp = spacy.load("en_core_web_sm")
                except OSError:
                    # model not installed; fall back to blank English
                    self._nlp = spacy.blank("en")
            except Exception:
                self._nlp = None

    def ner(self, text: str) -> NERResult:
        self.ensure()
        if not self._nlp or not hasattr(self._nlp, "pipe"):
            # extremely naive fallback
            return NERResult(persons=[], orgs=[], gpes=[], locs=[])
        doc = self._nlp(text)
        persons, orgs, gpes, locs = [], [], [], []
        for ent in getattr(doc, "ents", []):
            if ent.label_ == "PERSON":
                persons.append(ent.text)
            elif ent.label_ == "ORG":
                orgs.append(ent.text)
            elif ent.label_ == "GPE":
                gpes.append(ent.text)
            elif ent.label_ == "LOC":
                locs.append(ent.text)
        return NERResult(persons=persons, orgs=orgs, gpes=gpes, locs=locs)


def build_entity_signature(ner: NERResult) -> str:
    parts = []
    for bucket in (ner.gpes, ner.locs, ner.orgs, ner.persons):
        cleaned = [normalize_title(x) for x in bucket]
        cleaned = sorted(set(cleaned))
        parts.append("|".join(cleaned))
    return ";".join(parts)
