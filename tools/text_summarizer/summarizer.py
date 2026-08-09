"""Frequency-based extractive summarization.

Offline, stdlib-only: no external AI APIs, no network calls. Sentences are
scored by the summed frequency of their non-stopword words, and the
highest-scoring sentences are returned in their original order.
"""

import math
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
    """Score each sentence by its distinct non-stopword words' frequency.

    Each sentence's own repeated words count once toward both the corpus
    frequency table and its own score, so a word repeated many times inside
    a single sentence cannot inflate that sentence's score on its own. The
    raw frequency sum is then normalized by sqrt(word count), so a sentence
    doesn't win purely by accumulating more (even non-repeated) words —
    while still giving sentences that reference more of the document's
    vocabulary a modest edge.
    """
    tokenized = [{w for w in _tokenize(s) if w not in _STOPWORDS} for s in sentences]
    word_freq: Counter[str] = Counter()
    for words in tokenized:
        word_freq.update(words)  # each sentence contributes each word at most once

    scores: list[float] = []
    for words in tokenized:
        if not words:
            scores.append(0.0)
        else:
            scores.append(sum(word_freq[w] for w in words) / math.sqrt(len(words)))
    return scores


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
