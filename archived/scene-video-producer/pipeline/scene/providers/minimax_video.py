"""MiniMax video generation (API v2, MiniMax-H3 / MiniMax-H3-Max) — image-to-video from a first frame.

Docs: https://platform.minimax.io/docs/api-reference/video-generation-v2-create
  POST {base}/v2/video_generation                      -> {"task_id": ...}
  GET  {base}/v2/query/video_generation/{task_id}      -> {"status": ..., "content": {"url": ...}}

Auth: MINIMAX_API_KEY env var, or the file named by `key_file` (default ~/.minimax_key).
The key is never logged.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from ..util import SceneError

# USD per generated second (platform.minimax.io pay-as-you-go, checked 2026-09-25). Override via providers.video.price_per_second.
PRICES = {
    ("MiniMax-H3", "768P"): 0.08,
    ("MiniMax-H3", "2K"): 0.13,
    ("MiniMax-H3-Max", "480P"): 0.05,
    ("MiniMax-H3-Max", "768P"): 0.08,
}
DURATION_LIMITS = {"MiniMax-H3": (4, 15), "MiniMax-H3-Max": (5, 15)}
SUCCESS = {"succeeded", "success", "completed"}
FAILED = {"failed", "fail", "cancelled", "canceled", "error"}


class MiniMaxVideo:
    name = "minimax"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.model = cfg.get("model", "MiniMax-H3")
        self.resolution = cfg.get("resolution", "768P")
        self.base = cfg.get("base_url", "https://api.minimax.io").rstrip("/")
        self.expansion = cfg.get("prompt_expansion", "disabled")
        self.poll_every = float(cfg.get("poll_seconds", 10))
        self.timeout = float(cfg.get("timeout_seconds", 1800))
        if (self.model, self.resolution) not in PRICES and "price_per_second" not in cfg:
            raise SceneError(f"minimax: unsupported model/resolution {self.model} {self.resolution} "
                             f"(known: {', '.join(f'{m} {r}' for m, r in PRICES)})")

    # ------------------------------------------------------------ pricing / limits
    def price_per_second(self) -> float:
        return float(self.cfg.get("price_per_second", PRICES.get((self.model, self.resolution), 0.0)))

    def limits(self) -> tuple[int, int]:
        return DURATION_LIMITS.get(self.model, (4, 15))

    def fit_duration(self, seconds: int) -> int:
        lo, hi = self.limits()
        return max(lo, min(hi, int(seconds)))

    def estimate(self, seconds: int) -> float:
        return round(self.fit_duration(seconds) * self.price_per_second(), 4)

    # ------------------------------------------------------------ http
    def _key(self) -> str:
        key = os.environ.get("MINIMAX_API_KEY")
        if not key:
            kf = Path(self.cfg.get("key_file", "~/.minimax_key")).expanduser()
            if kf.exists():
                key = kf.read_text().strip()
        if not key:
            raise SceneError("MiniMax API key missing: set MINIMAX_API_KEY or write it to ~/.minimax_key (chmod 600)")
        return key

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method, headers={
            "Authorization": f"Bearer {self._key()}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                payload = json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise SceneError(f"minimax {method} {path} → HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            raise SceneError(f"minimax {method} {path} → {e.reason}") from e
        base = payload.get("base_resp") or {}
        if base.get("status_code") not in (None, 0):
            raise SceneError(f"minimax {path}: {base.get('status_code')} {base.get('status_msg')}")
        if isinstance(payload.get("error"), dict):
            raise SceneError(f"minimax {path}: {payload['error'].get('message')}")
        return payload

    # ------------------------------------------------------------ api
    @staticmethod
    def data_uri(image: Path) -> str:
        mime = mimetypes.guess_type(image.name)[0] or "image/png"
        return f"data:{mime};base64," + base64.b64encode(image.read_bytes()).decode()

    def build_body(self, prompt: str, first_frame: Path, seconds: int, last_frame: Path | None = None,
                   references: list[Path] | None = None) -> dict:
        content = [{"type": "text", "text": prompt},
                   {"type": "image_url", "image_url": {"url": self.data_uri(first_frame)}, "role": "first_frame"}]
        if last_frame:
            content.append({"type": "image_url", "image_url": {"url": self.data_uri(last_frame)}, "role": "last_frame"})
        for ref in (references or [])[:9]:  # e.g. the persona character sheet — keeps identity through motion
            content.append({"type": "image_url", "image_url": {"url": self.data_uri(ref)}, "role": "reference_image"})
        return {"model": self.model, "content": content, "duration": self.fit_duration(seconds),
                "resolution": self.resolution, "extra": {"prompt_expansion_mode": self.expansion}}

    def submit(self, prompt: str, first_frame: Path, seconds: int, last_frame: Path | None = None,
               references: list[Path] | None = None) -> str:
        payload = self._request("POST", "/v2/video_generation", self.build_body(prompt, first_frame, seconds, last_frame, references))
        task_id = payload.get("task_id") or (payload.get("data") or {}).get("task_id") or payload.get("id")
        if not task_id:
            raise SceneError(f"minimax: no task_id in response keys {sorted(payload)}")
        return str(task_id)

    def poll(self, task_id: str) -> tuple[str, str | None, dict]:
        """Return (state, url, raw) where state is 'running' | 'done' | 'failed'."""
        p = self._request("GET", f"/v2/query/video_generation/{task_id}")
        status = str(p.get("status") or (p.get("data") or {}).get("status") or "").lower()
        content = p.get("content") or (p.get("data") or {}).get("content") or {}
        url = content.get("url") if isinstance(content, dict) else None
        if status in SUCCESS:
            if not url:
                raise SceneError(f"minimax: task {task_id} succeeded without content.url")
            return "done", url, p
        if status in FAILED:
            return "failed", None, p
        return "running", None, p

    def wait(self, task_id: str, on_tick=None) -> str:
        start = time.time()
        while True:
            state, url, raw = self.poll(task_id)
            if state == "done":
                return url
            if state == "failed":
                reason = raw.get("error") or raw.get("status_msg") or raw.get("status")
                raise SceneError(f"minimax: task {task_id} failed: {reason}")
            if time.time() - start > self.timeout:
                raise SceneError(f"minimax: task {task_id} still running after {int(self.timeout)}s — rerun to resume")
            if on_tick:
                on_tick(raw)
            time.sleep(self.poll_every)

    @staticmethod
    def download(url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        tmp.replace(dest)
