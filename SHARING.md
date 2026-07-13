# Putting PresenceAI on a public link

The app runs on your laptop. `./share.sh` gives it a permanent public HTTPS address so
students can enrol from their own phones, from anywhere.

```
https://<your-machine>.<your-tailnet>.ts.net
```

That hostname **never changes**. Share it once; it survives reboots.

## Why not just deploy it somewhere?

Because the free tiers can't run it, and the ones that can want a credit card. Measured:

| Host | Verdict |
|---|---|
| Render free | 0.1 CPU → **69 s per face**; 512 MB → OOM; **no persistent disk**, so every enrolled student is wiped on the 15-minute idle spin-down |
| Hugging Face Spaces | Docker SDK is now a paid feature |
| Cloud Run | filesystem is in-memory; it auto-scales, and liveness + vote state live in one process's memory, so a second instance means nobody ever reaches quorum |
| GCP / Oracle / Fly / Railway | work fine — all require a card |

Tailscale Funnel is free, needs no card, and issues a real Let's Encrypt certificate.
The certificate is not a nicety: **browsers refuse `getUserMedia()` — the camera — on
plain http.** No certificate, no camera, no attendance.

## One-time setup (~10 minutes)

**1. Install Tailscale and sign in** (a Google account is enough — no card):

```sh
brew install --cask tailscale
open -a Tailscale          # sign in when the menu-bar icon appears
```

**2. Turn on the two features Funnel depends on.** In the admin console at
<https://login.tailscale.com/admin/dns>:

- enable **MagicDNS**
- click **Enable HTTPS**

Without these there is no hostname to issue a certificate for, and `share.sh` fails with
a cryptic error about the tailnet policy.

**3. Note your machine's name** — the admin console shows it. That plus your tailnet
gives you the URL above.

## Every time you want to share

Two terminals.

```sh
# terminal 1 — the backend (yours to run; it prints the model-load progress)
cd Server && ./venv/bin/python api.py

# terminal 2 — the public link
./share.sh
```

`share.sh` builds the frontend, checks the backend is alive, and prints the URL. Leave it
running. `Ctrl-C` takes the link down; the hostname is still reserved, so the next run
brings the *same* URL back.

## What the examiners see

Open the link on the projector. Students scan a QR code pointing at
`https://<...>.ts.net/enroll/<class-code>` and enrol from their phones, live. It's a real
domain with a padlock. Where the box physically sits is invisible to them — and plenty of
real products are demoed exactly this way.

## The catch, stated plainly

**Your laptop must be awake while the link is in use.** That's the whole trade.

In practice it costs you nothing: students enrol in a window you announce, and the demo is
half an hour with you sitting in front of the machine. Nobody is hitting the server at
3 a.m.

Two things to do before a session:

```sh
caffeinate -di        # stop the Mac sleeping while it's serving
```

and keep it plugged in — the camera loop and ONNX inference will drain a battery.

## If you later get a card, or a college Azure account

Nothing here is wasted. `docker compose up -d --build` on any Ubuntu VM runs the identical
app 24/7, and you keep the same enrolment links by pointing a domain at it. `Dockerfile`,
`docker-compose.yml` and `Caddyfile` are already in this repo and already work.
