"""E (edit & export) stage: assemble a HyperFrames project from the spec, then check and render it.

Picture per shot = the selected MiniMax clip when one is current, otherwise the keyframe with a virtual
camera move — so the video is always renderable, and upgrades shot by shot as clips arrive.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .. import compose
from ..providers import synth_music
from ..timing import plan, resolve_at, total
from ..util import SceneError, content_key, find_skill_file, log, media_duration, run
from . import clips, keyframes

SFX_REL = "media-use/audio/assets/sfx"
CARVE_REL = "hyperframes-audio/scripts/carve.mjs"


# ------------------------------------------------------------------ hyperframes cli
def hf_version(spec) -> str:
    pkg = spec.video_dir / "package.json"
    if pkg.exists():
        m = re.search(r"hyperframes@([\w.\-]+)", pkg.read_text())
        if m:
            return m.group(1)
    return "latest"


def hf(spec, *args, capture=False, check=True):
    return run(["npx", "--yes", f"hyperframes@{hf_version(spec)}", *args], cwd=spec.video_dir, capture=capture, check=check)


def ensure_project(spec) -> None:
    if (spec.video_dir / "hyperframes.json").exists():
        return
    if spec.video_dir.exists() and any(spec.video_dir.iterdir()):
        raise SceneError(f"{spec.video_dir} exists but is not a HyperFrames project")
    log("  initializing HyperFrames project in video/ …")
    run(["npx", "--yes", "hyperframes@latest", "init", spec.video_dir.name, "--non-interactive", "--example=blank"],
        cwd=spec.root, capture=True)


# ------------------------------------------------------------------ assets
def _sync(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_size != src.stat().st_size or dest.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dest)


def _fit_clip(src: Path, dest: Path, seconds: float) -> None:
    """Copy a clip; if it is shorter than its shot, hold the last frame so the shot never goes blank."""
    have = media_duration(src)
    if have + 0.05 >= seconds:
        _sync(src, dest)
        return
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime and media_duration(dest) + 0.05 >= seconds:
        return
    log(f"  {dest.stem}: clip is {have:.1f}s < shot {seconds}s — holding the last frame")
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", f"tpad=stop_mode=clone:stop_duration={seconds - have + 0.2:.2f}",
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "16", str(dest)])


def _music(spec, timeline) -> Path | None:
    cfg = spec.providers["music"]
    name = cfg.get("name", "synth")
    if name == "none":
        return None
    if name == "file":
        p = (spec.root / cfg["path"]).resolve()
        if not p.exists():
            raise SceneError(f"music file not found: {cfg['path']}")
        return p
    if name != "synth":
        raise SceneError(f"unknown music provider '{name}' (available: synth, file, none)")
    turn = None
    if cfg.get("turn_at_shot"):
        turn = next(p["start"] for p in timeline if p["id"] == cfg["turn_at_shot"])
    dest = spec.assets / "music" / "bgm.wav"
    key = content_key("music-synth", total(timeline), turn)
    stamp = dest.with_suffix(".key")
    if not dest.exists() or not stamp.exists() or stamp.read_text() != key:
        log("  music: synthesizing placeholder bed")
        synth_music.render(dest, float(total(timeline)), turn)
        stamp.write_text(key)
    return dest


def _sfx_dir(spec) -> Path | None:
    if spec.audio.get("sfx_dir"):
        return (spec.root / spec.audio["sfx_dir"]).expanduser()
    return find_skill_file(SFX_REL)


# ------------------------------------------------------------------ build
def build(spec, state) -> None:
    timeline = plan(spec, state)
    unmeasured = [p["id"] for s, p in zip(spec.shots, timeline) if s.get("vo") and not p["measured"]]
    if unmeasured:
        raise SceneError(f"run `scene voice` first (no VO for: {', '.join(unmeasured)})")
    ensure_project(spec)
    va = spec.video_dir / "assets"
    comp_dir = spec.video_dir / "compositions"
    comp_dir.mkdir(exist_ok=True)

    for s in spec.shots:  # image overlays: copy the file into the project and point the overlay at it
        for ov in s.get("overlays", []):
            if ov.get("type") == "image":
                src = (spec.root / ov["src"]).resolve()
                if not src.exists():
                    raise SceneError(f"{s['id']}: image not found: {ov['src']}")
                _sync(src, va / "images" / src.name)
                ov["_src"] = f"assets/images/{src.name}"

    used_clips = 0
    for s, p in zip(spec.shots, timeline):
        clip = clips.selected_clip(spec, state, s)
        if clip:
            dest = va / "clips" / f"{s['id']}.mp4"
            _fit_clip(clip, dest, p["dur"])
            plate = {"kind": "video", "src": f"assets/clips/{s['id']}.mp4"}
            used_clips += 1
        else:
            kf = keyframes.current(spec, state, s)
            if not kf:
                raise SceneError(f"{s['id']}: no keyframe — run `scene keyframes`")
            _sync(kf, va / "keyframes" / f"{s['id']}.png")
            plate = {"kind": "image", "src": f"assets/keyframes/{s['id']}.png"}
        sid = f"s-{s['id']}".replace("_", "-")
        (comp_dir / f"{sid}.html").write_text(compose.scene_html(spec, s, p, plate))
    keep = {f"s-{s['id']}".replace("_", "-") + ".html" for s in spec.shots} | {"captions.html"}
    for old in comp_dir.glob("s-*.html"):
        if old.name not in keep:
            old.unlink()
    (comp_dir / "captions.html").write_text(compose.captions_html(spec, timeline))

    audio = {"music": None, "voice": [], "sfx": []}
    music = _music(spec, timeline)
    if music:
        _sync(music, va / "music" / music.name)
        audio["music"] = f"assets/music/{music.name}"
    for s, p in zip(spec.shots, timeline):
        v = state.get("voice", s["id"])
        if not v:
            continue
        src = spec.root / v["file"]
        _sync(src, va / "voice" / src.name)
        audio["voice"].append({"id": f"vo-{s['id']}".replace("_", "-"), "src": f"assets/voice/{src.name}",
                               "start": round(p["start"] + p["vo_offset"], 3), "dur": media_duration(src)})
    sfx_dir, n = _sfx_dir(spec), 0
    for s, p in zip(spec.shots, timeline):
        for fx in s.get("sfx", []):
            src = (spec.root / fx["file"]) if fx.get("file") else (sfx_dir / f"{fx['name']}.mp3" if sfx_dir else None)
            if not src or not src.exists():
                raise SceneError(f"{s['id']}: sound '{fx.get('file') or fx.get('name')}' not found"
                                 + ("" if sfx_dir else " (no bundled SFX dir: install the media-use skill or set audio.sfx_dir)"))
            _sync(src, va / "sfx" / src.name)
            start = round(p["start"] + resolve_at(fx.get("at"), p), 3)
            length = media_duration(src) - float(fx.get("media_start", 0))
            dur = round(min(fx.get("dur", length), length, total(timeline) - start), 3)
            audio["sfx"].append({"id": f"sfx-{n:02d}", "src": f"assets/sfx/{src.name}", "start": start, "dur": dur,
                                 "vol": fx.get("vol", 0.5), "media_start": fx.get("media_start")})
            n += 1

    (spec.video_dir / "index.html").write_text(compose.index_html(spec, timeline, audio))
    (spec.root / ".scene" / "timeline.json").write_text(json.dumps(timeline, indent=1, ensure_ascii=False))
    if music and spec.audio.get("carve", True) and audio["voice"]:
        _carve(spec, [v["id"] for v in audio["voice"]])
    log(f"  built {len(timeline)} shots ({used_clips} video clips, {len(timeline) - used_clips} keyframe stills), "
        f"{total(timeline)}s, {len(audio['sfx'])} sfx")
    out = hf(spec, "lint", capture=True, check=False).stdout
    log("  lint: " + (out.strip().splitlines()[-1] if out.strip() else "ok"))


def _carve(spec, voices: list[str]) -> None:
    carve = find_skill_file(CARVE_REL)
    if not carve:
        log("  ⚠ music carve skipped: hyperframes-audio skill not installed")
        return
    core = spec.video_dir / "node_modules" / "@hyperframes" / "core"
    if not core.exists():
        log("  installing @hyperframes/core for the music carve …")
        run(["npm", "i", "-D", f"@hyperframes/core@{hf_version(spec)}", "--silent"], cwd=spec.video_dir, capture=True)
    args = ["node", str(carve), "--comp", "index.html", "--bed", "bgm"]
    for v in voices:
        args += ["--voice", v]
    run(args, cwd=spec.video_dir, capture=True)
    log("  music carved under the voice-over")


def check(spec) -> bool:
    res = hf(spec, "check", capture=True, check=False)
    tail = [l for l in (res.stdout + res.stderr).splitlines() if l.strip() and not l.startswith("[")]
    for line in tail[-12:]:
        log("  " + line)
    return "Check passed" in res.stdout + res.stderr


def render(spec, quality: str = "delivery") -> Path:
    spec.out_dir.mkdir(exist_ok=True)
    out = spec.out_dir / f"{spec.project}.mp4"
    log(f"  rendering {out.relative_to(spec.root)} …")
    hf(spec, "render", "-o", str(out), "--fps", str(spec.fps), "--quality", quality, capture=True)
    info = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                "-show_entries", "format=duration,size", "-of", "json", str(out)], capture=True).stdout
    meta = json.loads(info)
    st, fm = meta["streams"][0], meta["format"]
    log(f"  ✓ {st['width']}x{st['height']} @ {st['r_frame_rate']} · {float(fm['duration']):.1f}s · {int(fm['size']) / 1e6:.1f} MB")
    return out
