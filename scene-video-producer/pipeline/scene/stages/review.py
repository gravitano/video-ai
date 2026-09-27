"""QC stage: contact sheets for human review, plus optional automatic vision QC.

Vision QC sends the keyframe and first/mid/last frames of each selected clip to any OpenAI-compatible
chat endpoint with image input (e.g. an OmniRoute gateway with MiniMax-M3), configured in scene.yaml:

  review:
    vision: {base_url: https://assist.gits.app/v1, key_file: ~/.gits_key, model: minimax/MiniMax-M3}

It only flags problems; choosing or regenerating takes stays a human decision (`scene clips --retake`, `scene select`).
"""
from __future__ import annotations

import base64
import json
import re
import tempfile
import urllib.request
from pathlib import Path

from ..util import SceneError, log, media_duration, run
from . import clips, keyframes

W, H = 270, 480
QC_PROMPT = """You are a strict video QC reviewer. Image 1 is the approved keyframe for this shot; images 2-4 are the
first, middle and last frames of the generated clip. Intended motion: {motion}

Check: (1) identity drift — face, hair, outfit, room differ from the keyframe; (2) anatomy — distorted hands/faces;
(3) unwanted readable text, letters, logos or watermarks; (4) scene cut or composition change; (5) motion not matching intent.
Reply with JSON only: {{"ok": true|false, "issues": ["short issue", ...]}}"""


def _sheet(images: list[list[Path]], dest: Path) -> None:
    inputs, filters, rows = [], [], []
    k = 0
    for r, row in enumerate(images):
        labels = []
        for img in row:
            inputs += ["-i", str(img)]
            filters.append(f"[{k}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[v{k}]")
            labels.append(f"[v{k}]")
            k += 1
        if len(labels) == 1:
            filters.append(f"{labels[0]}null[r{r}]")
        else:
            filters.append(f"{''.join(labels)}hstack=inputs={len(labels)}[r{r}]")
        rows.append(f"[r{r}]")
    widths = {len(row) for row in images}
    if len(widths) > 1:  # pad short rows so vstack accepts them
        maxw = max(widths) * W
        for r, row in enumerate(images):
            filters.append(f"[r{r}]pad={maxw}:{H}:0:0:black[p{r}]")
        rows = [f"[p{r}]" for r in range(len(images))]
    filters.append(f"{''.join(rows)}vstack=inputs={len(rows)}[out]" if len(rows) > 1 else f"{rows[0]}null[out]")
    dest.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]", "-frames:v", "1", "-q:v", "3", str(dest)])


def _frames(clip: Path, tmp: Path) -> list[Path]:
    dur = media_duration(clip)
    out = []
    for name, t in (("first", 0.05), ("mid", dur / 2), ("last", max(0.0, dur - 0.1))):
        p = tmp / f"{clip.parent.name}-{clip.stem}-{name}.jpg"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(clip), "-frames:v", "1", "-q:v", "3", str(p)])
        out.append(p)
    return out


def run_review(spec, state, vision: bool = False) -> None:
    rdir = spec.root / "review"
    kf = [(s, keyframes.current(spec, state, s)) for s in spec.shots]
    have = [p for _, p in kf if p]
    if have:
        ref = keyframes.path_of(spec, keyframes.REF_ID)
        per_row = 5
        imgs = ([ref] if ref.exists() else []) + have
        _sheet([imgs[i:i + per_row] for i in range(0, len(imgs), per_row)], rdir / "keyframes.jpg")
        log(f"  wrote {rdir.relative_to(spec.root)}/keyframes.jpg ({len(have)}/{len(spec.shots)} shots)")
    rows, qc = [], {}
    with tempfile.TemporaryDirectory(prefix="scene-review-") as tmp:
        tmp = Path(tmp)
        for s, k in kf:
            c = clips.selected_clip(spec, state, s)
            if not c:
                continue
            fr = _frames(c, tmp)
            rows.append([k] + fr if k else fr)
            if vision:
                qc[s["id"]] = _vision_check(spec, s, k, fr)
                v = qc[s["id"]]
                log(f"  QC {s['id']}: {'✓ ok' if v.get('ok') else '✗ ' + '; '.join(v.get('issues', []))}")
        if rows:
            _sheet(rows, rdir / "clips.jpg")
            log(f"  wrote {rdir.relative_to(spec.root)}/clips.jpg (keyframe | first | mid | last per shot)")
        else:
            log("  no clips yet — run `scene clips`")
    if qc:
        (rdir / "qc.json").write_text(json.dumps(qc, indent=1, ensure_ascii=False))
        bad = [sid for sid, v in qc.items() if not v.get("ok")]
        if bad:
            log("  flagged: " + ", ".join(bad) + "  → `scene clips --shot <id> --retake` or `scene select <id> <take>`")


def _vision_check(spec, shot, keyframe: Path | None, frames: list[Path]) -> dict:
    cfg = (spec.raw.get("review") or {}).get("vision")
    if not cfg:
        raise SceneError("vision QC needs review.vision {base_url, key_file, model} in scene.yaml")
    key = Path(cfg["key_file"]).expanduser().read_text().strip()
    content = [{"type": "text", "text": QC_PROMPT.format(motion=shot["motion_prompt"].strip())}]
    images = list(frames)
    sheet = spec.persona_images()[:1]
    if sheet:  # character sheet goes first so identity is judged against the persona, not only the keyframe
        sjpg = frames[0].parent / "persona-sheet.jpg"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(sheet[0]), "-vf", "scale=768:-2", "-q:v", "3", str(sjpg)])
        content[0]["text"] = ("Image 0 is the persona character sheet (the ground truth for the character's design); the numbering below "
                              "starts after it.\n\n" + content[0]["text"])
    if keyframe:
        kjpg = frames[0].parent / f"{shot['id']}-keyframe.jpg"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(keyframe), "-vf", "scale=540:-2", "-q:v", "3", str(kjpg)])
        images.insert(0, kjpg)
    for img in ([sjpg] if sheet else []) + images:
        content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(img.read_bytes()).decode()}})
    body = {"model": cfg["model"], "max_tokens": 400, "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            text = json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:  # QC must never block the pipeline
        return {"ok": None, "issues": [f"QC call failed: {e}"]}
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {"ok": None, "issues": [text[:200]]}
    except json.JSONDecodeError:
        return {"ok": None, "issues": [text[:200]]}
