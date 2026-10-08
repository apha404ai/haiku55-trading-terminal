# HAIKU55 operational and financial safety

## Current execution boundaries

- Exchange calls are **read-only public market queries** using Hyperliquid's info endpoint (POST /info with type allMids).
- NO exchange keys, seed phrases, private keys, wallets, signatures or real-order APIs are used.
- All positions, PnL, stops and targets are paper-only SQLite records. Original terminal animations under frontend/legacy are fake/demo simulations, independent of the new backend.
- Provider model outputs are parsed as data only, are not executable programs, and do not override the deterministic risk gate.
- Four-model review is optional. When enabled but not configured or providers fail, AI council abstains.

## Risk engine limitations

The software is a prototype for education/testing; it is NOT suitable for real-money unattended execution. It lacks independent exchange-order reconciliation, liquidation accounting, precision constraints, real orderbook volume, latency-sensitive slippage, fee tier discovery, funding, position margin checks, hedging/cross margin and resilient multi-process locking.

Stops operate on an observed public mid-price with assumed slippage. Actual fills in a fast market may be much worse. In the current engine daily loss cutoffs use realized PnL only; open drawdown does not count toward the cutoff. Per-symbol cooldowns and historical sampled prices are in memory and reset on service restart. Do not interpret sample frequency as streaming exchange fills.

On a KILL action the engine attempts to close paper positions at the last fresh observed price and writes a persistent lock. If feed data is stale, positions remain unresolved rather than receiving fictional fills. There is no API action to reset the kill lock; deliberate offline maintenance/reset of the paper database is required.

## Web security and permissions

- POST actions require a long secret CONTROL_TOKEN in an Authorization Bearer header.
- If CONTROL_TOKEN is unset, all POST operations fail closed.
- GET /api/status and GET /api/trades are **not authenticated**. Anyone with access to the public Railway domain can see paper holdings and event history. Put the service behind upstream auth or a private network for account privacy.
- Set secret variables only in the deployment's encrypted variable manager, never in the repo, screenshots, browser URLs or public posts.
- Be alert to clipboard-sharing or browser extensions that expose a token typed in the dashboard.
- Deploy one replica with a persistent volume. Multiple replicas may duplicate strategy decisions or corrupt the ledger.
- Read-only market feed failure marks prices STALE and blocks new paper orders. The dashboard must not silently substitute generated numbers for market data.
- Model APIs can change or fail; user remains responsible for validating account permissions, billing and model identifiers.

## How to safely extend

For real exchange execution later, do not simply add wallet keys to this application. Use a segregated execution service, signed order authorization, reconciliation, explicit HUMAN approval of meaningful risk, risk limits including **unrealized** loss, tested order lifecycle and a separate secret-management architecture. Obtain operator approval and test thoroughly on testnet first.

Social-media marketing claims about returns should always disclose whether the results were simulated or real, and should not imply that arbitrary AI reviewers execute orders or guarantee profits.
