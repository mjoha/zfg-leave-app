from app.security import hash_password, verify_password


def test_password_hashes_are_salted_and_verifiable():
    first = hash_password("correct-horse")
    second = hash_password("correct-horse")

    assert first != second
    assert first.startswith("pbkdf2_sha256$600000$")
    assert verify_password("correct-horse", first)
    assert verify_password("correct-horse", second)
    assert not verify_password("incorrect", first)
    assert not verify_password("correct-horse", "not-a-hash")
