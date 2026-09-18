"""Security and Secret Manager integration package for Aura Concierge Agent."""

from aura_concierge.security.secret_manager import (
    SecretManagerVault,
    get_secret_from_gcp,
)

__all__ = ["SecretManagerVault", "get_secret_from_gcp"]
