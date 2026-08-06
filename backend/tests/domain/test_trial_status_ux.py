from app.domain.clinical_trial import TrialStatus
from app.domain.trial_status_ux import (
    PATIENT_DEFAULT_STATUSES,
    status_label,
    status_meaning,
)


def test_patient_default_excludes_enrolling_by_invitation():
    assert TrialStatus.RECRUITING in PATIENT_DEFAULT_STATUSES
    assert TrialStatus.NOT_YET_RECRUITING in PATIENT_DEFAULT_STATUSES
    assert TrialStatus.ENROLLING_BY_INVITATION not in PATIENT_DEFAULT_STATUSES


def test_status_meaning_keeps_official_label():
    assert status_label(TrialStatus.RECRUITING) == "Recruiting"
    assert "looking for participants" in status_meaning(TrialStatus.RECRUITING).lower()
