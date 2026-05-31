#!/usr/bin/env bash
set -e
python3 scripts/generate_openapi.py
if git diff --exit-code apps/api/openapi.json; then
  echo "✅ OpenAPI schema is up to date"
else
  echo "❌ OpenAPI schema drift detected — run scripts/generate_openapi.py"
  exit 1
fi
