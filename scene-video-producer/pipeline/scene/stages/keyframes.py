"""E stage: one approved keyframe per shot, anchored to a reference frame for identity continuity.

Cache key = prompt + reference image hash, so regenerating the reference invalidates every shot,
and editing one shot's prompt regenerates only that shot.
"""
from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import providers
from ..util import SceneError, content_key, file_hash, log

REF_ID = "00_reference"
EXTS = (".png", ".jpg", ".jpeg", ".webp")


def persona_line(spec) -> str:
    p = spec.persona
    if not p:
        return ""
    return (f"Character: {p.get('name', 'the persona')} — must match the attached character sheet exactly "
            f"(face, hair, outfit, colors, proportions). {p['look'].strip()}")


def shot_prompt(spec, shot) -> str:
    parts = [shot["keyframe_prompt"].strip(), persona_line(spec), (spec.style.get("consistency") or "").strip()]
    return "\n\n".join(x for x in parts if x)


def persona_hashes(spec) -> list[str]:
    return [file_hash(p) for p in spec.persona_images()]


def ref_key(spec) -> str | None:
    rp = spec.style.get("reference_prompt")
    return content_key("ref", rp, persona_line(spec), persona_hashes(spec)) if rp else None


def shot_key(spec, state, shot) -> str:
    ref = state.get("keyframes", REF_ID)
    return content_key("kf", shot_prompt(spec, shot), ref["hash"] if ref else None, persona_hashes(spec))


def path_of(spec, sid: str) -> Path:
    return spec.assets / "keyframes" / f"{sid}.png"


def current(spec, state, shot) -> Path | None:
    """The keyframe file if it is fresh for the current spec, else None."""
    e = state.get("keyframes", shot["id"])
    p = spec.root / e["file"] if e else None
    return p if e and p.exists() and e["key"] == shot_key(spec, state, shot) else None


def run(spec, state, shots=None, force=False, jobs=4) -> None:
    prov = providers.image(spec.providers["image"])
    kdir = spec.assets / "keyframes"
    ref = state.get("keyframes", REF_ID)
    rk = ref_key(spec)
    ref_path = path_of(spec, REF_ID)
    if rk and (force or not ref or ref["key"] != rk or not ref_path.exists()):
        if prov is None:
            raise SceneError("image provider is 'manual': add the reference with `scene adopt keyframes <dir>`")
        log("  keyframe 00_reference: generating")
        prompt = "\n\n".join(x for x in [spec.style["reference_prompt"].strip(), persona_line(spec)] if x)
        prov.generate(prompt, ref_path, spec.persona_images())
        state.put("keyframes", REF_ID, {"key": rk, "file": str(ref_path.relative_to(spec.root)), "hash": file_hash(ref_path), "source": prov.name})
    todo = [s for s in spec.select(shots) if force or not current(spec, state, s)]
    for s in spec.select(shots):
        if s not in todo:
            log(f"  keyframe {s['id']}: cached")
    if not todo:
        return
    if prov is None:
        raise SceneError("missing keyframes for: " + ", ".join(s["id"] for s in todo) + " — add them with `scene adopt keyframes <dir>`")
    reference = spec.persona_images() + ([ref_path] if ref_path.exists() else [])

    def one(s):
        dest = path_of(spec, s["id"])
        prov.generate(shot_prompt(spec, s), dest, reference)
        state.put("keyframes", s["id"], {"key": shot_key(spec, state, s), "file": str(dest.relative_to(spec.root)),
                                         "hash": file_hash(dest), "source": prov.name})
        return s["id"]

    log(f"  generating {len(todo)} keyframe(s) with {prov.name} ({jobs} parallel)…")
    with ThreadPoolExecutor(jobs) as ex:
        for sid in ex.map(one, todo):
            log(f"  keyframe {sid}: done")


def adopt(spec, state, src: Path) -> None:
    """Register externally made images (e.g. from ChatGPT web) as the current keyframes.

    Files are matched by shot id prefix: 01_hook.png, 01_hook-v2.jpg … and 00_reference.* for the reference.
    """
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)
    kdir = spec.assets / "keyframes"
    kdir.mkdir(parents=True, exist_ok=True)

    def find(sid):
        return next((p for p in files if p.stem == sid or p.stem.startswith(sid + "-") or p.stem.startswith(sid + "_v")), None)

    ref = find(REF_ID)
    if ref:
        dest = path_of(spec, REF_ID)
        if ref.resolve() != dest.resolve():
            shutil.copyfile(ref, dest)
        state.put("keyframes", REF_ID, {"key": ref_key(spec), "file": str(dest.relative_to(spec.root)), "hash": file_hash(dest), "source": "adopted"})
        log(f"  adopted {ref.name} → reference")
    n = 0
    for s in spec.shots:
        p = find(s["id"])
        if not p:
            continue
        dest = path_of(spec, s["id"])
        if p.suffix.lower() != ".png":
            from ..util import run as sh
            sh(["ffmpeg", "-y", "-v", "error", "-i", str(p), str(dest)])
        elif p.resolve() != dest.resolve():
            shutil.copyfile(p, dest)
        state.put("keyframes", s["id"], {"key": shot_key(spec, state, s), "file": str(dest.relative_to(spec.root)),
                                         "hash": file_hash(dest), "source": "adopted"})
        n += 1
        log(f"  adopted {p.name} → {s['id']}")
    missing = [s["id"] for s in spec.shots if not state.get("keyframes", s["id"])]
    log(f"  {n} keyframe(s) adopted" + (f"; still missing: {', '.join(missing)}" if missing else ""))
