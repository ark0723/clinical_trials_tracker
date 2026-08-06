from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.domain.clinical_trial import TrialChangeEvent, TrialPhase, TrialStatus
from app.domain.saved_trial import SavedTrialCreate
from app.domain.user_profile import (
    BrainMetastasisStatus,
    CancerStage,
    CurrentTreatment,
    NotificationChannel,
    UserProfileCreate,
)
from app.infrastructure.models import ClinicalTrialModel, PushSubscriptionModel
from app.services.change_notifier import notify_saved_trial_changes
from app.services.notifications import NotificationService
from app.services.profile_cipher import ProfileCipher
from app.services.saved_trial_service import save_trial
from app.services.user_profile_service import create_user_profile
from tests.services.test_notification_providers import RecordingBrowserProvider


@pytest.fixture()
def cipher() -> ProfileCipher:
    return ProfileCipher(ProfileCipher.generate_key())


def test_notify_saved_trial_changes_sends_browser_push(
    db_session: Session, cipher: ProfileCipher
):
    profile = create_user_profile(
        db_session,
        cipher,
        UserProfileCreate(
            age=45,
            stage=CancerStage.STAGE_II,
            biomarkers=["HER2-positive"],
            current_treatment=CurrentTreatment.UNKNOWN,
            brain_metastasis=BrainMetastasisStatus.UNKNOWN,
            max_travel_distance_miles=100,
            notification_channels=[NotificationChannel.BROWSER],
        ),
    )
    db_session.add(
        ClinicalTrialModel(
            nct_id="NCT01234567",
            title="Study",
            phase=TrialPhase.PHASE_2,
            status=TrialStatus.RECRUITING,
            eligibility_criteria_raw="Age >= 18",
            enrollment_count=10,
            has_results=False,
            last_updated=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    db_session.commit()
    save_trial(db_session, profile.id, SavedTrialCreate(nct_id="NCT01234567"))
    db_session.add(
        PushSubscriptionModel(
            user_id=profile.id,
            endpoint="https://push.example/abc",
            p256dh="p256dh-key",
            auth="auth-key",
            created_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    browser = RecordingBrowserProvider()
    service = NotificationService([browser])
    events = [
        TrialChangeEvent(
            nct_id="NCT01234567",
            event_type="status_changed",
            old_value="NOT_YET_RECRUITING",
            new_value="RECRUITING",
            detected_at=datetime.now(UTC),
        )
    ]

    sent = notify_saved_trial_changes(db_session, cipher, events, service)

    assert sent == 1
    assert browser.sent[0][0].data["nct_id"] == "NCT01234567"
