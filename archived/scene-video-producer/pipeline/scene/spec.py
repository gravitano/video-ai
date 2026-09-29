"""scene.yaml — the single source of truth for one video.

Claude (the create-video skill) writes and revises this file; every CLI stage only reads it.
See examples/sdd-reels-45s/scene.yaml for a complete, commented example.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .util import SceneError

DEFAULT_THEME = {
    "bg": "#0A1428", "ink": "#EAF4F8", "accent": "#3FD8EA", "warm": "#FFB35C", "danger": "#FF5A68",
    "fonts": {"display": "Archivo Black", "mono": "JetBrains Mono", "caption": "Montserrat"},
}
DEFAULT_PROVIDERS = {
    "image": {"name": "codex"},
    "voice": {"name": "edge", "voice": "id-ID-ArdiNeural", "rate": "+12%"},
    "video": {"name": "minimax", "model": "MiniMax-H3", "resolution": "768P", "prompt_expansion": "disabled"},
    "music": {"name": "synth"},
}
SHOT_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class Spec:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.root = self.path.parent
        try:
            raw = yaml.safe_load(self.path.read_text()) or {}
        except yaml.YAMLError as e:
            raise SceneError(f"{self.path.name}: invalid YAML — {e}") from e
        self.raw = raw
        self.project = raw.get("project") or self.root.name
        self.brief = raw.get("brief", {})
        fmt = raw.get("format", {})
        self.width, self.height, self.fps = fmt.get("width", 1080), fmt.get("height", 1920), fmt.get("fps", 30)
        self.theme = {**DEFAULT_THEME, **raw.get("theme", {})}
        self.theme["fonts"] = {**DEFAULT_THEME["fonts"], **raw.get("theme", {}).get("fonts", {})}
        self.style = raw.get("style", {})
        self.persona = self._load_persona(raw.get("persona"))
        persona_voice = (self.persona or {}).get("voice", {})
        self.providers = {k: {**v, **(persona_voice if k == "voice" else {}), **raw.get("providers", {}).get(k, {})}
                          for k, v in DEFAULT_PROVIDERS.items()}
        self.budget = raw.get("budget", {})
        self.captions = {"zone": "bottom", "max_words": 4, **raw.get("captions", {})}
        self.audio = {"music_volume": 0.55, "carve": True, **raw.get("audio", {})}
        self.shots: list[dict] = raw.get("shots") or []
        self._validate()

    # ------------------------------------------------------------------ persona
    def _load_persona(self, ref) -> dict | None:
        """persona: <dir containing persona.yaml> | {inline fields}. Paths resolve relative to the persona's folder."""
        if not ref:
            return None
        if isinstance(ref, str):
            pdir = (self.root / ref).resolve()
            pfile = pdir / "persona.yaml" if pdir.is_dir() else pdir
            if not pfile.exists():
                raise SceneError(f"persona not found: {ref}")
            data = yaml.safe_load(pfile.read_text()) or {}
            pdir = pfile.parent
        else:
            data, pdir = dict(ref), self.root
        if not data.get("look"):
            raise SceneError("persona needs a 'look' description")
        data["dir"] = pdir
        data["sheet"] = (pdir / data["sheet"]).resolve() if data.get("sheet") else None
        data["refs"] = [(pdir / r).resolve() for r in data.get("refs", [])]
        for img in [data["sheet"], *data["refs"]]:
            if img and not img.exists():
                raise SceneError(f"persona image missing: {img}")
        return data

    def persona_images(self) -> list[Path]:
        """Character sheet first, then extra refs (max 9 — MiniMax's reference_image limit)."""
        if not self.persona:
            return []
        return [p for p in [self.persona["sheet"], *self.persona["refs"]] if p][:9]

    # ------------------------------------------------------------------ paths
    @property
    def assets(self) -> Path:
        return self.root / "assets"

    @property
    def video_dir(self) -> Path:
        return self.root / "video"

    @property
    def out_dir(self) -> Path:
        return self.root / "out"

    def shot(self, sid: str) -> dict:
        for s in self.shots:
            if s["id"] == sid:
                return s
        raise SceneError(f"unknown shot '{sid}' (have: {', '.join(s['id'] for s in self.shots)})")

    def select(self, ids: list[str] | None) -> list[dict]:
        return [self.shot(i) for i in ids] if ids else list(self.shots)

    # ------------------------------------------------------------------ theme
    def color(self, value: str | None, default: str = "ink") -> str:
        value = value or default
        return self.theme.get(value, value) if isinstance(value, str) else value

    # ------------------------------------------------------------------ checks
    def _validate(self) -> None:
        errs = []
        if not self.shots:
            errs.append("no shots defined")
        seen = set()
        for i, s in enumerate(self.shots):
            where = f"shots[{i}]"
            sid = s.get("id")
            if not sid or not SHOT_ID.match(str(sid)):
                errs.append(f"{where}: id must be lowercase letters/digits/_/- (got {sid!r})")
                continue
            if sid in seen:
                errs.append(f"{where}: duplicate id '{sid}'")
            seen.add(sid)
            for field in ("keyframe_prompt", "motion_prompt"):
                if not s.get(field):
                    errs.append(f"{sid}: missing {field}")
            if "duration" in s and not (isinstance(s["duration"], int) and 1 <= s["duration"] <= 60):
                errs.append(f"{sid}: duration must be an integer number of seconds")
        if errs:
            raise SceneError(f"{self.path.name} is invalid:\n  - " + "\n  - ".join(errs))


def load(path: str | Path | None = None) -> Spec:
    p = Path(path or "scene.yaml")
    if p.is_dir():
        p = p / "scene.yaml"
    if not p.exists():
        raise SceneError(f"{p} not found — run `scene init <dir>` or pass --spec")
    return Spec(p)
