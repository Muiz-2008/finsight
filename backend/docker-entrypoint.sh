#!/bin/sh
# Runs migrations, then starts the API. Kept as a real script file rather
# than a `dockerCommand`/`startCommand` one-liner in render.yaml — Render's
# blueprint parser doesn't reliably preserve nested shell quoting in a YAML
# string (a `sh -c "a && b"` override there failed with exit 127, "command
# not found", because the quoting didn't survive however Render splits that
# field). A script file sidesteps the whole class of problem, and unifies
# behavior between Docker Compose (local) and Render (production) — one
# script, not two different command strings to keep in sync.
set -e

alembic upgrade head

# $PORT is set by Render at runtime; falls back to 8000 for local/Compose
# use, where docker-compose.yml maps a fixed host port instead.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
