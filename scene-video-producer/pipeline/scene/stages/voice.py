"""VO stage: synthesize each shot's line, measure it, record word timings. Runs before clips (it fixes durations)."""
from __future__ import annotations

from .. import providers
from ..timing import plan, total
from ..providers.edge_voice import TAIL
from ..util import content_key, log


def run(spec, state, shots=None, force=False) -> None:
    prov = providers.voice(spec.providers["voice"])
    for s in spec.select(shots):
        if not s.get("vo"):
            continue
        key = content_key("voice", s["vo"], prov.params())
        dest = spec.assets / "voice" / f"{s['id']}.wav"
        cur = state.get("voice", s["id"])
        if cur and cur.get("key") == key and dest.exists() and not force:
            log(f"  voice {s['id']}: cached ({cur['speech']:.2f}s)")
            continue
        info = prov.synthesize(s["vo"], dest)
        state.put("voice", s["id"], {"key": key, "file": str(dest.relative_to(spec.root)), **info})
        log(f"  voice {s['id']}: {info['speech']:.2f}s, {len(info['words'])} words")
    report(spec, state)


def report(spec, state) -> None:
    tl = plan(spec, state)
    target = spec.brief.get("duration")
    log("\n  shot            start   dur   vo_end")
    for p in tl:
        speech_end = p["vo_end"] - (TAIL if p["measured"] else 0)  # ignore the trailing silence pad
        warn = "  ⚠ speech runs past the shot end" if speech_end > p["dur"] else ""
        log(f"  {p['id']:<15} {p['start']:>5.1f}  {p['dur']:>4}s  {p['vo_end']:>6.2f}{warn}")
    t = total(tl)
    log(f"\n  total {t}s" + (f" (target {target}s{' ✓' if t == target else ' — adjust durations/vo_offset'})" if target else ""))
