# Deploy HAIKU55 on Railway from an iPhone

The repository exists on GitHub, but **GitHub by itself does not run the terminal 24/7**. You need a server. Railway can run the Dockerfile from the repository and automatically deploy updates.

## Step-by-step

1. Connect the **Railway** plugin to ChatGPT if you would like help creating and managing Railway services directly in this chat; connecting the plugin requires your explicit approval. Or go to https://railway.com in Safari and log in.
2. Choose **New Project → Deploy from GitHub repo**.
3. Authorize Railway to access GitHub account **apha404ai** and select **haiku55-trading-terminal**. Keep source branch **main**.
4. The existing Dockerfile starts the Python server. The existing railway.json defines restart policy ALWAYS, healthcheck endpoint /health and one replica.
5. Open service **Variables** and configure:
   - CONTROL_TOKEN: a random high-entropy secret; never share it in public.
   - AUTO_PAPER: 1
   - AI_MODE: 0
   - DB_PATH: /data/haiku55.db
   - PORT: **do not set it yourself** unless required; Railway normally injects PORT.
6. **Storage:** add a persistent Volume attached to the same service with mount path **/data**. Without a volume, paper positions may disappear during deployment or replacement. Do not use multiple running replicas with this in-process strategy scheduler.
7. Save/Deploy and wait for success. Under **Networking**, generate a public domain for your service.
8. Open the domain URL. The dashboard should appear. After the live feed connects, LIVE status, actual mid-prices and chart observations populate; no mock fallback occurs if the feed fails.
9. Open /health and /api/status from the same domain to see server and market-feed state.
10. Enter CONTROL_TOKEN in the terminal to authorize manual paper orders or pause/kill. Store the token in a password manager. Do not save it in GitHub.

## Optional real model votes

Leave AI_MODE=0 while testing the basic trading engine. For true API calls, configure **all eight** credentials/settings: ANTHROPIC_API_KEY + ANTHROPIC_MODEL, OPENAI_API_KEY + OPENAI_MODEL, XAI_API_KEY + XAI_MODEL, GEMINI_API_KEY + GEMINI_MODEL. Set AI_MODE=1 only when supported provider model IDs are known. Missing or failed providers cause a WAIT decision, not an invented vote.

## Monitoring 24/7

- Railway service must remain deployed as a **persistent service**, rather than a cron job or temporary preview.
- Railway restart policy is ALWAYS; it does not guarantee zero interruptions or continuous network availability.
- Railway /health is a deployment-startup probe, not an ongoing uptime test. Monitor the feed_status value in /api/status for STALE conditions and subscribe to platform uptime alerts if desired.
- Railway may charge for persistent compute and volumes; check their current pricing.
- GitHub Actions CI is for verification, **not** running the terminal continuously.
- The token-protected POST operations only change the PAPER ledger. The unprotected GET endpoints reveal paper trade history; add upstream access control if privacy is required.

## What cannot be done from a GitHub repo alone

A public GitHub repository does not provide a constantly running Python application. The static #21/#22 HTML mockups in `frontend/legacy/` are visual-only designs with no JavaScript or backend dependency; they are not the live-data dashboard. Deploy the provided Dockerfile to a server to access the separate paper-trading backend dashboard at `/`. Deploy the provided Dockerfile to a server to access the live-data PAPER dashboard.

## Troubleshooting

- "FEED STALE": inspect Railway logs, internet access, Hyperliquid response, timeout and rate limits. New orders are blocked when data is stale.
- "AUTH_REQUIRED_OR_DISABLED": set CONTROL_TOKEN in Railway variables, redeploy and enter the exact value in the dashboard.
- "No trades yet": the default trend prefilter requires 36 valid price samples and a qualifying price move; "24/7" does not mean placing an order every minute.
- PnL resets after deployment: mount a persistent volume at /data and use DB_PATH=/data/haiku55.db.
- AI reviewers show OFFLINE: AI_MODE=0 or model keys/IDs are missing. The UI does not fake API calls.
- KILL remains active: intended. It is persisted and has no network reset endpoint; maintenance/reset of the **paper** database must be done deliberately offline.
