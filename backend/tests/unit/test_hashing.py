from app.security.hashing import hash_password, verify_password


def test_verify_accepts_correct_password():
    hashed = hash_password("correcthorsebatterystaple")

    assert verify_password("correcthorsebatterystaple", hashed) is True


def test_verify_rejects_wrong_password():
    hashed = hash_password("correcthorsebatterystaple")

    assert verify_password("wrong-password", hashed) is False


def test_same_password_hashes_differently_each_time():
    # bcrypt salts each hash, so two hashes of the same password must differ
    # even though both verify correctly — this is what defeats rainbow tables.
    first = hash_password("correcthorsebatterystaple")
    second = hash_password("correcthorsebatterystaple")

    assert first != second
    assert verify_password("correcthorsebatterystaple", first)
    assert verify_password("correcthorsebatterystaple", second)
