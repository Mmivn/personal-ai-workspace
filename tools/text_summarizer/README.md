# text-summarizer

Offline extractive text summarizer — no external AI APIs, no network calls,
stdlib only.

Splits input text into sentences, scores each sentence by the frequency of
its non-stopword words, and returns the top-N highest-scoring sentences in
their original order.

## Usage

From the project root:

```
uv run python -m tools.text_summarizer.main --file input.txt --sentences 3
```

Or pipe text via stdin:

```
cat input.txt | uv run python -m tools.text_summarizer.main --sentences 3
```

## How it works

A simplified version of Luhn's algorithm:
1. Split text into sentences.
2. Tokenize each sentence into words, dropping a small built-in stopword list.
3. Count word frequency across the whole text.
4. Score each sentence as the sum of its words' frequencies.
5. Take the top N sentences by score, then restore their original order.

This is a frequency-based baseline, not an LLM summary — it extracts
existing sentences rather than generating new text. An LLM-backed version
could later be added behind the same `summarize()` function signature.
