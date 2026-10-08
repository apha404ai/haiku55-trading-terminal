"""Optional four-provider AI council. No model has permission to execute orders."""
import concurrent.futures
import json
import os
import re
import urllib.request

PROVIDERS = (
    ("HAIKU", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"),
    ("GPT", "OPENAI_API_KEY", "OPENAI_MODEL"),
    ("GROK", "XAI_API_KEY", "XAI_MODEL"),
    ("GEMINI", "GEMINI_API_KEY", "GEMINI_MODEL"),
)


def configured():
    return all(os.getenv(k) and os.getenv(m) for _, k, m in PROVIDERS)


def _post(url, headers, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.loads(response.read(100_000))


def _parse(message):
    # Only a small strict JSON-shaped answer is accepted. The model's prose is never executed.
    match = re.search(r"\{[\s\S]*?\}", message or "")
    if not match:
        return {"side": "WAIT", "confidence": 0, "reason": "Invalid JSON response"}
    try:
        obj = json.loads(match.group(0))
        side = str(obj.get("side", "WAIT")).upper()
        conf = float(obj.get("confidence", 0))
        if side not in {"LONG", "SHORT", "WAIT"} or not 0 <= conf <= 1:
            raise ValueError("Invalid decision")
        return {"side": side, "confidence": conf, "reason": str(obj.get("reason", ""))[:140]}
    except (ValueError, TypeError, json.JSONDecodeError):
        return {"side": "WAIT", "confidence": 0, "reason": "Malformed decision"}


def _call(label, prompt):
    if label == "HAIKU":
        result = _post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
            {"model": os.environ["ANTHROPIC_MODEL"], "max_tokens": 180,
             "messages": [{"role": "user", "content": prompt}]},
        )
        message = "".join(p.get("text", "") for p in result.get("content", []) if p.get("type") == "text")
    elif label in ("GPT", "GROK"):
        key = "OPENAI" if label == "GPT" else "XAI"
        url = "https://api.openai.com/v1/chat/completions" if label == "GPT" else "https://api.x.ai/v1/chat/completions"
        result = _post(
            url, {"Authorization": "Bearer " + os.environ[key + "_API_KEY"]},
            {"model": os.environ[key + "_MODEL"], "messages": [{"role": "user", "content": prompt}],
             "max_completion_tokens": 180},
        )
        message = result["choices"][0]["message"].get("content") or ""
    else:
        from urllib.parse import quote
        model = quote(os.environ["GEMINI_MODEL"], safe="-._")
        result = _post(
            "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent",
            {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
            {"contents": [{"parts": [{"text": prompt}]}],
             "generationConfig": {"maxOutputTokens": 180}},
        )
        message = "".join(p.get("text", "") for c in result.get("candidates", [])
                          for p in c.get("content", {}).get("parts", []))
    return _parse(message)


def evaluate(symbol, signal, prices, history):
    """Fail closed on missing keys, API errors or model disagreement."""
    if not configured():
        return {"side": "WAIT", "confidence": 0, "source": "AI_UNAVAILABLE",
                "votes": [], "reason": "Configure all four API keys and model identifiers"}
    if signal.get("side") not in ("LONG", "SHORT"):
        return {"side": "WAIT", "confidence": 0, "source": "AI_COUNCIL", "votes": [],
                "reason": "Rule prefilter did not identify a setup"}
    prompt = (
        "You are one of four independent crypto paper-trading reviewers. You cannot execute orders. "
        "Use only these numerical inputs. Respond with a SINGLE JSON object and no other text: "
        '{"side":"LONG|SHORT|WAIT","confidence":0.0,"reason":"up to 100 chars"}. '
        "Conservatively vote WAIT if insufficient information. "
        f"Asset: {symbol}-PERP. Public indicative mid prices: {json.dumps(prices)}. "
        f"Recent mark samples: {json.dumps(history[-36:])}. "
        f"Rule prefilter: {json.dumps(signal)}. "
        "Do not assume spreads, funding, volumes, liquidity or real-time news are known."
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {label: pool.submit(_call, label, prompt) for label, _, _ in PROVIDERS}
        votes = []
        for label, future in futures.items():
            try:
                vote = future.result(timeout=12)
            except Exception as exc:
                vote = {"side": "WAIT", "confidence": 0,
                        "reason": "Provider unavailable: " + type(exc).__name__}
            votes.append({"model": label, **vote})
    selected = signal["side"]
    # Require Haiku as head and at least 3 of 4 agreeing; no conflicting vote allowed.
    approve = sum(v["side"] == selected and v["confidence"] >= .65 for v in votes)
    conflict = any(v["side"] not in (selected, "WAIT") for v in votes)
    head_ok = votes[0]["side"] == selected and votes[0]["confidence"] >= .65
    accepted = approve >= 3 and not conflict and head_ok
    confidence = sum(v["confidence"] for v in votes if v["side"] == selected) / max(1, approve)
    return {"side": selected if accepted else "WAIT", "confidence": round(confidence, 3),
            "source": "AI_COUNCIL", "votes": votes,
            "reason": "Council approved" if accepted else "Council abstained / disagreed"}
