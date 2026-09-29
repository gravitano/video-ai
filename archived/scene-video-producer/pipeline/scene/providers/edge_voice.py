"""Voice-over through Microsoft Edge neural TTS (edge-tts), with word-boundary timestamps.

Each line is trimmed to [first word - 50ms, last word + 250ms] so shot timing measures speech, not padding.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from ..util import run

LEAD, TAIL = 0.05, 0.25


class EdgeVoice:
    name = "edge"

    def __init__(self, cfg: dict):
        self.voice = cfg.get("voice", "id-ID-ArdiNeural")
        self.rate = cfg.get("rate", "+0%")
        self.pitch = cfg.get("pitch", "+0Hz")
        self.af = cfg.get("af")  # optional ffmpeg audio filter, e.g. a robot chorus for a mascot

    def params(self) -> dict:
        return {"provider": self.name, "voice": self.voice, "rate": self.rate, "pitch": self.pitch, "af": self.af}

    async def _stream(self, text: str):
        import edge_tts

        comm = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch, boundary="WordBoundary")
        audio, words = b"", []
        async for ch in comm.stream():
            if ch["type"] == "audio":
                audio += ch["data"]
            elif ch["type"] == "WordBoundary":
                words.append({"text": ch["text"], "s": ch["offset"] / 1e7, "d": ch["duration"] / 1e7})
        return audio, words

    def synthesize(self, text: str, dest_wav: Path) -> dict:
        """Write a trimmed 48 kHz stereo WAV; return {speech, words:[{text,s,e}]} relative to the WAV start."""
        audio, words = asyncio.run(self._stream(text))
        if not words:
            raise RuntimeError(f"edge-tts returned no word timings for: {text[:60]}")
        lead = max(0.0, words[0]["s"] - LEAD)
        end = words[-1]["s"] + words[-1]["d"] + TAIL
        dest_wav.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".mp3") as mp3:
            Path(mp3.name).write_bytes(audio)
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{lead:.3f}", "-to", f"{end:.3f}", "-i", mp3.name,
                 *(["-af", self.af] if self.af else []), "-ar", "48000", "-ac", "2", str(dest_wav)])
        return {
            "speech": round(end - lead, 3),
            "words": [{"text": w["text"], "s": round(w["s"] - lead, 3), "e": round(w["s"] - lead + w["d"], 3)} for w in words],
        }
