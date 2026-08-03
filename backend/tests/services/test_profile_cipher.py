from app.domain.user_profile import (
    CancerStage,
    NotificationChannel,
    UserProfileCreate,
)
from app.services.profile_cipher import ProfileCipher


def build_profile() -> UserProfileCreate:
    return UserProfileCreate(
        age=45,
        stage=CancerStage.STAGE_III,
        biomarkers=["HER2-positive"],
        current_treatment="trastuzumab deruxtecan",
        max_travel_distance_km=100,
        notification_channels=[NotificationChannel.EMAIL],
    )


def test_encrypts_and_decrypts_profile_without_plaintext_leakage():
    cipher = ProfileCipher(ProfileCipher.generate_key())
    profile = build_profile()

    encrypted = cipher.encrypt(profile)

    assert "HER2-positive" not in encrypted
    assert "trastuzumab" not in encrypted
    assert cipher.decrypt(encrypted) == profile


def test_same_profile_uses_randomized_ciphertext():
    cipher = ProfileCipher(ProfileCipher.generate_key())
    profile = build_profile()

    assert cipher.encrypt(profile) != cipher.encrypt(profile)
