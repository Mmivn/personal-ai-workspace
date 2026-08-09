# text-summarizer

Offline extractive text summarizer — no external AI APIs, no network calls,
stdlib only. Supports English and Russian (Cyrillic) text out of the box.

Splits input text into sentences and returns the `N` sentences that best
represent the document, pulled verbatim and kept in their original order —
it extracts existing sentences rather than generating new text.

## Usage

From the project root:

```
uv run python -m tools.text_summarizer.main --file input.txt --sentences 3
```

Or pipe text via stdin:

```
cat input.txt | uv run python -m tools.text_summarizer.main --sentences 3
```

`--file` input is read as UTF-8. Omit `--file` to read from stdin instead.

## How it works

A frequency-based extractive baseline (a variant of Luhn's algorithm), in five steps:

1. **Split into sentences** on `.`/`!`/`?` followed by whitespace, with a few
   guards against false splits: single-letter initials ("А.", "J."), a small
   list of title/reference abbreviations ("Dr.", "рис."), and closing
   quotes/brackets between the punctuation and the whitespace (so quoted
   sentences split correctly instead of merging with what follows).
2. **Tokenize** each sentence into lowercased words (Unicode-aware, so
   Cyrillic works the same as Latin script) and drop a built-in English +
   Russian stopword list.
3. **Score** each sentence by the frequency of its *distinct* words summed
   across the whole document, normalized by `sqrt(word count)` — so a
   sentence can't win purely by being long, and a single word repeated many
   times within one sentence can't inflate that sentence's own score.
4. **Select** the top-scoring sentences greedily, skipping any sentence too
   similar (word-overlap based) to one already picked, so two near-duplicate
   sentences don't both take a slot that could cover more of the document.
5. **Reorder** the selected sentences back to their original position in the
   text before returning them.

## Known limitations

- **No stemming/lemmatization.** Different inflected forms of a word
  (e.g. Russian "кошки"/"кошек") are treated as unrelated tokens, so
  repetition-based scoring and redundancy detection can miss real
  connections between sentences that a human reader would see immediately.
  This affects Russian more than English due to richer inflection.
- **Redundancy detection only catches near-verbatim duplicates**, for the
  same reason — it compares exact word sets, so true paraphrases with
  different word forms may not be recognized as similar.
- **A few ambiguous abbreviations are always treated as sentence
  boundaries** ("etc.", "и т.д.", "и др.") because in practice they're
  usually sentence-final; this is a deliberate tradeoff, not an oversight.
- This is a frequency-based baseline, not an LLM summary, and won't produce
  fluent, reworded prose. An LLM-backed version could later be added behind
  the same `summarize()` function signature.
