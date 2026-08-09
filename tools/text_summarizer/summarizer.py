"""Frequency-based extractive summarization.

Offline, stdlib-only: no external AI APIs, no network calls. Sentences are
scored by the summed frequency of their non-stopword words, and the
highest-scoring sentences are returned in their original order.
"""

import re
from collections import Counter

_ENGLISH_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "our",
        "she",
        "that",
        "the",
        "their",
        "there",
        "these",
        "this",
        "those",
        "to",
        "was",
        "we",
        "were",
        "will",
        "with",
        "you",
        "your",
    }
)

_RUSSIAN_STOPWORDS = frozenset(
    {
        "и",
        "в",
        "во",
        "не",
        "что",
        "он",
        "на",
        "я",
        "с",
        "со",
        "как",
        "а",
        "то",
        "все",
        "она",
        "так",
        "его",
        "но",
        "да",
        "ты",
        "к",
        "у",
        "же",
        "вы",
        "за",
        "бы",
        "по",
        "только",
        "ее",
        "мне",
        "было",
        "вот",
        "от",
        "меня",
        "о",
        "из",
        "ему",
        "когда",
        "уже",
        "или",
        "ни",
        "быть",
        "был",
        "до",
        "вас",
        "себя",
        "они",
        "тут",
        "где",
        "есть",
        "надо",
        "для",
        "мы",
        "тебя",
        "их",
        "чем",
        "была",
        "без",
        "того",
        "кто",
        "этот",
        "этого",
        "этом",
        "при",
        "об",
        "если",
        "чтобы",
    }
)

_STOPWORDS = _ENGLISH_STOPWORDS | _RUSSIAN_STOPWORDS

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"(?:[^\W_]|')+")


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on '.', '!', or '?' followed by whitespace."""
    text = text.strip()
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _tokenize(sentence: str) -> list[str]:
    """Lowercase a sentence and extract word tokens, dropping punctuation."""
    return _WORD_RE.findall(sentence.lower())


def score_sentences(sentences: list[str]) -> list[float]:
    """Score each sentence by the summed frequency of its non-stopword words."""
    tokenized = [[w for w in _tokenize(s) if w not in _STOPWORDS] for s in sentences]
    word_freq: Counter[str] = Counter()
    for words in tokenized:
        word_freq.update(words)

    return [float(sum(word_freq[w] for w in words)) for words in tokenized]


def summarize(text: str, num_sentences: int = 3) -> str:
    """Return the top `num_sentences` sentences from `text`, in original order.

    Sentences are ranked by `score_sentences` (word-frequency based). If
    `text` has fewer sentences than `num_sentences`, the whole text is
    returned unchanged (sentence-split and rejoined).

    Raises:
        ValueError: if `num_sentences` is less than 1.
    """
    if num_sentences < 1:
        raise ValueError("num_sentences must be at least 1")

    sentences = split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    scores = score_sentences(sentences)
    top_indices = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
    top_indices = top_indices[:num_sentences]
    top_indices.sort()  # restore original reading order
    return " ".join(sentences[i] for i in top_indices)
