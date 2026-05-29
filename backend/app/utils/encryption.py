"""Fernet symmetric encryption for external API keys at rest."""

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.encryption_key.encode())


def encrypt(plaintext: str) -> str:
    """Encrypt plaintext and return a base64-encoded ciphertext string."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a Fernet ciphertext string and return the original plaintext."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt API key") from exc
