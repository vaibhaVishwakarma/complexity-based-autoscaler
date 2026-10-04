#!/usr/bin/env python3
"""
scratch/test_models_matrix.py

Role:
    Tests candidate Gemini models across all 4 API keys in .env.backup,
    measuring:
      - 4/4 key compatibility
      - Token consumption (prompt, completion, total tokens)
      - Latency (seconds)
    Ranks the candidates to find the top 2-3 models that work for all keys,
    preferring models with lower token consumption.
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BACKUP_FILE = WORKSPACE_ROOT / ".env.backup"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

# Comprehensive list of Flash and Lite models from API catalog
CANDIDATE_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
]

TEST_PROMPT = "Calculate 12 * 12 and output only the number."


def test_model_on_key(key: str, model: str) -> dict:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "max_tokens": 50,
    }).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            elapsed = time.time() - t0
            body = json.loads(resp.read().decode("utf-8"))
            usage = body.get("usage", {})
            choice = body.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            return {
                "ok": True,
                "status": resp.status,
                "latency": round(elapsed, 2),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "sample_output": choice[:40],
                "error": "",
            }
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        err_msg = ""
        try:
            body = json.loads(e.read().decode("utf-8"))
            err_msg = body.get("error", {}).get("message", "")[:80]
        except Exception:
            err_msg = str(e)[:80]
        return {
            "ok": False,
            "status": e.code,
            "latency": round(elapsed, 2),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "sample_output": "",
            "error": f"HTTP {e.code}: {err_msg}",
        }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status": 0,
            "latency": round(elapsed, 2),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "sample_output": "",
            "error": str(e)[:80],
        }


def main():
    keys = [
        line.strip()
        for line in BACKUP_FILE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    print("=" * 80)
    print(f" TESTING CANDIDATE MODELS ACROSS {len(keys)} API KEYS")
    print(f" Goal: Select 2-3 universal models (preferring low token consumption)")
    print("=" * 80 + "\n")

    summary = {}

    for model in CANDIDATE_MODELS:
        print(f"Testing {model:<26} ... ", end="", flush=True)
        key_results = []
        for i, k in enumerate(keys, 1):
            res = test_model_on_key(k, model)
            key_results.append(res)
            time.sleep(0.2)

        passes = sum(1 for r in key_results if r["ok"])
        valid_results = [r for r in key_results if r["ok"]]

        avg_lat = round(sum(r["latency"] for r in valid_results) / max(1, len(valid_results)), 2)
        avg_comp_tokens = round(sum(r["completion_tokens"] for r in valid_results) / max(1, len(valid_results)), 1)
        avg_total_tokens = round(sum(r["total_tokens"] for r in valid_results) / max(1, len(valid_results)), 1)

        print(f"{passes}/{len(keys)} passed | avg total tokens: {avg_total_tokens} | avg latency: {avg_lat}s")

        summary[model] = {
            "passes": passes,
            "total_keys": len(keys),
            "avg_latency": avg_lat,
            "avg_comp_tokens": avg_comp_tokens,
            "avg_total_tokens": avg_total_tokens,
            "details": key_results,
        }

    print("\n" + "=" * 85)
    print(f"{'RANK':<5} | {'MODEL NAME':<26} | {'KEYS PASS':<10} | {'TOTAL TOKENS':<13} | {'LATENCY':<9} | {'STATUS'}")
    print("=" * 85)

    # Rank by: 1) pass rate desc, 2) total tokens asc, 3) latency asc
    ranked = sorted(
        summary.items(),
        key=lambda x: (
            -x[1]["passes"],
            x[1]["avg_total_tokens"] if x[1]["passes"] > 0 else 999999,
            x[1]["avg_latency"],
        ),
    )

    for rank, (model, data) in enumerate(ranked, 1):
        passes_str = f"{data['passes']}/{data['total_keys']}"
        tokens_str = f"{data['avg_total_tokens']:.1f}" if data["passes"] > 0 else "N/A"
        lat_str = f"{data['avg_latency']:.2f}s" if data["passes"] > 0 else "N/A"
        
        status = "RECOMMENDED CANDIDATE ✓" if data["passes"] == len(keys) else f"Failed {len(keys) - data['passes']} keys"
        print(f"{rank:<5} | {model:<26} | {passes_str:<10} | {tokens_str:<13} | {lat_str:<9} | {status}")

    print("=" * 85)


if __name__ == "__main__":
    main()
