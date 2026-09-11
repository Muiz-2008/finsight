import bcrypt

# bcrypt: a deliberately slow, salted hash designed for passwords (unlike
# SHA-256/MD5, which are fast and therefore bad for this — speed is what
# makes brute-forcing cheap). gensalt() embeds a fresh random salt into
# every hash, so two users with the same password get different hashes.
#
# bcrypt's algorithm caps input at 72 bytes; UserCreate enforces
# max_length=72 on the plaintext password so this never raises in practice.


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
