"""Tests for tools.text_summarizer.summarizer — pure functions, no I/O."""

import pytest

from tools.text_summarizer.summarizer import (
    _jaccard_similarity,  # pyright: ignore[reportPrivateUsage]
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


def test_split_sentences_keeps_title_abbreviation_together() -> None:
    text = "Dr. Smith arrived early. The meeting began."
    assert split_sentences(text) == [
        "Dr. Smith arrived early.",
        "The meeting began.",
    ]


def test_split_sentences_keeps_cyrillic_initials_together() -> None:
    text = "Роман А. С. Пушкина известен всем. Многие его читали."
    assert split_sentences(text) == [
        "Роман А. С. Пушкина известен всем.",
        "Многие его читали.",
    ]


def test_split_sentences_keeps_russian_reference_abbreviation_together() -> None:
    text = "Смотри рис. 3 в приложении. Там указаны данные."
    assert split_sentences(text) == [
        "Смотри рис. 3 в приложении.",
        "Там указаны данные.",
    ]


def test_split_sentences_handles_quoted_sentences() -> None:
    # A period immediately followed by a closing quote (not whitespace) must
    # still be recognized as a sentence boundary, or the quoted sentence
    # silently merges with the one that follows it.
    text = 'She said "Hello." Then she left the room.'
    assert split_sentences(text) == [
        'She said "Hello."',
        "Then she left the room.",
    ]


def test_split_sentences_handles_russian_guillemets() -> None:
    text = "Он сказал: «Привет.» И ушёл домой."
    assert split_sentences(text) == [
        "Он сказал: «Привет.»",
        "И ушёл домой.",
    ]


def test_split_sentences_still_splits_after_ambiguous_abbreviations() -> None:
    # "и т.д." ("etc.") is deliberately NOT suppressed -- it's usually
    # sentence-final in practice, so treating it as a boundary is correct
    # more often than not. This documents that known, intentional tradeoff.
    text = "Он купил яблоки, апельсины и т.д. Потом пошёл домой."
    assert split_sentences(text) == [
        "Он купил яблоки, апельсины и т.д.",
        "Потом пошёл домой.",
    ]


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


def test_score_sentences_ignores_intra_sentence_repetition() -> None:
    # A single word repeated many times in one sentence must not outscore a
    # sentence with several distinct real words. Without per-sentence
    # deduplication, "банан" x8 (self-inflated frequency 8, summed 8 times)
    # would score 64 and dwarf everything else.
    sentences = [
        "Банан банан банан банан банан банан банан банан.",
        "Компания разрабатывает новую систему анализа данных.",
    ]
    scores = score_sentences(sentences)
    assert scores[0] < scores[1]


def test_summarize_excludes_dominant_repeated_word_sentence() -> None:
    text = (
        "Компания разрабатывает новую систему искусственного интеллекта для "
        "анализа медицинских данных. Проект помогает врачам быстрее находить "
        "важную информацию в документах. Банан банан банан банан банан банан "
        "банан банан. Новая технология сокращает время обработки результатов "
        "исследований. Разработчики планируют протестировать систему в "
        "нескольких клиниках."
    )
    result = summarize(text, num_sentences=2)
    assert "банан" not in result.lower()


def test_score_sentences_normalizes_by_sentence_length() -> None:
    # A short sentence whose words are genuinely repeated elsewhere in the
    # document should outscore a longer sentence made entirely of words
    # unique to itself, even though the longer sentence has a higher raw
    # word-frequency sum. Without sqrt(word count) normalization, the raw
    # sum would wrongly favor the longer sentence (6 vs 8).
    sentences = [
        "Кошки очень умные.",
        "Дождь холодный сильный неприятный затяжной утомительный монотонный ветреный.",
        "Кошки очень умные и заботливые.",
    ]
    scores = score_sentences(sentences)
    assert scores[0] > scores[1]


def test_jaccard_similarity() -> None:
    assert _jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0
    assert _jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0
    assert _jaccard_similarity({"a", "b"}, {"b", "c"}) == pytest.approx(1 / 3)
    assert _jaccard_similarity(set(), {"a"}) == 0.0
    assert _jaccard_similarity({"a"}, set()) == 0.0
    assert _jaccard_similarity(set(), set()) == 0.0


def test_summarize_prefers_diverse_sentence_over_near_duplicate() -> None:
    text = (
        "Компания сообщила об увеличении прибыли в этом квартале. "
        "Компания сообщила об увеличении прибыли в четвертом квартале. "
        "Клиенты жалуются на долгую поддержку."
    )
    # The first two sentences differ by one word and both outscore the
    # third (unrelated) sentence, but they're near-duplicates (Jaccard
    # ~0.83). Without redundancy filtering, the top 2 by score alone would
    # be the two near-duplicates, wasting a slot on repeated content.
    result = summarize(text, num_sentences=2)
    assert "долгую поддержку" in result
    assert result.count("Компания сообщила") == 1


def test_summarize_backfill_still_returns_requested_count_when_all_redundant() -> None:
    text = (
        "Прибыль компании выросла в этом квартале. "
        "Прибыль нашей компании выросла в этом квартале. "
        "Прибыль компании сильно выросла в этом квартале."
    )
    # All three sentences are mutually near-duplicates. Redundancy
    # filtering alone would only ever select one of them; the backfill
    # step must still return exactly 2, not 1.
    result = summarize(text, num_sentences=2)
    assert len(split_sentences(result)) == 2
