import hashlib
import hmac
import secrets

_ALGORITHM = "sha256"
_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(_ALGORITHM, password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_{_ALGORITHM}${_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iterations_text, salt_hex, digest_hex = stored.split("$")
        if scheme != f"pbkdf2_{_ALGORITHM}":
            return False
        derived = hashlib.pbkdf2_hmac(
            _ALGORITHM,
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations_text),
        )
        return hmac.compare_digest(derived.hex(), digest_hex)
    except (TypeError, ValueError):
        return False
