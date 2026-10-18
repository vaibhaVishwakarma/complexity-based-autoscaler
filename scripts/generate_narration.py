#!/usr/bin/env python3
"""
scripts/generate_narration.py
Synthesizes professional Jenny neural voice narration for CGDA Explainer Video using edge-tts.
Measures exact audio durations and concatenates with precise scene padding for video synchronization.
"""

import asyncio
import json
import os
import subprocess
import edge_tts

VOICE = "en-US-JennyNeural"
RATE = "+15%"
AUDIO_DIR = "media/narration"
os.makedirs(AUDIO_DIR, exist_ok=True)

SCRIPTS = {
    "scene1": "In cascaded edge-cloud inference, standard autoscalers face a critical blind spot: Complexity Blindness. When query difficulty shifts, total network ingress remains completely flat, yet edge triage collapses—suddenly tripling cloud GPU demand and overwhelming buffers.",
    "scene2": "To solve this, we instrument conformal prediction sets. Confident singletons yield over ninety-seven percent selective accuracy for instant, zero-cost edge resolution. But when queries become ambiguous, we must alert cloud GPU pools before SLA budgets expire.",
    "scene3": "CGDA converts edge acceptance dynamics into a real-time derivative: delta-p of t. When this velocity plummets, our fast loop immediately issues feed-forward scale-out commands—gaining up to ten seconds of preemption over container boot lag.",
    "scene4": "Tracking active workers and tail latency: CGDA preempts on the derivative, bringing cloud capacity online before the fifteen-second deadline and keeping P99 latency flat at under six seconds. In contrast, reactive scalers wait for queue backpressure, triggering severe latency spikes up to twenty-eight seconds.",
    "scene5a": "Across nearly twenty thousand real-world requests, CGDA guarantees zero deadline misses up to ten seconds of boot delay, and slashes misses by eighty-three percent at twenty seconds and thirty-nine percent at fifty seconds—delivering maximum physical damage mitigation.",
    "scene5b": "Because our controller operates purely on dimensionless scalar telemetry, this framework transfers seamlessly beyond vision—to Small Language Model cascades and Vision-Language cascades—vital for multi-minute foundation model cold starts.",
    "scene6_outro": "Conformal-Gated Dual-Horizon Autoscaler: eliminating complexity blindness in the edge-cloud continuum."
}

async def synthesize_all():
    durations = {}
    for key, text in SCRIPTS.items():
        mp3_path = os.path.join(AUDIO_DIR, f"{key}.mp3")
        communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
        await communicate.save(mp3_path)
        
        # Get duration using ffmpeg
        cmd = ["./.venv/bin/ffmpeg", "-i", mp3_path]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = dur_str.split(":")
                dur_sec = float(h)*3600 + float(m)*60 + float(s)
                durations[key] = round(dur_sec, 2)
                print(f"[{key}] Duration: {dur_sec:.2f}s | File: {mp3_path}")
                break

    json_path = os.path.join(AUDIO_DIR, "durations.json")
    with open(json_path, "w") as f:
        json.dump(durations, f, indent=2)

    print("\n--- Audio Durations Summary (rate=+15%) ---")
    total_audio = sum(durations.values())
    for k, v in durations.items():
        print(f"  {k}: {v:.2f}s")
    print(f"Total Speech Duration: {total_audio:.2f}s")
    print(f"Saved manifest to {json_path}")

if __name__ == "__main__":
    asyncio.run(synthesize_all())
