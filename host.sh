#!/usr/bin/env bash
#
# host.sh — put the whole app on a public https:// link.
#
# Flask serves BOTH the API and the built React app, so there is one origin and therefore
# one tunnel and one URL. (Two origins would mean CORS, two tunnels, and two links to hand
# out — and the student's browser calling "localhost:5000" would be calling their own
# phone, not this laptop.)
#
#     ./host.sh
#
# Everything runs on this machine. Student faces never leave it.

set -e
cd "$(dirname "$0")"

echo "▸ Building the frontend…"
(cd Frontend && npm run build >/dev/null 2>&1)

echo "▸ Starting the backend on :5000…"
(cd Server && ./venv/bin/python api.py) &
API_PID=$!
trap 'kill $API_PID 2>/dev/null; pkill -f "cloudflared tunnel" 2>/dev/null; exit' INT TERM

# wait for the model to load (~5s) before exposing anything
for i in $(seq 1 40); do
  curl -sf http://127.0.0.1:5000/api/health >/dev/null 2>&1 && break
  sleep 0.5
done

echo "▸ Opening the public tunnel…"
echo
cloudflared tunnel --url http://localhost:5000 2>&1 | while read -r line; do
  # cloudflared prints the URL once, buried in its banner — pull it out and show it clearly
  if [[ "$line" =~ (https://[a-z0-9-]+\.trycloudflare\.com) ]]; then
    URL="${BASH_REMATCH[1]}"
    echo
    echo "  ╭──────────────────────────────────────────────────────────────╮"
    echo "  │  LIVE                                                        │"
    echo "  ╰──────────────────────────────────────────────────────────────╯"
    echo
    echo "    Teacher   $URL/login"
    echo "    Students  $URL/classes  →  copy the enrolment link from a class"
    echo
    echo "    Share that /enroll/<code> link. Only roll numbers you put on the"
    echo "    roster can use it — a stranger with the link has nothing to claim."
    echo
    echo "    Ctrl-C to stop. The link dies when this laptop sleeps."
    echo
  fi
done
