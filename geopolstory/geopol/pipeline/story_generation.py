from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

from jinja2 import Template

from .processing import normalize_whitespace


STORY_PROMPT_TEMPLATE = """
You are a careful geopolitical analyst. Write a narrative-style update grounded
in the provided articles and historical context. Cite sources explicitly with
[Source N] markers matching the provided list. Be factual and avoid speculation.

Input:
- Conflict name: {{ conflict_name }}
- Date: {{ date }}
- Historical context (bullets):
{% for b in context_bullets %}- {{ b }}
{% endfor %}
- Articles:
{% for a in articles %}- [{{ loop.index }}] {{ a.title }} ({{ a.source_name }}) — {{ a.url }}
{% endfor %}

Write 3-6 concise paragraphs (<= 500 words), include a one-line summary first.
End with a footer listing sources and a confidence score between 0 and 1.
"""


@dataclass
class ArticleRef:
    title: str
    source_name: str
    url: str
    snippet: str


def render_prompt(conflict_name: str, date: str, articles: List[ArticleRef], context_bullets: List[str]) -> str:
    tmpl = Template(STORY_PROMPT_TEMPLATE)
    return tmpl.render(
        conflict_name=conflict_name,
        date=date,
        articles=articles,
        context_bullets=context_bullets,
    )


def openai_generate(prompt: str, model: str = "gpt-4o-mini") -> str:
    from openai import OpenAI

    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "You are a precise geopolitical writer."},
                  {"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=900,
    )
    return resp.choices[0].message.content or ""


def ollama_generate(prompt: str, model: str = "llama3.1") -> str:
    import httpx
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    payload = {"model": model, "prompt": prompt, "options": {"temperature": 0.3}}
    with httpx.Client(timeout=60) as client:
        r = client.post(f"{host}/api/generate", json=payload)
        r.raise_for_status()
        # streaming returns concatenated lines; we return full text
        return r.text
