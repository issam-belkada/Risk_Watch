from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hash = PasswordHash.recommended()


def hasher_mot_de_passe(mot_de_passe: str) -> str:
    return password_hash.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hache: str) -> bool:
    return password_hash.verify(mot_de_passe, hache)


def creer_token(user_id: int) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expiration}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)