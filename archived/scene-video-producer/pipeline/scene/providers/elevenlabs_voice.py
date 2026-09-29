"""Voice-over through ElevenLabs, with character-level timestamps turned into word timings.

  TTS:     POST /v1/text-to-speech/{voice_id}/with-timestamps   → audio_base64 + alignment
  Library: GET  /v1/shared-voices?language=id&gender=female&search=…   (filters need an API key)
           POST /v1/voices/add/{public_owner_id}/{voice_id}      → add a Voice Library voice to your account

Auth: ELEVENLABS_API_KEY env var, or the file named by `key_file` (default ~/.elevenlabs_key). Never logged.
Billing: ElevenLabs credits per character of text (cached by the voice stage, so unchanged lines are free).
"""
from __future__ import annotations

import base64
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..util import SceneError, run

API = "https://api.elevenlabs.io"
LEAD, TAIL = 0.05, 0.25


def api_key(cfg: dict | None = None) -> str:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        kf = Path((cfg or {}).get("key_file", "~/.elevenlabs_key")).expanduser()
        if kf.exists():
            key = kf.read_text().strip()
    if not key:
        raise SceneError("ElevenLabs API key missing: set ELEVENLABS_API_KEY or write it to ~/.elevenlabs_key (chmod 600)")
    return key


def _request(method: str, path: str, key: str, body: dict | None = None, query: dict | None = None) -> dict:
    url = API + path + ("?" + urllib.parse.urlencode(query, doseq=True) if query else "")
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        raise SceneError(f"elevenlabs {method} {path} → HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise SceneError(f"elevenlabs {method} {path} → {e.reason}") from e


def search_shared(key: str, *, language: str | None = None, gender: str | None = None, age: str | None = None,
                  search: str | None = None, descriptives: list[str] | None = None, use_cases: list[str] | None = None,
                  sort: str = "usage_character_count_1y", page_size: int = 30) -> list[dict]:
    q = {k: v for k, v in {"language": language, "gender": gender, "age": age, "search": search, "descriptives": descriptives,
                           "use_cases": use_cases, "sort": sort, "page_size": page_size}.items() if v}
    return _request("GET", "/v1/shared-voices", key, query=q).get("voices", [])


def add_shared(key: str, public_owner_id: str, voice_id: str, name: str) -> str:
    return _request("POST", f"/v1/voices/add/{public_owner_id}/{voice_id}", key, body={"new_name": name})["voice_id"]


def words_from_alignment(al: dict) -> list[dict]:
    """Group character timings into words (split on whitespace)."""
    words, cur, start, end = [], "", None, None
    for ch, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if ch.isspace():
            if cur:
                words.append({"text": cur, "s": start, "e": end})
            cur, start = "", None
            continue
        if not cur:
            start = s
        cur += ch
        end = e
    if cur:
        words.append({"text": cur, "s": start, "e": end})
    return words


class ElevenLabsVoice:
    name = "elevenlabs"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        if not cfg.get("voice_id"):
            raise SceneError("elevenlabs voice needs voice_id (find one with `scene voices search`)")
        self.voice_id = cfg["voice_id"]
        self.model = cfg.get("model", "eleven_multilingual_v2")
        self.language = cfg.get("language_code")
        self.settings = {k: cfg[k] for k in ("stability", "similarity_boost", "style", "speed", "use_speaker_boost") if k in cfg}
        self.af = cfg.get("af")

    def params(self) -> dict:
        return {"provider": self.name, "voice_id": self.voice_id, "model": self.model, "language": self.language,
                "settings": self.settings, "af": self.af}

    def synthesize(self, text: str, dest_wav: Path) -> dict:
        body = {"text": text, "model_id": self.model}
        if self.language:
            body["language_code"] = self.language
        if self.settings:
            body["voice_settings"] = self.settings
        res = _request("POST", f"/v1/text-to-speech/{self.voice_id}/with-timestamps", api_key(self.cfg), body=body,
                       query={"output_format": "mp3_44100_128"})
        al = res.get("alignment") or res.get("normalized_alignment")
        if not al or not res.get("audio_base64"):
            raise SceneError("elevenlabs: response without audio/alignment")
        words = words_from_alignment(al)
        if not words:
            raise SceneError(f"elevenlabs returned no word timings for: {text[:60]}")
        lead = max(0.0, words[0]["s"] - LEAD)
        end = words[-1]["e"] + TAIL
        dest_wav.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".mp3") as mp3:
            Path(mp3.name).write_bytes(base64.b64decode(res["audio_base64"]))
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{lead:.3f}", "-to", f"{end:.3f}", "-i", mp3.name,
                 *(["-af", self.af] if self.af else []), "-ar", "48000", "-ac", "2", str(dest_wav)])
        return {"speech": round(end - lead, 3),
                "words": [{"text": w["text"], "s": round(w["s"] - lead, 3), "e": round(w["e"] - lead, 3)} for w in words]}
