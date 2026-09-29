"""Timeline planning: real voice-over drives shot durations.

Voice comes first in the pipeline. Each shot's duration is either fixed in scene.yaml
or derived from its measured VO length, rounded UP to whole seconds so the same number
can be sent to image-to-video models that only accept integer durations (MiniMax H3: 4–15s).

Overlay/SFX times may be written as:
  1.25            seconds from the shot start
  "w:kilat"       when the word "kilat" starts in this shot's VO   ("w:langkah#2" = 2nd occurrence)
  "w:kilat+0.2"   …plus/minus an offset
  "end-0.3"       relative to the shot end
  "vo_end+0.1"    relative to the end of this shot's VO
"""
from __future__ import annotations

import math
import re

from .util import SceneError

DEFAULT_VO_OFFSET = 0.3
DEFAULT_TAIL = 0.5
WORDS_PER_SEC_ESTIMATE = 2.2

_AT = re.compile(r"^(?:(?P<kind>w|end|vo_end)(?::(?P<word>[^#+\-\s][^#+]*?)(?:#(?P<nth>\d+))?)?)?\s*(?P<off>[+-]\s*\d+(?:\.\d+)?)?$")


def norm_word(w: str) -> str:
    return re.sub(r"[^\w-]", "", w.lower())


def plan(spec, state, min_duration: int = 1) -> list[dict]:
    """Return one timeline entry per shot: start, dur, vo offsets, and words in shot-local time."""
    out, t = [], 0.0
    for s in spec.shots:
        v = state.get("voice", s["id"])
        off = float(s.get("vo_offset", DEFAULT_VO_OFFSET)) if s.get("vo") else 0.0
        if v:
            speech = v["speech"]
            words = [{"text": w["text"], "s": round(off + w["s"], 3), "e": round(off + w["e"], 3)} for w in v["words"]]
        else:
            speech = len((s.get("vo") or "").split()) / WORDS_PER_SEC_ESTIMATE
            words = []
        dur = s.get("duration") or max(min_duration, math.ceil(off + speech + DEFAULT_TAIL))
        out.append({
            "id": s["id"], "start": round(t, 3), "dur": int(dur), "vo_offset": off,
            "vo_end": round(off + speech, 3), "words": words, "measured": bool(v),
        })
        t += dur
    return out


def total(timeline: list[dict]) -> int:
    return sum(p["dur"] for p in timeline)


def resolve_at(at, shot_plan: dict, default: float = 0.0) -> float:
    if at is None:
        return default
    if isinstance(at, (int, float)):
        return float(at)
    try:
        return float(str(at))
    except ValueError:
        pass
    m = _AT.match(str(at).strip())
    if not m:
        raise SceneError(f"{shot_plan['id']}: cannot parse time '{at}'")
    kind, word, nth, off = m.group("kind"), m.group("word"), m.group("nth"), m.group("off")
    offset = float(off.replace(" ", "")) if off else 0.0
    if kind is None:
        return offset
    if kind == "end":
        return shot_plan["dur"] + offset
    if kind == "vo_end":
        return shot_plan["vo_end"] + offset
    # word reference
    if not shot_plan["words"]:
        raise SceneError(f"{shot_plan['id']}: '{at}' needs word timings — run `scene voice` first")
    target, want = norm_word(word), int(nth or 1)
    hits = [w for w in shot_plan["words"] if norm_word(w["text"]) == target]
    if len(hits) < want:
        have = " ".join(w["text"] for w in shot_plan["words"])
        raise SceneError(f"{shot_plan['id']}: word '{word}' (#{want}) not in VO: {have}")
    return round(hits[want - 1]["s"] + offset, 3)
