#!/usr/bin/env bash
set -euo pipefail

gunicorn -k uvicorn.workers.UvicornWorker --bind=0.0.0.0:${PORT:-8000} app.main:app
