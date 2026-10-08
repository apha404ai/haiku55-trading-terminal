# HAIKU55 · 24/7 Crypto Trading Terminal

**Alpha404 · Live public market data · Autonomous paper trading · Optional AI council**

[![CI](https://github.com/apha404ai/haiku55-trading-terminal/actions/workflows/ci.yml/badge.svg)](https://github.com/apha404ai/haiku55-trading-terminal/actions/workflows/ci.yml)

> PAPER ONLY. This project does **not** place actual orders or trade real money. Public mid-prices can be real, but position execution and PnL are simulated. The archived originals were animated simulations with **entirely synthetic** market data and PnL; the public #21/#22 HTML files have now been converted into **static visual mockups**. No investment returns are promised.

## What works

- BTC, ETH and SOL perpetual indicative mid-prices from the Hyperliquid public allMids API.
- Always-on server-side price poller and autonomous, rules-only PAPER strategy.
- A polished dark/pink responsive HTML dashboard with current prices, price chart, paper equity and live paper positions.
- Stop/target management, fee/slippage assumptions, position-size caps and UTC daily realized loss cutoff.
- SQLite persistence for paper positions, closed trades and audit events.
- Authenticated paper LONG, SHORT, CLOSE, PAUSE, RESUME and latching KILL.
- Optional four-model AI council using configurable APIs: Anthropic (Haiku head), OpenAI (GPT), xAI (Grok), Google (Gemini). No model can bypass the hard-coded risk gate.
- Static, watermarked **#21 Haiku Desk** and **#22 Haiku Core** HTML concept layouts in frontend/legacy/: no JS, random numbers, timers, speed buttons, trading controls or model calls. The original versions remain identifiable in earlier Git history.
- Dockerfile, Railway config, automated CI and regression tests.

## Operating modes

| Variables | Behavior |
|---|---|
| AUTO_PAPER=0 | Manual paper orders only (requires control token) |
| AUTO_PAPER=1 and AI_MODE=0 (default) | Autonomous trend-heuristic PAPER trades, explicitly **RULES_ONLY**; zero model calls |
| AUTO_PAPER=1 and AI_MODE=1 | Four provider APIs vote on rule-prefiltered setups; all API keys + model IDs required; model errors or disagreement block trades |

**HAIKU55 is a project brand** and is not a verified Anthropic model identifier. Configure ANTHROPIC_MODEL to an actual available model ID supported by your provider. The Grok reviewer uses price-only numeric inputs, **not** live X/news feeds.

## Run on a computer

Requirements: Python 3.12+. No Python package installation needed.

    git clone https://github.com/apha404ai/haiku55-trading-terminal.git
    cd haiku55-trading-terminal
    export AUTO_PAPER=1
    export AI_MODE=0
    export CONTROL_TOKEN="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
    python -m app.server

Open http://localhost:8080. Enter your CONTROL_TOKEN into the browser to authorize manual paper controls. The app **does not auto-load** .env files; supply environment variables via your shell, Docker, or hosting provider. Never commit your keys.

Test locally:

    python -m unittest discover -s tests -v
    node --check frontend/app.js

Docker example:

    docker build -t haiku55 .
    docker run --rm -p 8080:8080 -v "$PWD/data:/data" -e DB_PATH=/data/haiku55.db -e CONTROL_TOKEN=REPLACE_WITH_LONG_RANDOM_SECRET -e AUTO_PAPER=1 -e AI_MODE=0 haiku55

## Deploy 24/7 on Railway

**The GitHub code is published, but it is not automatically hosted.** Continuous running requires a web host. The included Dockerfile and railway.json support Railway deployment.

1. Open Railway and create a project from the GitHub repository **apha404ai/haiku55-trading-terminal**.
2. Set service Variables: CONTROL_TOKEN to a long random secret, AUTO_PAPER=1, AI_MODE=0, DB_PATH=/data/haiku55.db.
3. Add a persistent volume mounted at **/data**, otherwise SQLite data may disappear after a redeploy.
4. Keep the service at **one replica**. The included railway.json sets an ALWAYS restart policy and a /health startup check.
5. Generate a public Railway domain and open its root URL on your phone. Monitor /api/status for feed freshness.
6. Add your real provider API keys and supported model IDs only if you later enable AI_MODE=1.

See [mobile deployment checklist](docs/DEPLOY.md) and [security notes](docs/SECURITY.md). Railway runs on a separate server, so your phone can be offline while it is operating. Uptime, network access and profitable performance are never guaranteed.

## Model credentials (optional)

| Role | Key | Provider model ID |
|---|---|---|
| Head · Haiku | ANTHROPIC_API_KEY | ANTHROPIC_MODEL |
| Risk reviewer · GPT | OPENAI_API_KEY | OPENAI_MODEL |
| Sentiment reviewer · Grok | XAI_API_KEY | XAI_MODEL |
| Market reviewer · Gemini | GEMINI_API_KEY | GEMINI_MODEL |

Use exact supported model IDs from provider accounts; APIs and availability change. Model calls cost money. If any provider fails, models disagree or response JSON is malformed, AI council abstains. Only numerical market observations are passed, so no real headline sentiment or orderbook analysis is being claimed.

## Paper risk limits

| Gate | Default |
|---|---|
| Maximum positions | 3 |
| Risk budget per entry | 0.5% of current cash |
| Notional per position | 20% of current cash |
| UTC day realized-loss cutoff | 3% of day opening cash |
| Stop / take profit distance | 1% / 2% |
| Assumed fee/slippage per side | 4 / 2 bps |
| Symbol cooldown after exit | 600 seconds (in-memory) |
| Maximum stale-feed age at entry | 20 seconds |
| Minimum signal confidence | 65% |

This is **not production-ready for real money**. Risk is not collateral accounting. Stop triggers use public mids, with approximate fills; funding, liquidation risk, order book liquidity, exchange precision and actual brokerage costs are not modeled. The daily risk cutoff counts **realized** PnL only. The KILL flag persists across restarts; if the feed is stale, paper positions may stay unresolved. There is no unauthenticated kill-reset endpoint.

## API and access

- GET / : new dashboard with real public mids when available.
- GET /health : HTTP service health + last feed status.
- GET /api/status : public read-only paper account status.
- GET /api/trades : public paper closed-trade history.
- POST /api/order : JSON symbol + LONG/SHORT, Bearer CONTROL_TOKEN required.
- POST /api/close : JSON symbol, Bearer CONTROL_TOKEN required.
- POST /api/control : JSON action pause/resume/kill, Bearer CONTROL_TOKEN required.

On a public Railway domain the GET account data is public. Use private hosting or an upstream login if that is unsuitable. POST is token protected; no real exchange endpoints exist in this repository.

## Source structure

- app/server.py — continuous market polling and authenticated HTTP controls
- app/engine.py — SQLite paper orders and deterministic trade risk
- app/council.py — optional four-provider review
- frontend/index.html + frontend/app.js — live-data paper dashboard
- frontend/legacy/21-haiku-desk.html — static, watermarked HTML mockup (no simulation)
- frontend/legacy/22-haiku-core.html — static, watermarked HTML mockup (no simulation)
- docs/SOURCE.md — source and transparency
- docs/DEPLOY.md — hosting steps
- docs/SECURITY.md — known limits
- tests/test_engine.py — no-network regression tests

These concepts are adapted from the author's Mason333xbt/writer source branch claude/pensive-volta-lathuj. The original Git blobs were preserved in earlier commits; current HTML files are visual-only adaptations with permanent @alpha404ai watermarks. Open either file directly from the folder in a browser (its mockup.css and ../assets/*.png files must stay alongside it). The $HAIKU55 ticker mentioned in social posts is not an integrated token or deployment instruction.
