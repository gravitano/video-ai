"""Keyframe images through the Codex CLI's image generation tool (ChatGPT subscription).

The approved reference frame is attached to every shot so face, outfit, room and palette stay consistent.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from ..util import SceneError, require, run


class CodexImage:
    name = "codex"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        require("codex")

    def generate(self, prompt: str, dest: Path, reference=None) -> None:
        refs = [r for r in (reference if isinstance(reference, (list, tuple)) else [reference]) if r]
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="scene-codex-") as tmp:
            fname = "out.png"
            keep = ("The attached image(s) are approved references (a character sheet and/or a scene reference): keep the SAME "
                    "character design — face, hair, outfit, colors, proportions — and the same environment, lighting palette and "
                    "rendering style. " if refs else "")
            instr = (f"Use your image generation tool to create ONE image, portrait/vertical 9:16 (e.g. 1024x1536). {keep}"
                     f"Save the generated PNG into the current directory as {fname} (copy it from where the tool "
                     f"stores it). Write no other files. Prompt:\n\n{prompt.strip()}")
            cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write", "-C", tmp, instr]
            if refs:
                cmd += ["-i", *map(str, refs)]  # -i is variadic: it must come after the prompt
            run(cmd, capture=True)
            out = Path(tmp) / fname
            if not out.exists():
                raise SceneError(f"codex did not produce an image for {dest.name}")
            shutil.move(str(out), dest)
