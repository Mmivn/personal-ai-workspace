"""Tests for tools.text_summarizer.summarizer — pure functions, no I/O."""

import pytest

from tools.text_summarizer.summarizer import (
    _tokenize,  # pyright: ignore[reportPrivateUsage]
    score_sentences,
    split_sentences,
    summarize,
)


def test_split_sentences_basic() -> None:
    text = "Cats are great. Dogs are great too! Are birds great?"
    assert split_sentences(text) == [
        "Cats are great.",
        "Dogs are great too!",
        "Are birds great?",
    ]


def test_split_sentences_empty() -> None:
    assert split_sentences("") == []
    assert split_sentences("   ") == []


def test_split_sentences_single() -> None:
    assert split_sentences("Just one sentence.") == ["Just one sentence."]


def test_score_sentences_favors_repeated_words() -> None:
    sentences = ["Cats are great.", "The weather is fine.", "Cats are wonderful."]
    scores = score_sentences(sentences)
    # "cats" appears in sentences 0 and 2, so they should outscore sentence 1,
    # whose words don't repeat elsewhere.
    assert scores[0] > scores[1]
    assert scores[2] > scores[1]


def test_summarize_returns_all_when_text_is_short() -> None:
    text = "One sentence. Two sentence."
    assert summarize(text, num_sentences=3) == "One sentence. Two sentence."


def test_summarize_picks_top_n_in_original_order() -> None:
    text = (
        "Cats are wonderful pets. The weather today is mild. "
        "Many people love cats. Traffic was light this morning."
    )
    result = summarize(text, num_sentences=2)
    # The two cat-related sentences share the repeated word "cats" and should
    # outscore the others, but must come back in original reading order.
    assert result == "Cats are wonderful pets. Many people love cats."


def test_summarize_empty_text() -> None:
    assert summarize("", num_sentences=3) == ""


def test_summarize_rejects_non_positive_num_sentences() -> None:
    with pytest.raises(ValueError):
        summarize("Some text. More text.", num_sentences=0)


def test_tokenize_extracts_cyrillic_words() -> None:
    # Direct proof the tokenizer regex matches Cyrillic letters, not just ASCII.
    assert _tokenize("Привет, мир! Это тест.") == ["привет", "мир", "это", "тест"]


def test_score_sentences_favors_repeated_cyrillic_words() -> None:
    sentences = ["Кошки очень умные.", "Сегодня хорошая погода.", "Кошки очень ласковые."]
    scores = score_sentences(sentences)
    # "кошки" and "очень" repeat in sentences 0 and 2, so they should outscore
    # sentence 1, whose words don't repeat elsewhere. This fails on the old
    # ASCII-only tokenizer, which would score every sentence 0.
    assert scores[0] > scores[1]
    assert scores[2] > scores[1]


def test_summarize_picks_top_n_cyrillic_in_original_order() -> None:
    text = "Кошки любят играть. Дождь идёт весь день. Кошки любят молоко. Птицы поют рано утром."
    result = summarize(text, num_sentences=2)
    # The two cat sentences share repeated words ("кошки", "любят") and should
    # outscore the others, but must come back in original reading order.
    assert result == "Кошки любят играть. Кошки любят молоко."


def test_score_sentences_ignores_russian_stopwords() -> None:
    # "и" and "в" are common Russian stopwords with no real content; a
    # sentence built entirely from them should score 0 despite the
    # repetition, while a sentence with repeated content words scores above
    # it. This fails (scores[0] > 0) without Russian stopword filtering.
    sentences = ["И в и в и в.", "Кошки любят кошки."]
    scores = score_sentences(sentences)
    assert scores[0] == 0
    assert scores[1] > scores[0]
