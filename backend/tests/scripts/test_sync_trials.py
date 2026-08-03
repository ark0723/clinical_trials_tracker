import pytest

from app.scripts import sync_trials
from app.services.trial_sync_service import SyncResult


class _StubSession:
    def __enter__(self):
        return "fake-db-session"

    def __exit__(self, *args):
        return False


def test_main_returns_zero_and_logs_summary_on_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sync_trials, "SessionLocal", _StubSession)
    monkeypatch.setattr(
        sync_trials,
        "sync_clinical_trials",
        lambda db, client, condition: SyncResult(created=2, updated=1, events=[]),
    )

    exit_code = sync_trials.main()

    assert exit_code == 0


def test_main_returns_one_when_sync_raises(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sync_trials, "SessionLocal", _StubSession)

    def _raise(*args, **kwargs):
        raise RuntimeError("upstream API is down")

    monkeypatch.setattr(sync_trials, "sync_clinical_trials", _raise)

    exit_code = sync_trials.main()

    assert exit_code == 1
