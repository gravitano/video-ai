"""Provider registry. Each kind has one interface so providers can be swapped in scene.yaml."""
from __future__ import annotations

from ..util import SceneError


def video(cfg: dict):
    name = cfg.get("name")
    if name == "minimax":
        from .minimax_video import MiniMaxVideo
        return MiniMaxVideo(cfg)
    if name == "mock":
        from .mock_video import MockVideo
        return MockVideo(cfg)
    raise SceneError(f"unknown video provider '{name}' (available: minimax, mock)")


def image(cfg: dict):
    name = cfg.get("name")
    if name == "codex":
        from .codex_image import CodexImage
        return CodexImage(cfg)
    if name == "manual":
        return None  # images are supplied with `scene adopt keyframes <dir>`
    raise SceneError(f"unknown image provider '{name}' (available: codex, manual)")


def voice(cfg: dict):
    name = cfg.get("name")
    if name == "edge":
        from .edge_voice import EdgeVoice
        return EdgeVoice(cfg)
    if name == "elevenlabs":
        from .elevenlabs_voice import ElevenLabsVoice
        return ElevenLabsVoice(cfg)
    raise SceneError(f"unknown voice provider '{name}' (available: edge, elevenlabs)")
