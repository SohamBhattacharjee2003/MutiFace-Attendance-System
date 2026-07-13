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
#
# ── the link you hand out ─────────────────────────────────────────────────────────────
# A free Cloudflare quick-tunnel gets a NEW random hostname every run, so handing students
# the tunnel URL directly means every link you already shared dies the moment you restart —
# that is where the Cloudflare 530s came from.
#
# So students get a GitHub Pages URL instead, which never changes, and this script rewrites
# the redirect it contains on every start. Share the Pages link once; it is still correct
# next week, and it is safe to put in the report.
#
# One-time setup: GitHub → Settings → Pages → Source: "Deploy from a branch",
#                 Branch: master, Folder: /docs → Save.

set -e
cd "$(dirname "$0")"

# github.io hostnames are lowercase. Not ${VAR,,} — macOS ships bash 3.2, where that is a
# syntax error, and this script exists to run on exactly that machine.
REPO_URL="$(git config --get remote.origin.url)"
REPO_USER="$(echo "$REPO_URL" | sed -E 's#.*[:/]([^/]+)/[^/]+$#\1#' | tr '[:upper:]' '[:lower:]')"
REPO_NAME="$(basename -s .git "$REPO_URL")"
PAGES_URL="https://${REPO_USER}.github.io/${REPO_NAME}"

echo "▸ Building the frontend…"
(cd Frontend && npm run build >/dev/null)

echo "▸ Starting the backend on :5000…"
(cd Server && ./venv/bin/python api.py) &
API_PID=$!
trap 'kill $API_PID 2>/dev/null; pkill -f "cloudflared tunnel" 2>/dev/null; exit' INT TERM

# Wait for the model to load (~5s) before exposing anything — a tunnel pointing at a port
# that answers 502 is worse than no tunnel.
for i in $(seq 1 40); do
  curl -sf http://127.0.0.1:5000/api/health >/dev/null 2>&1 && break
  sleep 0.5
done

# Publish the new tunnel hostname to the permanent link.
publish() {
  local url="$1"
  local stamp; stamp="$(date '+%d %b, %H:%M')"
  # These are the only two lines in docs/index.html that ever change.
  sed -i '' \
    -e "s#^  const TUNNEL = \".*\";#  const TUNNEL = \"${url}\";#" \
    -e "s#^  const UPDATED = \".*\";#  const UPDATED = \"${stamp}\";#" \
    docs/index.html
  if git diff --quiet docs/index.html; then return 0; fi
  git add docs/index.html
  git commit -qm "Point the permanent link at the current tunnel" || return 0
  git push -q origin HEAD 2>/dev/null || {
    echo "  ⚠ could not push — students will still reach the OLD tunnel."
    echo "    Run: git push origin master"
    return 0
  }
}

echo "▸ Opening the public tunnel…"
echo
cloudflared tunnel --url http://localhost:5000 2>&1 | while read -r line; do
  # cloudflared prints the URL once, buried in its banner — pull it out and show it clearly
  if [[ "$line" =~ (https://[a-z0-9-]+\.trycloudflare\.com) ]]; then
    URL="${BASH_REMATCH[1]}"
    echo "▸ Publishing it to the permanent link…"
    publish "$URL"
    echo
    echo "  ╭──────────────────────────────────────────────────────────────╮"
    echo "  │  LIVE                                                        │"
    echo "  ╰──────────────────────────────────────────────────────────────╯"
    echo
    echo "    SHARE THIS — it never changes, even after a restart:"
    echo
    echo "      $PAGES_URL"
    echo
    echo "    Teacher   $URL/login"
    echo "    Students  $URL/classes  →  copy a class's enrolment link, then hand out"
    echo "                                 $PAGES_URL/#/enroll/<code>"
    echo
    echo "    Only roll numbers on the roster can enrol — a stranger with the link"
    echo "    has nothing to claim."
    echo
    echo "    Ctrl-C to stop. While this laptop is asleep the permanent link shows"
    echo "    \"not open right now\" instead of a Cloudflare error."
    echo
  fi
done
