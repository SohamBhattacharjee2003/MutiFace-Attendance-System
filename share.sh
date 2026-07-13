#!/usr/bin/env bash
#
# share.sh — put PresenceAI on a PERMANENT public https:// link.
#
#     ./share.sh
#
# This replaces host.sh's Cloudflare quick-tunnel, which minted a NEW random
# *.trycloudflare.com hostname on every run — so every restart silently killed every
# /enroll link already handed to a student, and they got a Cloudflare 530. This hostname
# never changes. Share it once, put it in the report, reboot as often as you like.
#
# Flask serves BOTH the API and the built React app, so there is one origin, one tunnel
# and one link. (Two origins would mean CORS — and a frontend calling "localhost:5000"
# from a student's phone would be calling their own phone, not this laptop.)
#
# One-time setup: see SHARING.md. Student faces never leave this machine.

set -e
cd "$(dirname "$0")"

PORT=5000

# The Homebrew cask installs the GUI app; its CLI lives inside the bundle and is usually
# not on PATH.
TS="$(command -v tailscale 2>/dev/null || true)"
[ -n "$TS" ] || TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
if [ ! -x "$TS" ]; then
  echo "✗ Tailscale is not installed. Run the one-time setup in SHARING.md first:"
  echo "    brew install --cask tailscale"
  exit 1
fi

if ! "$TS" status >/dev/null 2>&1; then
  echo "✗ Tailscale is installed but not logged in. Run:"
  echo "    $TS up"
  exit 1
fi

echo "▸ Building the frontend…"
(cd Frontend && npm run build >/dev/null)

# The backend is yours to run — start it in another terminal with:
#     cd Server && ./venv/bin/python api.py
# Exposing a port that nothing is listening on just publishes a 502 to the whole internet.
if ! curl -sf "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
  echo
  echo "✗ Nothing is answering on :$PORT."
  echo "  Start the backend in another terminal, then re-run this:"
  echo
  echo "      cd Server && ./venv/bin/python api.py"
  echo
  exit 1
fi

echo "▸ Backend is up. Opening the public link…"
echo

# Funnel only accepts 443, 8443 and 10000 from the internet; it terminates TLS there and
# forwards to our plain-http :5000. Real certificate, so the browser will actually hand
# over the camera — getUserMedia() is refused on plain http from any host but localhost.
exec "$TS" funnel "$PORT"
