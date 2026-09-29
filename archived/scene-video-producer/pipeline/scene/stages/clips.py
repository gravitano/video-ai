"""N stage: image-to-video clip per shot (MiniMax H3 by default).

Money-safety rules:
  * cost is estimated and checked against the budget BEFORE anything is submitted;
  * a paid submission needs --yes (or an interactive "y");
  * every task_id is written to state before polling, so a rerun resumes it instead of paying again;
  * a clip is only regenerated when its key (model, resolution, duration, motion prompt, keyframe hash) changes.
"""
from __future__ import annotations

import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .. import providers
from ..timing import plan
from ..util import SceneError, content_key, log
from . import keyframes

EXTS = (".mp4", ".mov", ".webm")


def video_refs(spec) -> list[Path]:
    """Persona images sent as reference_image with every clip (disable with providers.video.persona_refs: false)."""
    return spec.persona_images() if spec.providers["video"].get("persona_refs", True) else []


def clip_key(prov, shot, seconds: int, kf_hash: str, ref_hashes: list[str] | None = None) -> str:
    return content_key("clip", prov.name, prov.model, prov.resolution, prov.fit_duration(seconds),
                       shot["motion_prompt"].strip(), kf_hash, getattr(prov, "expansion", None), ref_hashes or [])


def selected_clip(spec, state, shot) -> Path | None:
    """Selected, finished take for the CURRENT key (stale clips are ignored so edits never show old footage)."""
    e = state.get("clips", shot["id"])
    if not e:
        return None
    takes = [t for t in e.get("takes", []) if t.get("status") == "done"]
    if not takes:
        return None
    if e.get("key") != _expected_key(spec, state, shot):
        return None
    pick = next((t for t in takes if t["n"] == e.get("selected")), takes[0])
    p = spec.root / pick["file"]
    return p if p.exists() else None


def _expected_key(spec, state, shot) -> str | None:
    kf = state.get("keyframes", shot["id"])
    if not kf:
        return None
    prov =providers.video(spec.providers["video"])
    tl = {p["id"]: p for p in plan(spec, state, prov.limits()[0])}
    return clip_key(prov, shot, tl[shot["id"]]["dur"], kf["hash"], keyframes.persona_hashes(spec) if video_refs(spec) else [])


def run(spec, state, ledger, shots=None, takes: int = 1, retake: bool = False, budget: float | None = None,
        yes: bool = False, dry_run: bool = False, jobs: int = 4) -> None:
    prov = providers.video(spec.providers["video"])
    tl = {p["id"]: p for p in plan(spec, state, prov.limits()[0])}
    missing_vo = [s["id"] for s in spec.select(shots) if s.get("vo") and not tl[s["id"]]["measured"] and not s.get("duration")]
    if missing_vo:
        raise SceneError(f"run `scene voice` first — durations come from the VO (unmeasured: {', '.join(missing_vo)})")

    work = []  # (shot, entry, [take numbers to submit], seconds)
    for s in spec.select(shots):
        kf = keyframes.current(spec, state, s)
        if not kf:
            raise SceneError(f"{s['id']}: no current keyframe — run `scene keyframes` (or adopt one)")
        seconds = tl[s["id"]]["dur"]
        if seconds != prov.fit_duration(seconds):
            log(f"  ⚠ {s['id']}: {seconds}s is outside {prov.name} limits {prov.limits()} — clip will be {prov.fit_duration(seconds)}s and trimmed/held in the edit")
        key = clip_key(prov, s, seconds, state.get("keyframes", s["id"])["hash"],
                       keyframes.persona_hashes(spec) if video_refs(spec) else [])
        entry = state.get("clips", s["id"]) or {}
        if entry.get("key") != key:
            if entry.get("takes"):
                entry.setdefault("history", []).extend(entry.pop("takes"))
            entry.update({"key": key, "takes": [], "selected": None})
        alive = [t for t in entry["takes"] if t["status"] in ("pending", "done")]
        want = max(takes, len(alive) + (1 if retake else 0))
        next_n = max([t["n"] for t in entry["takes"]] + [0]) + 1
        new = list(range(next_n, next_n + max(0, want - len(alive))))
        work.append((s, entry, new, seconds, kf))

    new_cost = sum(prov.estimate(sec) * len(new) for _, _, new, sec, _ in work)
    n_new = sum(len(new) for _, _, new, _, _ in work)
    pending = sum(1 for _, e, _, _, _ in work for t in e["takes"] if t["status"] == "pending")
    cap = budget if budget is not None else spec.budget.get("video_usd")
    spent = ledger.spent("video")

    log(f"  provider {prov.name} · {prov.model} · {prov.resolution} · ${prov.price_per_second():.2f}/s")
    for s, e, new, sec, _ in work:
        done = sum(1 for t in e["takes"] if t["status"] == "done")
        log(f"  {s['id']:<15} {prov.fit_duration(sec):>3}s  done:{done} pending:{sum(1 for t in e['takes'] if t['status'] == 'pending')}"
            f"  new:{len(new)}  ${prov.estimate(sec) * len(new):.2f}")
    log(f"  → {n_new} new submission(s), est. ${new_cost:.2f}; resuming {pending}; spent so far ${spent:.2f}"
        + (f"; budget ${cap:.2f}" if cap is not None else ""))

    if dry_run or (n_new == 0 and pending == 0):
        if n_new == 0 and pending == 0:
            log("  nothing to do — all clips current")
        return
    if cap is not None and spent + new_cost > cap + 1e-9:
        raise SceneError(f"budget exceeded: ${spent:.2f} spent + ${new_cost:.2f} new > ${cap:.2f} — raise budget.video_usd or pass --budget")
    if new_cost > 0 and not yes:
        if not sys.stdin.isatty():
            raise SceneError(f"this will spend about ${new_cost:.2f} — rerun with --yes to confirm")
        if input(f"  spend about ${new_cost:.2f}? [y/N] ").strip().lower() != "y":
            raise SceneError("cancelled")

    for s, e, new, _, _ in work:
        for n in new:
            e["takes"].append({"n": n, "status": "queued"})
        state.put("clips", s["id"], e)

    refs = video_refs(spec)
    if refs:
        log(f"  persona: sending {len(refs)} reference image(s) with each clip")
    jobs_list = [(s, t, sec, kf) for s, e, _, sec, kf in work for t in e["takes"] if t["status"] in ("queued", "pending")]

    def one(job):
        s, take, sec, kf = job
        sid, n = s["id"], take["n"]
        try:
            if take["status"] == "queued":
                task_id = prov.submit(s["motion_prompt"].strip(), kf, sec, references=refs)
                usd = prov.estimate(sec)
                _set_take(state, sid, n, status="pending", task_id=task_id, usd=usd, seconds=prov.fit_duration(sec))
                ledger.add(event="submitted", kind="video", shot=sid, take=n, provider=prov.name, model=prov.model,
                           resolution=prov.resolution, seconds=prov.fit_duration(sec), usd=usd, task_id=task_id)
                log(f"  {sid} take {n}: submitted ({task_id})")
            else:
                task_id = take["task_id"]
                log(f"  {sid} take {n}: resuming {task_id}")
            url = prov.wait(task_id)
            dest = spec.assets / "clips" / sid / f"take-{n}.mp4"
            prov.download(url, dest)
            _set_take(state, sid, n, status="done", file=str(dest.relative_to(spec.root)))
            ledger.add(event="done", kind="video", shot=sid, take=n, task_id=task_id)
            e = state.get("clips", sid)
            if not e.get("selected"):
                state.update("clips", sid, selected=n)
            return f"  {sid} take {n}: ✓ {dest.relative_to(spec.root)}"
        except SceneError as err:
            if take["status"] == "queued" and not _get_take(state, sid, n).get("task_id"):
                _set_take(state, sid, n, status="failed", error=str(err))
            elif "still running" not in str(err):
                _set_take(state, sid, n, status="failed", error=str(err))
                ledger.add(event="failed", kind="video", shot=sid, take=n, error=str(err)[:300])
            return f"  {sid} take {n}: ✗ {err}"

    with ThreadPoolExecutor(jobs) as ex:
        for line in ex.map(one, jobs_list):
            log(line)


def _get_take(state, sid, n) -> dict:
    return next(t for t in state.get("clips", sid)["takes"] if t["n"] == n)


def _set_take(state, sid, n, **fields) -> None:
    with state._lock:
        e = state.data["clips"][sid]
        next(t for t in e["takes"] if t["n"] == n).update(fields)
        state._save()


def select(spec, state, sid: str, n: int) -> None:
    spec.shot(sid)
    e = state.get("clips", sid)
    if not e or not any(t["n"] == n and t["status"] == "done" for t in e.get("takes", [])):
        raise SceneError(f"{sid}: take {n} is not a finished take")
    state.update("clips", sid, selected=n)
    log(f"  {sid}: selected take {n}")


def adopt(spec, state, src: Path) -> None:
    """Register clips made outside the pipeline (e.g. MiniMax/Hailuo web): files named <shot_id>*.mp4.

    Every matching file becomes a take (01_hook.mp4, 01_hook-2.mp4 …); the first new one is selected.
    Files already adopted (same name + size) are skipped, so rerunning is safe.
    """
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in EXTS)
    total = 0
    for s in spec.shots:
        matches = [f for f in files if f.stem == s["id"] or f.stem.startswith(s["id"] + "-") or f.stem.startswith(s["id"] + "_")]
        matches.sort(key=lambda f: (f.stem != s["id"], f.name))  # the un-numbered file is the primary take
        if not matches:
            continue
        if not state.get("keyframes", s["id"]):
            raise SceneError(f"{s['id']}: adopt/generate its keyframe before adopting a clip")
        e = state.get("clips", s["id"]) or {"takes": []}
        key = _expected_key(spec, state, s)
        if e.get("key") != key:  # clips for an older keyframe/prompt are history, not candidates
            if e.get("takes"):
                e.setdefault("history", []).extend(e.pop("takes"))
            e.update({"key": key, "takes": [], "selected": None})
        seen = {(t.get("origin"), t.get("size")) for t in e["takes"]}
        first_new = None
        for f in matches:
            if (f.name, f.stat().st_size) in seen:
                continue
            n = max([t["n"] for t in e["takes"]] + [0]) + 1
            dest = spec.assets / "clips" / s["id"] / f"take-{n}{f.suffix.lower()}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dest)
            e["takes"].append({"n": n, "status": "done", "file": str(dest.relative_to(spec.root)), "source": "adopted",
                               "origin": f.name, "size": f.stat().st_size})
            first_new = first_new or n
            total += 1
            log(f"  adopted {f.name} → {s['id']} take {n}")
        if first_new and not e.get("selected"):
            e["selected"] = first_new
        state.put("clips", s["id"], e)
    log(f"  {total} clip(s) adopted" + ("" if total else " — name files like 01_hook.mp4 / 01_hook-2.mp4"))
