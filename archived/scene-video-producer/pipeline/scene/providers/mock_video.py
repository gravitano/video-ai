"""Offline stand-in for a paid image-to-video provider.

Renders a slow push-in from the keyframe with ffmpeg, through the same submit/poll/download
interface as MiniMaxVideo, so the whole pipeline (cache, resume, review, build) can be tested for $0.
"""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

from ..util import run


class MockVideo:
    name = "mock"
    model = "mock-kenburns"
    resolution = "768P"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.tmp = Path(tempfile.gettempdir()) / "scene-mock-video"
        self.tmp.mkdir(exist_ok=True)

    def price_per_second(self) -> float:
        return 0.0

    def limits(self) -> tuple[int, int]:
        return (1, 60)

    def fit_duration(self, seconds: int) -> int:
        return max(1, int(seconds))

    def estimate(self, seconds: int) -> float:
        return 0.0

    def submit(self, prompt: str, first_frame: Path, seconds: int, last_frame: Path | None = None, references=None) -> str:
        task = hashlib.sha1(f"{first_frame}{seconds}{prompt}".encode()).hexdigest()[:12]
        out = self.tmp / f"{task}.mp4"
        frames = int(seconds * 30)
        vf = (f"scale=864:1536:force_original_aspect_ratio=increase,crop=864:1536,"
              f"zoompan=z='1+0.10*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=864x1536:fps=30")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(first_frame), "-vf", vf, "-t", str(seconds),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(out)])
        return task

    def poll(self, task_id: str):
        return "done", str(self.tmp / f"{task_id}.mp4"), {"status": "succeeded"}

    def wait(self, task_id: str, on_tick=None) -> str:
        return self.poll(task_id)[1]

    @staticmethod
    def download(url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(url, dest)
