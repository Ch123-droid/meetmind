"""Clients LLM : Claude (API Anthropic) et client factice pour les tests."""
from __future__ import annotations

import json
import os
import re
from typing import Callable, Protocol

DEFAULT_MODEL = os.getenv("MEETMIND_MODEL", "claude-sonnet-5-5")


class LLMClient(Protocol):
    def complete(self, system: str, user: str, max_tokens: int = 4000) -> str: ...


class ClaudeClient:
    """Appelle l'API Claude. La clé est lue dans ANTHROPIC_API_KEY."""

    def __init__(self, model: str | None = None, api_key: str | None = None):
        import anthropic  # import tardif : le mode hors-ligne n'en a pas besoin

        self.model = model or DEFAULT_MODEL
        self._client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


class FakeClient:
    """Client déterministe pour les tests : `handler(system, user) -> str`."""

    def __init__(self, handler: Callable[[str, str], str]):
        self.handler = handler
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str, max_tokens: int = 4000) -> str:
        self.calls.append((system, user))
        return self.handler(system, user)


def extract_json(text: str) -> dict:
    """Extrait un objet JSON d'une réponse (tolère ```json … ``` et texte parasite)."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Aucun objet JSON dans la réponse du modèle")
    return json.loads(text[start : end + 1])


def call_json(llm: LLMClient, system: str, user: str, retries: int = 2, max_tokens: int = 4000) -> dict:
    """Appelle le LLM et relance en cas de JSON invalide (en lui donnant l'erreur)."""
    prompt, last = user, None
    for _ in range(retries + 1):
        try:
            return extract_json(llm.complete(system, prompt, max_tokens))
        except (ValueError, json.JSONDecodeError) as exc:
            last = exc
            prompt = f"{user}\n\n[Ta réponse précédente était invalide ({exc}). Réponds UNIQUEMENT par un JSON valide.]"
    raise RuntimeError(f"Sortie JSON invalide après {retries + 1} essais : {last}")
