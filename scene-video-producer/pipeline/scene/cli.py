"""`scene` — run the S.C.E.N.E. pipeline for one scene.yaml.

  scene init DIR                         scaffold DIR/scene.yaml
  scene status | estimate                what exists, what it will cost
  scene voice [--shot ID…]               VO + word timings (fixes shot durations)
  scene keyframes [--shot ID…]           reference + one keyframe per shot
  scene adopt keyframes|clips DIR        register images/clips made elsewhere
  scene handoff [--target minimax|flow]  export keyframes + motion prompts for a web UI (MiniMax/Hailuo, Google Flow)
  scene clips [--shot ID…] [--takes N] [--retake] [--budget USD] [--yes] [--dry-run]
  scene select SHOT TAKE                 choose which take goes in the edit
  scene voices search [--lang id] [--gender female] [--q cute]   ElevenLabs Voice Library + preview downloads
  scene voices add PUBLIC_OWNER_ID VOICE_ID --name NAME        add a library voice to your account
  scene review [--vision]                contact sheets (+ automatic QC)
  scene build | check | render           HyperFrames assembly → checks → MP4
  scene run [--no-clips] [--yes]         voice → keyframes → clips → build → check → render
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, providers
from .spec import load
from .state import Ledger, State
from .stages import build as build_stage
from .stages import clips as clip_stage
from .stages import keyframes as kf_stage
from .stages import review as review_stage
from .stages import voice as voice_stage
from .timing import plan, total
from .util import SceneError, log


def _ctx(args):
    spec = load(args.spec)
    return spec, State(spec.root), Ledger(spec.root)


def cmd_init(args):
    dest = Path(args.dir)
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / "scene.yaml"
    if target.exists() and not args.force:
        raise SceneError(f"{target} already exists (use --force to overwrite)")
    text = (Path(__file__).parent / "templates" / "scene.yaml").read_text().replace("project: my-video", f"project: {dest.resolve().name}")
    target.write_text(text)
    (dest / ".gitignore").write_text(".scene/\nvideo/node_modules/\nout/\nreview/\n")
    log(f"  created {target}\n  next: edit it (or ask Claude to fill it from a brief), then `scene estimate`")


def cmd_status(args):
    spec, state, ledger = _ctx(args)
    prov = providers.video(spec.providers["video"])
    tl = plan(spec, state, prov.limits()[0])
    log(f"  {spec.project} · {len(spec.shots)} shots · {total(tl)}s (target {spec.brief.get('duration', '?')}s)")
    log("  shot            dur  voice  keyframe  clip")
    for s, p in zip(spec.shots, tl):
        v = "✓" if p["measured"] else ("—" if not s.get("vo") else "·")
        k = "✓" if kf_stage.current(spec, state, s) else ("stale" if state.get("keyframes", s["id"]) else "·")
        e = state.get("clips", s["id"]) or {}
        c = clip_stage.selected_clip(spec, state, s)
        takes = e.get("takes", [])
        cl = (f"✓ take {e.get('selected')}" if c else "·") + (f" ({sum(t['status'] == 'done' for t in takes)} done, "
                                                               f"{sum(t['status'] == 'pending' for t in takes)} pending)" if takes else "")
        log(f"  {s['id']:<15} {p['dur']:>3}s  {v:^5}  {k:^8}  {cl}")
    log(f"  spent on video: ${ledger.spent('video'):.2f}" + (f" of ${spec.budget['video_usd']:.2f}" if spec.budget.get("video_usd") else ""))


def cmd_estimate(args):
    spec, state, ledger = _ctx(args)
    clip_stage.run(spec, state, ledger, dry_run=True, takes=args.takes)


def cmd_voice(args):
    spec, state, _ = _ctx(args)
    voice_stage.run(spec, state, args.shot, force=args.force)


def cmd_keyframes(args):
    spec, state, _ = _ctx(args)
    kf_stage.run(spec, state, args.shot, force=args.force, jobs=args.jobs)


def cmd_adopt(args):
    spec, state, _ = _ctx(args)
    src = Path(args.dir)
    if not src.is_dir():
        raise SceneError(f"{src} is not a directory")
    (kf_stage.adopt if args.kind == "keyframes" else clip_stage.adopt)(spec, state, src)


def cmd_handoff(args):
    from .stages import handoff
    spec, state, _ = _ctx(args)
    handoff.run(spec, state, args.target)


def cmd_clips(args):
    spec, state, ledger = _ctx(args)
    clip_stage.run(spec, state, ledger, args.shot, takes=args.takes, retake=args.retake, budget=args.budget,
                   yes=args.yes, dry_run=args.dry_run, jobs=args.jobs)


def cmd_voices(args):
    from .providers import elevenlabs_voice as el
    key = el.api_key()
    if args.action == "add":
        vid = el.add_shared(key, args.owner, args.voice, args.name)
        log(f"  added '{args.name}' → voice_id {vid}\n  use: voice: {{name: elevenlabs, voice_id: {vid}}}")
        return
    voices = el.search_shared(key, language=args.lang, gender=args.gender, age=args.age, search=args.q,
                              descriptives=args.descriptive, use_cases=args.use_case, page_size=args.limit)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    import json as _json
    import urllib.request as _ur
    (out / "voices.json").write_text(_json.dumps(voices, indent=1, ensure_ascii=False))
    log(f"  {len(voices)} voice(s) → previews in {out}/")
    for i, v in enumerate(voices, 1):
        prev = next((vl.get("preview_url") for vl in v.get("verified_languages") or [] if vl.get("language") == args.lang and vl.get("preview_url")),
                    v.get("preview_url"))
        fname = f"{i:02d}-{''.join(ch for ch in v['name'] if ch.isalnum())[:24]}.mp3"
        if prev:
            try:
                _ur.urlretrieve(prev, out / fname)
            except Exception:
                fname = "(preview failed)"
        log(f"  {i:>2}. {v['name'][:30]:<30} {v.get('gender', '')}/{v.get('age', '')} {v.get('descriptive', '')} · {v.get('use_case', '')}"
            f" · {v.get('language')}/{v.get('accent')} · owner {v['public_owner_id'][:10]}… id {v['voice_id']} · {fname}")


def cmd_select(args):
    spec, state, _ = _ctx(args)
    clip_stage.select(spec, state, args.shot_id, args.take)


def cmd_review(args):
    spec, state, _ = _ctx(args)
    review_stage.run_review(spec, state, vision=args.vision)


def cmd_build(args):
    spec, state, _ = _ctx(args)
    build_stage.build(spec, state)


def cmd_check(args):
    spec, _, _ = _ctx(args)
    if not build_stage.check(spec):
        raise SceneError("hyperframes check failed — see findings above")


def cmd_render(args):
    spec, _, _ = _ctx(args)
    build_stage.render(spec, args.quality)


def _require_check(spec):
    if not build_stage.check(spec):
        raise SceneError("hyperframes check failed — fix the findings, then `scene render`")


def cmd_run(args):
    spec, state, ledger = _ctx(args)
    steps = [("voice", lambda: voice_stage.run(spec, state)),
             ("keyframes", lambda: kf_stage.run(spec, state)),
             ("clips", None if args.no_clips else lambda: clip_stage.run(spec, state, ledger, yes=args.yes, budget=args.budget)),
             ("build", lambda: build_stage.build(spec, state)),
             ("check", lambda: _require_check(spec)),
             ("render", lambda: build_stage.render(spec))]
    for name, fn in steps:
        if fn is None:
            log(f"\n▸ {name}: skipped (stills with virtual camera)")
            continue
        log(f"\n▸ {name}")
        fn()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scene", description="S.C.E.N.E. AI video pipeline", formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--spec", default="scene.yaml", help="path to scene.yaml or its directory (default: ./scene.yaml)")
    ap.add_argument("--version", action="version", version=f"scene {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="scaffold a new scene.yaml")
    p.add_argument("dir")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_init)

    sub.add_parser("status", help="per-shot progress and spend").set_defaults(fn=cmd_status)
    p = sub.add_parser("estimate", help="what `scene clips` would submit and cost")
    p.add_argument("--takes", type=int, default=1)
    p.set_defaults(fn=cmd_estimate)

    for name, fn, help_ in (("voice", cmd_voice, "TTS + word timings"), ("keyframes", cmd_keyframes, "generate keyframes")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--shot", nargs="+")
        p.add_argument("--force", action="store_true", help="regenerate even if cached")
        if name == "keyframes":
            p.add_argument("--jobs", type=int, default=4)
        p.set_defaults(fn=fn)

    p = sub.add_parser("adopt", help="register externally made keyframes or clips")
    p.add_argument("kind", choices=["keyframes", "clips"])
    p.add_argument("dir")
    p.set_defaults(fn=cmd_adopt)

    p = sub.add_parser("handoff", help="export keyframes + prompts for making clips in a web UI")
    p.add_argument("--target", default="minimax", choices=["minimax", "flow"])
    p.set_defaults(fn=cmd_handoff)

    p = sub.add_parser("clips", help="image-to-video per shot (paid)")
    p.add_argument("--shot", nargs="+")
    p.add_argument("--takes", type=int, default=1, help="ensure at least N takes per shot")
    p.add_argument("--retake", action="store_true", help="add one more take")
    p.add_argument("--budget", type=float, help="override budget.video_usd")
    p.add_argument("--yes", action="store_true", help="confirm spending")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--jobs", type=int, default=4)
    p.set_defaults(fn=cmd_clips)

    p = sub.add_parser("voices", help="ElevenLabs Voice Library: search (+previews) or add")
    vs = p.add_subparsers(dest="action", required=True)
    q = vs.add_parser("search")
    q.add_argument("--lang", default="id")
    q.add_argument("--gender")
    q.add_argument("--age")
    q.add_argument("--q", help="free-text search, e.g. cute")
    q.add_argument("--descriptive", nargs="+")
    q.add_argument("--use-case", nargs="+")
    q.add_argument("--limit", type=int, default=20)
    q.add_argument("--out", default="voice-previews")
    a = vs.add_parser("add")
    a.add_argument("owner")
    a.add_argument("voice")
    a.add_argument("--name", required=True)
    p.set_defaults(fn=cmd_voices)

    p = sub.add_parser("select", help="choose the take used in the edit")
    p.add_argument("shot_id")
    p.add_argument("take", type=int)
    p.set_defaults(fn=cmd_select)

    p = sub.add_parser("review", help="contact sheets (+ --vision QC)")
    p.add_argument("--vision", action="store_true")
    p.set_defaults(fn=cmd_review)

    sub.add_parser("build", help="assemble the HyperFrames project").set_defaults(fn=cmd_build)
    sub.add_parser("check", help="hyperframes check").set_defaults(fn=cmd_check)
    p = sub.add_parser("render", help="render the MP4")
    p.add_argument("--quality", default="delivery", choices=["draft", "looks", "delivery"])
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("run", help="all stages in order")
    p.add_argument("--no-clips", action="store_true", help="skip paid video generation")
    p.add_argument("--yes", action="store_true")
    p.add_argument("--budget", type=float)
    p.set_defaults(fn=cmd_run)

    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except SceneError as e:
        log(f"✗ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        log("✗ interrupted — state is saved; rerun the same command to resume")
        sys.exit(130)


if __name__ == "__main__":
    main()
