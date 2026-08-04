from sqlalchemy.orm import Session

from app.domain.user_profile import CancerStage, CurrentTreatment, NotificationChannel, UserProfileCreate
from app.infrastructure.models import UserProfileModel
from app.services.profile_cipher import ProfileCipher
from app.services.user_profile_service import (
    clear_profile_cache,
    create_user_profile,
    get_user_profile,
    update_user_profile,
)


def build_payload(**overrides) -> UserProfileCreate:
    defaults = dict(
        age=45,
        stage=CancerStage.STAGE_III,
        biomarkers=["HER2-positive"],
        current_treatment=CurrentTreatment.TRASTUZUMAB,
        max_travel_distance_miles=100,
        notification_channels=[NotificationChannel.EMAIL],
    )
    defaults.update(overrides)
    return UserProfileCreate(**defaults)


def test_get_user_profile_uses_cache_on_second_read(db_session: Session):
    clear_profile_cache()
    cipher = ProfileCipher(ProfileCipher.generate_key())
    created = create_user_profile(db_session, cipher, build_payload())

    first = get_user_profile(db_session, cipher, created.id)
    assert first is not None

    # Remove the DB row; a warm cache should still return the profile briefly.
    model = db_session.get(UserProfileModel, created.id)
    assert model is not None
    db_session.delete(model)
    db_session.commit()

    cached = get_user_profile(db_session, cipher, created.id)
    assert cached is not None
    assert cached.id == created.id
    assert cached.age == 45


def test_update_user_profile_invalidates_cache(db_session: Session):
    clear_profile_cache()
    cipher = ProfileCipher(ProfileCipher.generate_key())
    created = create_user_profile(db_session, cipher, build_payload(age=45))

    assert get_user_profile(db_session, cipher, created.id) is not None

    updated = update_user_profile(
        db_session,
        cipher,
        created.id,
        build_payload(age=52),
    )
    assert updated is not None
    assert updated.age == 52

    reread = get_user_profile(db_session, cipher, created.id)
    assert reread is not None
    assert reread.age == 52
