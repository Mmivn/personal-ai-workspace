"""Tests for tools.text_summarizer.main -- CLI argument parsing and I/O."""

import io
import sys
from pathlib import Path

import pytest

from tools.text_summarizer.main import main


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
