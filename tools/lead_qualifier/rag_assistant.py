"""Grounded answer generation for the Family Secret knowledge assistant."""

from collections.abc import Sequence
from dataclasses import dataclass

import requests

from tools.lead_qualifier.vector_store import VectorSearchResult

DEFAULT_GENERATION_MODEL = "gemini-3.5-flash"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"


@dataclass(frozen=True)
class AssistantAnswer:
    text: str
    sources: tuple[VectorSearchResult, ...]


def direct_answer_for_common_question(question: str) -> str | None:
    """Return deterministic answers for the restaurant's most common questions."""
    text = question.casefold()
    is_russian = any("а" <= character <= "я" or character == "ё" for character in text)

    answer_rules = (
        (
            ("open", "close", "hours", "work", "откры", "закры", "час", "работ"),
            (
                "Мы открыты каждый день с 9 утра до 11 вечера. "
                "Будем рады видеть вас в Family Secret!"
            )
            if is_russian
            else (
                "We are open every day from 9:00 AM to 11:00 PM. "
                "We look forward to welcoming you to Family Secret!"
            ),
        ),
        (
            ("potato", "mash", "карто", "пюре"),
            "Да, у нас есть картофельное пюре в качестве гарнира."
            if is_russian
            else "Yes, we have mashed potatoes available as a side dish.",
        ),
        (
            ("phone", "contact", "call", "телефон", "связ", "позвон"),
            "Связаться с нами можно по телефону 0354 057 942."
            if is_russian
            else "You can contact us by phone at 0354 057 942.",
        ),
        (
            ("child", "children", "kid", "дет", "ребен", "ребён"),
            "Да, рядом с основным залом есть детская игровая зона."
            if is_russian
            else "Yes, we have a children's play area near the main dining room.",
        ),
    )

    for keywords, answer in answer_rules:
        if any(keyword in text for keyword in keywords):
            return answer
    return None


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
Start with a direct answer. For a yes-or-no question, begin with "Yes" or "No"
when the supplied context supports it. Never mention "the supplied context" to the guest.
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
                # Newer Gemini models may spend part of this allowance on
                # internal reasoning. A small limit can therefore cut off even
                # a concise guest-facing sentence before it is complete.
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024,
                    # Restaurant answers need speed and reliability, not a long
                    # hidden reasoning phase that can consume the output budget.
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        parts = payload["candidates"][0]["content"]["parts"]
        return "".join(str(part.get("text", "")) for part in parts).strip()


class GroqGenerationClient:
    """Generate a grounded answer through Groq when Gemini is unavailable."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_GROQ_MODEL,
        timeout: float = 45.0,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GROQ_API_KEY is required")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.session = session or requests.Session()

    def generate(self, question: str, context: str) -> str:
        system_prompt = (
            "You are the official Family Secret restaurant concierge. "
            "Answer in the guest's language, naturally, warmly, and concisely. "
            "Use only the provided restaurant information and never invent dishes, "
            "prices, availability, or policies. If the answer is unavailable, say so "
            "and suggest contacting the restaurant."
        )
        response = self.session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "temperature": 0.2,
                "max_tokens": 1024,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"RESTAURANT INFORMATION:\n{context}\n\nQUESTION:\n{question}",
                    },
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload["choices"][0]["message"]["content"]).strip()


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
