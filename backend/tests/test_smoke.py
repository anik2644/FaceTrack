"""Smoke tests that exercise the app without heavy ML dependencies.

These validate wiring (config, security, health, auth) rather than the vision
pipeline, so they run quickly in CI even where dlib/YOLO are unavailable.
"""
from __future__ import annotations

import numpy as np

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.person_service import bytes_to_encoding, encoding_to_bytes


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("s3cret")
    assert hashed != "s3cret"
    assert verify_password("s3cret", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip() -> None:
    token = create_access_token("admin", {"role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "admin"
    assert payload["role"] == "admin"


def test_encoding_serialisation_roundtrip() -> None:
    vector = np.random.rand(128).astype(np.float64)
    restored = bytes_to_encoding(encoding_to_bytes(vector))
    assert np.allclose(vector, restored)
