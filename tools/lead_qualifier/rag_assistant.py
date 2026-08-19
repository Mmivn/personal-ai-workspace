"""Grounded answer generation for the Family Secret knowledge assistant."""

from collections.abc import Sequence
from dataclasses import dataclass

import requests

from tools.lead_qualifier.vector_store import VectorSearchResult

DEFAULT_GENERATION_MODEL = "gemini-3.5-flash"


@dataclass(frozen=True)
class AssistantAnswer:
    text: str
    sources: tuple[VectorSearchResult, ...]


class GeminiGenerationClient:
    """Generate concise answers from retrieved context using Gemini's free tier."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_GENERATION_MODEL,
        timeout: float = 45.0,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session = session or requests.Session()

    def generate(self, question: str, context: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self.model}:generateContent"
        )
        prompt = f"""You are the official Family Secret restaurant assistant.
Answer in the same language as the guest.
Write naturally and use correct grammar in that language.
Use only the supplied context. Do not invent prices, policies, availability, or menu items.
If the context does not contain the answer, clearly say that the information is unavailable
and suggest contacting the restaurant. Keep the answer friendly and concise.

CONTEXT:
{context}

GUEST QUESTION:
{question}
"""
        response = self.session.post(
            url,
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        parts = payload["candidates"][0]["content"]["parts"]
        return "".join(str(part.get("text", "")) for part in parts).strip()


def answer_from_results(
    question: str,
    results: Sequence[VectorSearchResult],
    generation_client: GeminiGenerationClient,
    minimum_score: float = 0.55,
) -> AssistantAnswer:
    """Filter weak matches and ask Gemini to answer only from retrieved chunks."""
    relevant = tuple(result for result in results if result.score >= minimum_score)
    if not relevant:
        return AssistantAnswer(
            text=(
                "В базе знаний пока нет надёжного ответа на этот вопрос. "
                "Пожалуйста, свяжитесь с рестораном напрямую."
            ),
            sources=(),
        )

    context = "\n\n".join(
        f"SOURCE: {result.source_file}\nSECTION: {result.heading}\n{result.content}"
        for result in relevant
    )
    return AssistantAnswer(
        text=generation_client.generate(question, context),
        sources=relevant,
    )
