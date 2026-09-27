"""Placeholder music bed synthesized locally (numpy): tense minor pads + pulse until `turn`, warm resolve after.

Deterministic (seeded) and license-free. Replace with a licensed track for publishing
(providers.music: {name: file, path: ...}).
"""
from __future__ import annotations

import wave
from pathlib import Path

from ..util import run

SR = 48000
TENSION = [[45, 57, 60, 64], [41, 57, 60, 65], [38, 57, 62, 65], [40, 56, 59, 64]]
RESOLVE = [[48, 60, 64, 67, 71], [43, 59, 62, 67, 71], [45, 60, 64, 69, 72], [41, 60, 65, 69, 72]]


def _hz(midi: float) -> float:
    return 440 * 2 ** ((midi - 69) / 12)


def render(dest: Path, total: float, turn: float | None = None, bpm: int = 100) -> None:
    import numpy as np

    t = np.arange(int(SR * total)) / SR
    turn = total * 0.45 if turn is None else max(1.0, min(turn, total - 1.0))

    def pad(freqs, a, b, amp):
        seg = (t >= a) & (t < b)
        y = np.zeros_like(t)
        for f in freqs:
            for det in (-0.12, 0.0, 0.12):
                fr = _hz(f + det)
                y += np.sin(2 * np.pi * fr * t) + 0.35 * np.sin(4 * np.pi * fr * t + 0.3) + 0.15 * np.sin(6 * np.pi * fr * t)
        env = np.clip(np.minimum((t - a) / 1.2, (b - t) / 1.2), 0, 1)
        return y * env * seg * amp / len(freqs)

    y = np.zeros_like(t)
    for chords, a, b, amp in ((TENSION, 0.0, turn + 0.3, 0.07), (RESOLVE, turn + 0.3, total, 0.08)):
        step = (b - a) / len(chords)
        for i, c in enumerate(chords):
            y += pad(c, a + i * step, a + (i + 1) * step, amp)
    beat = 60 / bpm
    ph = (t % beat) / beat
    kick = np.exp(-ph * 9) * np.sin(2 * np.pi * (45 + 60 * np.exp(-ph * 25)) * t)
    y += 0.22 * kick * np.clip(t / turn, 0.3, 1) * (t < turn + 0.3)
    after = (t >= turn + 1.0) & (t < total - 0.5)
    y += 0.16 * kick * after
    rng = np.random.default_rng(7)
    hat = np.exp(-(((t + beat / 2) % beat) / beat) * 60) * rng.standard_normal(len(t))
    y += 0.03 * hat * after
    y *= 1 - 0.15 * (t < turn + 0.3) * (0.5 + 0.5 * np.sin(2 * np.pi * 4 * t))
    y *= np.clip(t / 1.0, 0, 1) * np.clip((total - t) / 1.5, 0, 1)
    d = int(0.012 * SR)
    st = np.stack([y, np.concatenate([np.zeros(d), y[:-d]])], 1)
    st /= np.abs(st).max() * 1.12

    dest.parent.mkdir(parents=True, exist_ok=True)
    raw = dest.with_suffix(".raw.wav")
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
         "aecho=0.8:0.6:60|120:0.25|0.15,lowpass=f=6000,loudnorm=I=-20:TP=-2", "-ar", "48000", str(dest)])
    raw.unlink()
