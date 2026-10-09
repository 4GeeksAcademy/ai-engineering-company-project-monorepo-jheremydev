#!/bin/sh
set -eu

npm run dev --workspace=uis/backoffice -- --configLoader runner --host 0.0.0.0 --port "${BACKOFFICE_PORT:-5173}" &
backoffice_pid=$!
npm run dev --workspace=uis/website -- --host 0.0.0.0 --port "${WEBSITE_PORT:-5174}" &
website_pid=$!

trap 'kill "$backoffice_pid" "$website_pid" 2>/dev/null || true' INT TERM
wait