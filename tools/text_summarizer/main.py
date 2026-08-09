"""CLI entry point for text-summarizer.

Usage:
    uv run python -m tools.text_summarizer.main --file input.txt --sentences 3
    cat input.txt | uv run python -m tools.text_summarizer.main --sentences 3
"""

import argparse
import sys
from pathlib import Path

from tools.text_summarizer.summarizer import summarize


def _read_input(file_path: str | None) -> str:
    """Read text from `file_path`, or from stdin if no path is given."""
    if file_path:
        return Path(file_path).read_text()
    return sys.stdin.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline extractive text summarizer (frequency-based, no external APIs)."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a text file to summarize. Omit to read from stdin.",
    )
    parser.add_argument(
        "--sentences",
        type=int,
        default=3,
        help="Number of sentences to include in the summary (default: 3).",
    )
    args = parser.parse_args()

    text = _read_input(args.file)
    print(summarize(text, num_sentences=args.sentences))


if __name__ == "__main__":
    main()
