"""Application-layer encryption for sensitive patient profile fields."""

from cryptography.fernet import Fernet

from app.domain.user_profile import UserProfileCreate


class ProfileCipher:
    """Encrypts the complete health payload before it reaches the database."""

    def __init__(self, key: str):
        self._fernet = Fernet(key.encode("ascii"))

    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode("ascii")

    def encrypt(self, profile: UserProfileCreate) -> str:
        plaintext = profile.model_dump_json().encode("utf-8")
        return self._fernet.encrypt(plaintext).decode("ascii")

    def decrypt(self, encrypted_health_data: str) -> UserProfileCreate:
        plaintext = self._fernet.decrypt(encrypted_health_data.encode("ascii"))
        return UserProfileCreate.model_validate_json(plaintext)
