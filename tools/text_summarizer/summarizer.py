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

# Jaccard similarity (over distinct non-stopword words) above which two
# sentences are treated as redundant during selection. Deliberately
# conservative: exact-word-set overlap only catches near-verbatim
# duplicates, not paraphrases with different inflected word forms (e.g.
# Russian case endings) -- a real paraphrase can score well below this.
# Chosen high enough that no existing test's legitimately-different
# sentence pairs (max observed: 0.5) trigger it.
_REDUNDANCY_THRESHOLD = 0.6

# Sentence-ending punctuation, optionally followed by closing quote/bracket
# characters (straight and curly quotes, Russian guillemets, parens), before
# requiring whitespace. Without the optional closers, 'She said "Hello." Then
# she left.' would never split -- the period is followed by a closing quote,
# not whitespace, so the boundary would be missed entirely.
_SENTENCE_END_RE = re.compile(r"[.!?]+['\"»”’)\]]*(?=\s)")
_TRAILING_WORD_RE = re.compile(r"(\S+)$")
_WORD_RE = re.compile(r"(?:[^\W_]|')+")

# Title/reference abbreviations that are essentially never real sentence
# boundaries (always followed by more of the same sentence). Deliberately
# excludes ambiguous abbreviations like "etc." or "и т.д." that are often
# sentence-final in practice -- suppressing splits after those would trade
# one bug for another (merging two real sentences).
_SAFE_ABBREVIATIONS = frozenset(
    {
        "mr",
        "mrs",
        "ms",
        "dr",
        "prof",
        "sr",
        "jr",
        "st",
        "vs",
        "гг",
        "им",
        "ул",
        "рис",
        "стр",
        "см",
        "тыс",
        "проф",
    }
)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on '.', '!', or '?' followed by whitespace,
    allowing closing quotes/brackets ('"', '»', ')', ...) between the
    punctuation and the whitespace so quoted sentences ('She said "Hi."
    Then left.') split correctly instead of merging into one.

    Suppresses splits after single-letter initials ("А.", "J.") and a
    small list of title/reference abbreviations that are never real
    sentence boundaries ("Dr.", "рис."). Ambiguous abbreviations that are
    often sentence-final in practice (e.g. "etc.", "и т.д.") are NOT
    suppressed -- treating them as boundaries is more often correct.
    """
    text = text.strip()
    if not text:
        return []

    sentences: list[str] = []
    start = 0
    for match in _SENTENCE_END_RE.finditer(text):
        word_match = _TRAILING_WORD_RE.search(text[start : match.start()])
        word = word_match.group(1).lower() if word_match else ""
        if len(word) == 1 or word in _SAFE_ABBREVIATIONS:
            continue  # not a real sentence boundary
        sentences.append(text[start : match.end()].strip())
        start = match.end()
    sentences.append(text[start:].strip())
    return [s for s in sentences if s]


def _tokenize(sentence: str) -> list[str]:
    """Lowercase a sentence and extract word tokens, dropping punctuation."""
    return _WORD_RE.findall(sentence.lower())


def _distinct_words(sentence: str) -> set[str]:
    """Return a sentence's distinct non-stopword words (lowercased)."""
    return {w for w in _tokenize(sentence) if w not in _STOPWORDS}


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Return the Jaccard similarity of two word sets (0.0 if either is empty)."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


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
    tokenized = [_distinct_words(s) for s in sentences]
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

    Sentences are ranked by `score_sentences` (word-frequency based) and
    selected greedily highest-first, skipping any sentence too similar
    (see `_REDUNDANCY_THRESHOLD`) to one already selected, so a near-duplicate
    sentence doesn't waste a slot that could cover more of the document. If
    redundancy filtering can't fill all `num_sentences` slots (e.g. every
    remaining candidate is a near-duplicate of one already picked), the
    remaining slots are backfilled with the next highest-scoring sentences
    regardless of similarity -- the output always has `num_sentences`
    sentences whenever `text` has at least that many.

    If `text` has fewer sentences than `num_sentences`, the whole text is
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
    words = [_distinct_words(s) for s in sentences]
    ranked = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)

    selected: list[int] = []
    for i in ranked:
        if len(selected) >= num_sentences:
            break
        if any(_jaccard_similarity(words[i], words[j]) >= _REDUNDANCY_THRESHOLD for j in selected):
            continue  # too similar to an already-selected sentence
        selected.append(i)

    if len(selected) < num_sentences:  # backfill: never return fewer than requested
        for i in ranked:
            if len(selected) >= num_sentences:
                break
            if i not in selected:
                selected.append(i)

    selected.sort()  # restore original reading order
    return " ".join(sentences[i] for i in selected)
