from concurrent.futures import ThreadPoolExecutor
import sqlite3
from unittest.mock import Mock

import pytest
import requests

from tools.lead_qualifier.reservations import submit_reservation


def test_save_commits_before_notification_and_survives_reopen(tmp_path):
    database = str(tmp_path / "requests.sqlite3")
    payload = {"name": "Test Guest"}

    def notify(**fields):
        with sqlite3.connect(database) as reader:
            assert reader.execute("SELECT status FROM reservations").fetchone() == ("unknown",)
        assert fields == payload

    assert submit_reservation(database, "one", payload, notify) == "sent"
    notify_again = Mock()
    assert submit_reservation(database, "one", payload, notify_again) == "sent"
    notify_again.assert_not_called()


def test_timeout_keeps_request_and_never_automatically_retries(tmp_path):
    database = str(tmp_path / "requests.sqlite3")
    notify = Mock(side_effect=requests.Timeout("sensitive URL must not be stored"))
    for _ in range(2):
        assert submit_reservation(database, "one", {"name": "Guest"}, notify) == "unknown"
    notify.assert_called_once()
    with sqlite3.connect(database) as reader:
        row = reader.execute("SELECT payload,status FROM reservations").fetchone()
    assert "Guest" in row[0]
    assert "sensitive" not in str(row)


def test_concurrent_duplicate_is_sent_once(tmp_path):
    database = str(tmp_path / "requests.sqlite3")
    notify = Mock()
    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = list(pool.map(
            lambda _: submit_reservation(database, "one", {"name": "Guest"}, notify),
            range(4),
        ))
    assert set(statuses) <= {"sent", "unknown"}
    notify.assert_called_once()


def test_conflicting_payload_cannot_reuse_request_id(tmp_path):
    database = str(tmp_path / "requests.sqlite3")
    notify = Mock()
    submit_reservation(database, "one", {"name": "First"}, notify)
    with pytest.raises(ValueError):
        submit_reservation(database, "one", {"name": "Second"}, notify)
    notify.assert_called_once()


@pytest.mark.parametrize("database", ["", ":memory:", "relative.sqlite3"])
def test_unconfigured_storage_never_sends(database):
    notify = Mock()
    with pytest.raises(ValueError):
        submit_reservation(database, "one", {}, notify)
    notify.assert_not_called()


def test_unwritable_storage_never_sends(tmp_path):
    notify = Mock()
    with pytest.raises(sqlite3.OperationalError):
        submit_reservation(str(tmp_path / "missing" / "requests.sqlite3"), "one", {}, notify)
    notify.assert_not_called()


def test_missing_notification_configuration_is_recorded(tmp_path):
    notify = Mock(side_effect=KeyError("TELEGRAM_BOT_TOKEN"))
    database = str(tmp_path / "requests.sqlite3")
    assert submit_reservation(database, "one", {}, notify) == "needs_attention"
