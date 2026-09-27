"""Small shared helpers: hashing, subprocess, media probing, skill lookup."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


class SceneError(RuntimeError):
    """A user-facing error: printed without a traceback by the CLI."""


def content_key(*parts) -> str:
    """Stable short hash of JSON-able parts (and raw bytes)."""
    h = hashlib.sha256()
    for p in parts:
        if isinstance(p, bytes):
            h.update(p)
        else:
            h.update(json.dumps(p, sort_keys=True, default=str).encode())
        h.update(b"\0")
    return h.hexdigest()[:16]


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run(cmd: list[str], cwd: Path | None = None, capture: bool = False, check: bool = True, **kw):
    try:
        return subprocess.run(cmd, cwd=cwd, check=check, text=True,
                              capture_output=capture, stdin=subprocess.DEVNULL, **kw)
    except FileNotFoundError as e:
        raise SceneError(f"command not found: {cmd[0]}") from e
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or "").strip()[-800:] if capture else ""
        raise SceneError(f"command failed ({e.returncode}): {' '.join(cmd[:3])} …\n{detail}") from e


def require(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise SceneError(f"'{tool}' is required but not on PATH")
    return path


def media_duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
              capture=True).stdout.strip()
    return round(float(out), 3)


def skill_roots() -> list[Path]:
    roots = []
    if os.environ.get("SCENE_SKILLS_DIR"):
        roots.append(Path(os.environ["SCENE_SKILLS_DIR"]).expanduser())
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        roots.append(Path(os.environ["CLAUDE_CONFIG_DIR"]).expanduser() / "skills")
    home = Path.home()
    roots += [home / ".claude-hsr" / "skills", home / ".claude" / "skills", home / ".agents" / "skills"]
    return roots


def find_skill_file(rel: str) -> Path | None:
    """Locate a file shipped by an installed HyperFrames skill (e.g. bundled SFX, carve.mjs)."""
    for root in skill_roots():
        p = root / rel
        if p.exists():
            return p
    return None


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)
