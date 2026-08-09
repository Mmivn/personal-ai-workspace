"""Tests for tools.text_summarizer.main -- CLI argument parsing and I/O."""

import io
import sys
from pathlib import Path

import pytest

from tools.text_summarizer.main import main
from tools.text_summarizer.summarizer import split_sentences


def _set_argv(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["text-summarizer", *argv])


def test_main_summarizes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text(
        "Cats are wonderful pets. The weather today is mild. Many people love cats."
    )
    _set_argv(monkeypatch, ["--file", str(input_file), "--sentences", "1"])

    main()

    assert "cats" in capsys.readouterr().out.lower()


def test_main_reads_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("One sentence. Two sentence."))
    _set_argv(monkeypatch, ["--sentences", "3"])

    main()

    assert "One sentence." in capsys.readouterr().out


def test_main_exits_cleanly_on_missing_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_argv(monkeypatch, ["--file", "/no/such/file.txt"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "no such file" in err.lower()
    assert "Traceback" not in err


def test_main_exits_cleanly_on_invalid_sentence_count(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("Hello. World."))
    _set_argv(monkeypatch, ["--sentences", "0"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "error" in err.lower()
    assert "Traceback" not in err


def test_main_ratio_selects_correct_sentence_count(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    text = " ".join(f"Sentence number {i} is here." for i in range(10))
    monkeypatch.setattr(sys, "stdin", io.StringIO(text))
    _set_argv(monkeypatch, ["--ratio", "0.2"])

    main()

    result = capsys.readouterr().out
    assert len(split_sentences(result)) == 2  # 20% of 10 sentences


def test_main_rejects_sentences_and_ratio_together(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _set_argv(monkeypatch, ["--sentences", "2", "--ratio", "0.2"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2  # argparse's own usage-error exit code
    assert "not allowed with" in capsys.readouterr().err.lower()


def test_main_exits_cleanly_on_invalid_ratio(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("Hello. World."))
    _set_argv(monkeypatch, ["--ratio", "1.5"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "error" in err.lower()
    assert "Traceback" not in err
