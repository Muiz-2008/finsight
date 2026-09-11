import os

# Must run before anything imports app.config: Settings.secret_key has no
# default (by design — a real deployment must supply one), and
# get_settings() is @lru_cache'd, so this needs to land before the first
# call anywhere in the test session.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-do-not-use-in-prod")
