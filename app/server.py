"""HAIKU55 HTTP dashboard and continuously running PAPER market loop."""
import hmac
import json
import math
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from app.council import configured, evaluate
from app.engine import PaperEngine, SYMBOLS

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = os.getenv("DB_PATH", str(ROOT / "data" / "haiku55.db"))
ENGINE = PaperEngine(db_path=DATA_PATH, starting_balance=float(os.getenv("STARTING_BALANCE", "10000")))
TOKEN = os.getenv("CONTROL_TOKEN", "")
AUTO_PAPER = os.getenv("AUTO_PAPER", "1").lower() in ("1", "true", "yes")
AI_MODE = os.getenv("AI_MODE", "0").lower() in ("1", "true", "yes")
POLL_SECONDS = max(2.0, float(os.getenv("POLL_SECONDS", "5")))
SCAN_SECONDS = max(30.0, float(os.getenv("SCAN_SECONDS", "60")))
SOURCE_URL = "https://api.hyperliquid.xyz/info"
RUNNING = True
WORKER = {"last_poll_error": None, "last_poll_at": None, "auto_paper": AUTO_PAPER,
          "ai_enabled": AI_MODE, "models_configured": configured(), "last_scan_at": None}


def market_fetch():
    """Public Hyperliquid perp mids. Response is real data or raises an error."""
    req = urllib.request.Request(SOURCE_URL, data=b'{"type":"allMids","dex":""}',
                                 headers={"Content-Type": "application/json", "User-Agent": "HAIKU55-paper/1.0"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read(100000))
    if not isinstance(data, dict):
        raise ValueError("Unexpected market data payload")
    prices = {}
    for s in SYMBOLS:
        if s not in data:
            raise ValueError(f"Market response missing {s}")
        value = float(data[s])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"Invalid price for {s}")
        prices[s] = value
    return prices


def poll_worker():
    while RUNNING:
        try:
            prices = market_fetch()
            ENGINE.update_prices(prices)
            WORKER["last_poll_at"] = time.time()
            WORKER["last_poll_error"] = None
        except Exception as exc:
            WORKER["last_poll_error"] = f"{type(exc).__name__}: {str(exc)[:150]}"
            # Never invent a market price or place orders after a feed failure.
        time.sleep(POLL_SECONDS)


def strategy_worker():
    while RUNNING:
        if AUTO_PAPER and not ENGINE._get("paused") and not ENGINE._get("killed"):
            try:
                st = ENGINE.status()
                if st["feed_status"] == "LIVE":
                    for symbol in SYMBOLS:
                        if symbol in {p["symbol"] for p in st["positions"]}:
                            continue
                        raw = ENGINE.rule_signal(symbol)
                        if raw["side"] == "WAIT":
                            continue
                        if AI_MODE:
                            result = evaluate(symbol, raw, st["prices"], st["history"][symbol])
                        else:
                            result = {**raw, "source": "RULES_ONLY", "votes": []}
                        ENGINE.last_signal = {"symbol": symbol, "at": time.time(), **result}
                        if result["side"] != "WAIT":
                            ENGINE.open(symbol, result["side"], result["confidence"], result["source"])
                WORKER["last_scan_at"] = time.time()
            except Exception as exc:
                WORKER["last_strategy_error"] = f"{type(exc).__name__}: {str(exc)[:150]}"
        time.sleep(SCAN_SECONDS)


class Handler(BaseHTTPRequestHandler):
    server_version = "HAIKU55/1.0"

    def _send(self, status, data, ctype="application/json; charset=utf-8"):
        if isinstance(data, (dict, list)):
            raw = json.dumps(data, separators=(",", ":"), allow_nan=False).encode("utf-8")
        elif isinstance(data, str):
            raw = data.encode("utf-8")
        else:
            raw = data
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def _authorized(self):
        header = self.headers.get("Authorization", "")
        return bool(TOKEN) and hmac.compare_digest(header, "Bearer " + TOKEN)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, (ROOT / "frontend" / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/static/app.js":
            self._send(200, (ROOT / "frontend" / "app.js").read_bytes(), "text/javascript; charset=utf-8")
        elif path == "/health":
            st = ENGINE.status()
            self._send(200, {"ok": True, "mode": "PAPER", "feed_status": st["feed_status"],
                             "last_poll_error": WORKER.get("last_poll_error")})
        elif path == "/api/status":
            st = ENGINE.status()
            st["service"] = dict(WORKER)
            st["service"]["controls_available"] = bool(TOKEN)
            self._send(200, st)
        elif path == "/api/trades":
            self._send(200, {"trades": ENGINE.trades()})
        else:
            self._send(404, {"error": "NOT_FOUND"})

    def do_POST(self):
        if not self._authorized():
            self._send(401, {"ok": False, "reason": "AUTH_REQUIRED_OR_DISABLED"})
            return
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            self._send(415, {"ok": False, "reason": "JSON_ONLY"})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
            if not 0 <= length <= 4096:
                raise ValueError("Payload too large or missing")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Body must be an object")
        except (ValueError, TypeError, json.JSONDecodeError):
            self._send(400, {"ok": False, "reason": "INVALID_JSON"})
            return
        path = urlparse(self.path).path
        if path == "/api/order":
            side = body.get("side")
            symbol = body.get("symbol")
            result = ENGINE.open(symbol, side, confidence=1, source="HUMAN_PAPER")
        elif path == "/api/close":
            result = ENGINE.close(body.get("symbol"))
        elif path == "/api/control":
            result = ENGINE.set_control(body.get("action"))
        else:
            self._send(404, {"error": "NOT_FOUND"})
            return
        self._send(200 if result["ok"] else 409, result)


def main():
    port = int(os.getenv("PORT", "8080"))
    threading.Thread(target=poll_worker, name="market-poll", daemon=True).start()
    threading.Thread(target=strategy_worker, name="paper-strategy", daemon=True).start()
    print(f"HAIKU55 PAPER server on 0.0.0.0:{port}, auto={AUTO_PAPER}, ai={AI_MODE}, providers_configured={configured()}", flush=True)
    with ThreadingHTTPServer(("0.0.0.0", port), Handler) as server:
        server.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    main()
