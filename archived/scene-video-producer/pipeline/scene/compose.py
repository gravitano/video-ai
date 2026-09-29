"""HyperFrames composition generator: scene.yaml + timeline -> index.html, compositions/<shot>.html, captions.html.

Every visual treatment is a named component selected from the spec, so no per-video code is written:

  hud        {text, color, at}
  overlays:  headline {text, top, size, color, at, anim: slam|snap|rise|glitch|mono|type, out, plate}
             callouts {boxes: [{x, y, w, h, index, title, title2, sub, at}], confirm_at, title_size, pad}   # moves with the camera
             flow     {top, size, tokens: [{text, color, at}], arrow_color}
             badge    {top, text, at}
             cta      {text, top, at, pulse}
             stats    {top, columns, items: [{value, prefix, suffix, label, at}], plate}          # count-up numbers
             chips    {top, items: [{text, at, color}], size, plate}                            # pills that pop in
             image    {src, top, w, x, at, anim: rise|pop, plate}   # src relative to scene.yaml (copied on build)
  fx:        glow {x, y, color} · alarm {pulses: [[at, alpha]], shake_at, wash: [from, to]}
             flash_in {dur} · flash_out {dur} · bloom {x, y, at} · bars {top, widths, at, step, out}
  camera     {from, to, x: [a, b], y: [a, b], origin, ease}      (camera_clip applies when a video clip is used)
"""
from __future__ import annotations

import html
import json
import math
import re

from .timing import norm_word, resolve_at

DEFAULT_CAMERA = {"from": 1.06, "to": 1.14, "x": [0, 0], "y": [0, 0], "origin": "50% 50%", "ease": "sine.inOut"}
DEFAULT_CAMERA_CLIP = {"from": 1.0, "to": 1.03, "x": [0, 0], "y": [0, 0], "origin": "50% 50%", "ease": "sine.inOut"}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fit(text: str, size: int, width: int = 920, k: float = 0.80) -> int:
    """Largest font size <= size whose estimated display-caps width fits `width`."""
    return int(min(size, width / (k * max(1, len(text)))))


def _num(v) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


# ====================================================================== scene
def scene_html(spec, shot: dict, p: dict, plate: dict) -> str:
    """plate = {"kind": "image"|"video", "src": "assets/..."}"""
    sid = f"s-{shot['id']}".replace("_", "-")
    d = p["dur"]
    th = spec.theme
    fonts = th["fonts"]
    C = spec.color
    T = lambda at, default=0.0: resolve_at(at, p, default)  # noqa: E731

    if plate["kind"] == "video":  # the clip carries its own camera move: keep ours subtle
        cam = {**DEFAULT_CAMERA_CLIP, **shot.get("camera_clip", {})}
    else:
        cam = {**DEFAULT_CAMERA, **shot.get("camera", {})}
    css, dom, top_dom, cam_layer, js = [], [], [], [], []

    css.append(f"""
      #{sid} {{ position:absolute; inset:0; overflow:hidden; background:{th['bg']}; color:{C('ink')}; }}
      #{sid} .cam {{ position:absolute; inset:0; transform-origin:{cam['origin']}; will-change:transform; }}
      #{sid} .drift, #{sid} .shake {{ position:absolute; inset:0; will-change:transform; }}
      #{sid} .plate {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; }}
      #{sid} .scrim-top {{ position:absolute; left:0; top:0; width:100%; height:860px;
          background:linear-gradient(180deg, rgba(6,12,26,.90) 0%, rgba(6,12,26,.62) 42%, rgba(6,12,26,0) 100%); }}
      #{sid} .scrim-bot {{ position:absolute; left:0; bottom:0; width:100%; height:820px;
          background:linear-gradient(0deg, rgba(6,12,26,.88) 0%, rgba(6,12,26,.45) 45%, rgba(6,12,26,0) 100%); }}
      #{sid} .hud {{ position:absolute; left:80px; top:228px; display:flex; align-items:center; gap:18px;
          font-family:'{fonts['mono']}', monospace; font-weight:700; font-size:26px; letter-spacing:.14em; }}
      #{sid} .hud .rule {{ display:block; width:110px; height:3px; transform-origin:0 50%; }}
      #{sid} .hl {{ position:absolute; left:80px; width:940px; font-family:'{fonts['display']}', sans-serif; text-transform:uppercase;
          line-height:1; letter-spacing:-0.03em; white-space:nowrap; transform-origin:0 50%; }}
      #{sid} .hl.mono {{ font-family:'{fonts['mono']}', monospace; font-weight:700; text-transform:none; letter-spacing:0; }}
      #{sid} .hl.hl-plate {{ width:auto; max-width:940px; padding:10px 22px 14px; border-radius:14px; background:rgba(6,12,26,.78);
          box-shadow:0 10px 40px rgba(0,0,0,.35); }}
      #{sid} .hl.hl-plate .gl {{ width:auto; }}
      #{sid} .hl .caret {{ display:inline-block; width:.55em; height:1em; margin-left:.08em; vertical-align:-0.12em; background:{C('accent')}; }}
      #{sid} .gl {{ position:relative; display:block; width:940px; }}
      #{sid} .gl span, #{sid} .gl strong {{ position:absolute; left:0; top:0; font-weight:400; }}
      #{sid} .gl strong {{ position:relative; }}
      #{sid} .gl span:nth-child(1) {{ color:#ff2d55; mix-blend-mode:screen; }}
      #{sid} .gl span:nth-child(2) {{ color:#22e1ff; mix-blend-mode:screen; }}
    """)

    if plate["kind"] == "video":
        plate_el = (f'<video id="{sid}-clip" class="plate" src="{plate["src"]}" data-start="0" data-duration="{d}" '
                    f'muted playsinline></video>')
    else:
        plate_el = f'<img class="plate" src="{plate["src"]}" alt="" />'
    dom.append(f'<div class="cam" id="{sid}-cam" data-layout-allow-overflow><div class="drift" id="{sid}-drift">'
               f'<div class="shake" id="{sid}-shake">{plate_el}</div></div></div>')

    def camera_tweens(cam_id: str, drift_id: str) -> None:
        js.append(f'tl.fromTo("#{cam_id}", {{ scale:{cam["from"]}, x:{cam["x"][0]}, y:{cam["y"][0]} }}, '
                  f'{{ scale:{cam["to"]}, x:{cam["x"][1]}, y:{cam["y"][1]}, duration:{d}, ease:"{cam["ease"]}" }}, 0);')
        js.append(f'tl.fromTo("#{drift_id}", {{ scale:1.02, x:-7, y:5 }}, {{ scale:1.02, x:7, y:-5, '
                  f'duration:{d / 2:.3f}, ease:"sine.inOut", yoyo:true, repeat:1 }}, 0);')

    camera_tweens(f"{sid}-cam", f"{sid}-drift")

    # ------------------------------------------------------------------ fx
    for i, fx in enumerate(shot.get("fx", [])):
        kind, fid = fx["type"], f"{sid}-fx{i}"
        if kind == "glow":
            col = C(fx.get("color"), "accent")
            css.append(f"#{fid} {{ position:absolute; left:{fx.get('x', '50%')}; top:{fx.get('y', '45%')}; width:900px; height:900px; "
                       f"margin:-450px 0 0 -450px; border-radius:50%; background:radial-gradient(circle, {col}55 0%, {col}00 65%); mix-blend-mode:screen; }}")
            dom.append(f'<div id="{fid}" data-layout-ignore></div>')
            js.append(f'tl.fromTo("#{fid}", {{ opacity:.55, scale:.9 }}, {{ opacity:.95, scale:1.08, duration:{d / 2:.3f}, ease:"sine.inOut", yoyo:true, repeat:1 }}, 0);')
        elif kind == "alarm":
            w0, w1 = fx.get("wash", [0.25, 0.6])
            css.append(f"""#{fid}-wash {{ position:absolute; inset:0; mix-blend-mode:multiply;
                background:radial-gradient(ellipse at 60% 40%, rgba(255,40,60,.55) 0%, rgba(120,0,20,.35) 55%, rgba(40,0,10,.5) 100%); }}
              #{fid}-glow {{ position:absolute; inset:0; opacity:0; mix-blend-mode:screen; background:radial-gradient(circle at 70% 30%, rgba(255,60,80,.5), rgba(255,60,80,0) 60%); }}""")
            dom.append(f'<div id="{fid}-wash" data-layout-ignore></div><div id="{fid}-glow" data-layout-ignore></div>')
            js.append(f'tl.fromTo("#{fid}-wash", {{ opacity:{w0} }}, {{ opacity:{w1}, duration:{d}, ease:"none" }}, 0);')
            pulses = sorted((T(a), alpha) for a, alpha in fx.get("pulses", []))
            for k, (t, alpha) in enumerate(pulses):
                nxt = pulses[k + 1][0] if k + 1 < len(pulses) else d
                fade = max(0.1, min(0.6, nxt - t - 0.2))
                js.append(f'tl.fromTo("#{fid}-glow", {{ opacity:0 }}, {{ opacity:{alpha}, duration:.16, ease:"power2.out", immediateRender:{str(k == 0).lower()} }}, {t:.3f});')
                js.append(f'tl.to("#{fid}-glow", {{ opacity:0, duration:{fade:.2f}, ease:"power2.in" }}, {t + 0.17:.3f});')
            if fx.get("shake_at") is not None:
                t = T(fx["shake_at"])
                for k, (sx, sy) in enumerate([(-14, 6), (12, -8), (-9, 10), (8, -5), (-5, 4), (3, -2), (0, 0)]):
                    js.append(f'tl.set("#{sid}-shake", {{ x:{sx}, y:{sy} }}, {t + k * 0.045:.3f});')
        elif kind in ("flash_in", "flash_out"):
            start_opacity = 0 if kind == "flash_out" else 1
            css.append(f"#{fid} {{ position:absolute; inset:0; opacity:{start_opacity}; background:radial-gradient(circle at 50% 45%, #ffffff 0%, #bff6ff 45%, {C('accent')} 100%); }}")
            top_dom.append(f'<div id="{fid}" data-layout-ignore></div>')
            if kind == "flash_out":
                dur = fx.get("dur", 0.22)
                js.append(f'tl.fromTo("#{fid}", {{ opacity:0 }}, {{ opacity:1, duration:{dur}, ease:"power1.in" }}, {d - dur:.3f});')
            else:
                js.append(f'tl.fromTo("#{fid}", {{ opacity:1 }}, {{ opacity:0, duration:{fx.get("dur", 0.45)}, ease:"power2.out" }}, {fx.get("at", 0.08)});')
        elif kind == "bloom":
            col = C(fx.get("color"), "accent")
            css.append(f"#{fid} {{ position:absolute; left:{fx.get('x', '50%')}; top:{fx.get('y', '47%')}; width:1300px; height:700px; margin:-350px 0 0 -650px; "
                       f"border-radius:50%; background:radial-gradient(ellipse, {col}66 0%, {col}00 70%); mix-blend-mode:screen; }}")
            dom.append(f'<div id="{fid}" data-layout-ignore></div>')
            t = T(fx.get("at"), 0.2)
            js.append(f'tl.fromTo("#{fid}", {{ opacity:0, scale:.7 }}, {{ opacity:.9, scale:1, duration:1.6, ease:"power2.out" }}, {t:.3f});')
            js.append(f'tl.to("#{fid}", {{ opacity:.55, duration:1.2, ease:"sine.inOut", yoyo:true, repeat:1 }}, {t + 1.6:.3f});')
        elif kind == "bars":
            widths = fx.get("widths", [520, 380, 460, 300, 540, 410])
            css.append(f"""#{fid} {{ position:absolute; left:80px; top:{fx.get('top', 372)}px; width:560px; display:flex; flex-direction:column; gap:14px; }}
              #{fid} .bar {{ display:block; height:12px; border-radius:6px; background:{C('accent')}; opacity:.85; transform-origin:0 50%; }}""")
            dom.append(f'<div id="{fid}">' + "".join(f'<span class="bar" id="{fid}-b{k}" style="width:{w}px"></span>' for k, w in enumerate(widths)) + "</div>")
            t0, step = T(fx.get("at"), 1.0), fx.get("step", 0.22)
            for k in range(len(widths)):
                js.append(f'tl.fromTo("#{fid}-b{k}", {{ scaleX:0 }}, {{ scaleX:1, duration:.3, ease:"power3.out" }}, {t0 + k * step:.3f});')
            if fx.get("out") is not None:
                js.append(f'tl.to("#{fid}", {{ opacity:0, y:-20, duration:.22, ease:"power2.in" }}, {T(fx["out"]):.3f});')

    dom.append('<div class="scrim-top" data-layout-ignore></div><div class="scrim-bot" data-layout-ignore></div>')

    # ------------------------------------------------------------------ hud
    hud = shot.get("hud")
    if hud:
        col = C(hud.get("color"), "accent")
        at = T(hud.get("at"), 0.08)
        dom.append(f'<div class="hud" style="color:{col}"><span class="rule" id="{sid}-rule" style="background:{col}"></span>'
                   f'<span id="{sid}-hudtxt">{esc(hud["text"])}</span></div>')
        js.append(f'tl.fromTo("#{sid}-rule", {{ scaleX:0 }}, {{ scaleX:1, duration:.45, ease:"expo.out" }}, {at:.3f});')
        js.append(f'tl.fromTo("#{sid}-hudtxt", {{ opacity:0, x:-16 }}, {{ opacity:1, x:0, duration:.4, ease:"power3.out" }}, {at + 0.12:.3f});')

    # ------------------------------------------------------------------ overlays
    for i, ov in enumerate(shot.get("overlays", [])):
        kind, oid = ov["type"], f"{sid}-o{i}"
        if kind == "headline":
            _headline(ov, oid, dom, js, C, T, d)
        elif kind == "callouts":
            _callouts(ov, oid, css, cam_layer, js, C, T, fonts)
        elif kind == "flow":
            _flow(ov, oid, css, dom, js, C, T, fonts)
        elif kind == "badge":
            css.append(f"""#{oid} {{ position:absolute; left:80px; top:{ov.get('top', 440)}px; display:flex; align-items:center; gap:18px; padding:16px 30px 16px 20px;
                border-radius:999px; background:rgba(63,216,234,.16); border:3px solid {C('accent')}; font-family:'{fonts['mono']}', monospace;
                font-weight:700; font-size:34px; color:{C('ink')}; }}
              #{oid} svg {{ width:44px; height:44px; display:block; }}""")
            dom.append(f'<div id="{oid}"><svg viewBox="0 0 44 44"><circle cx="22" cy="22" r="20" fill="{C("accent")}"/>'
                       f'<path d="M12 23 L19 30 L32 15" fill="none" stroke="{spec.theme["bg"]}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                       f'<span>{esc(ov["text"])}</span></div>')
            js.append(f'tl.fromTo("#{oid}", {{ opacity:0, y:30, scale:.9 }}, {{ opacity:1, y:0, scale:1, duration:.45, ease:"back.out(2)" }}, {T(ov.get("at")):.3f});')
        elif kind == "stats":
            _stats(ov, oid, css, dom, js, C, T, fonts)
        elif kind == "chips":
            _chips(ov, oid, css, dom, js, C, T, fonts)
        elif kind == "image":
            _image(ov, oid, css, dom, js, T)
        elif kind == "cta":
            css.append(f"""#{oid} {{ position:absolute; left:50%; top:{ov.get('top', 1178)}px; transform-origin:50% 50%; display:flex; align-items:center; gap:18px;
                padding:26px 44px; border-radius:999px; background:{C('accent')}; color:{spec.theme['bg']}; font-family:'{fonts['caption']}', sans-serif;
                font-weight:900; font-size:42px; white-space:nowrap; box-shadow:0 12px 50px rgba(63,216,234,.45); }}
              #{oid} svg {{ width:44px; height:44px; display:block; }}""")
            dom.append(f'<div id="{oid}"><span>{esc(ov["text"])}</span><svg viewBox="0 0 44 44"><path d="M6 22 H36 M24 10 L37 22 L24 34" fill="none" '
                       f'stroke="{spec.theme["bg"]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
            t = T(ov.get("at"))
            js.append(f'tl.fromTo("#{oid}", {{ opacity:0, xPercent:-50, y:40, scale:.9 }}, {{ opacity:1, xPercent:-50, y:0, scale:1, duration:.5, ease:"back.out(2)" }}, {t:.3f});')
            if ov.get("pulse", True):
                reps = max(0, math.floor((d - t - 0.6) / 0.5) - 1)
                js.append(f'tl.to("#{oid}", {{ scale:1.05, duration:.5, ease:"sine.inOut", yoyo:true, repeat:{reps} }}, {t + 0.6:.3f});')

    if cam_layer:  # overlays that must track the plate but sit above the scrims
        top_dom.insert(0, f'<div class="cam" id="{sid}-cam2" data-layout-allow-overflow><div class="drift" id="{sid}-drift2">{"".join(cam_layer)}</div></div>')
        camera_tweens(f"{sid}-cam2", f"{sid}-drift2")

    return f"""<!doctype html>
<html lang="{esc(spec.brief.get('language', 'en'))}">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template id="{sid}-template">
      <style>{''.join(css)}
      </style>
      <div id="{sid}" data-composition-id="{sid}" data-width="{spec.width}" data-height="{spec.height}" data-duration="{d}">
        {''.join(dom)}{''.join(top_dom)}
      </div>
      <script>
        (function () {{
          const tl = gsap.timeline({{ paused: true }});
          {chr(10).join('          ' + line for line in js).lstrip()}
          window.__timelines["{sid}"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
"""


def _headline(ov, oid, dom, js, C, T, d):
    text, anim = str(ov["text"]), ov.get("anim", "rise")
    top, size, col = ov.get("top", 292), ov.get("size", 110), C(ov.get("color"), "ink")
    plate = " hl-plate" if ov.get("plate") else ""  # dark backing for text over busy/light footage (not ".plate": that is the scene image)
    t_in = T(ov.get("at"), 0.3)
    if anim in ("mono", "type"):
        inner = esc(text) if anim == "mono" else f'<span id="{oid}-txt"></span><span class="caret" id="{oid}-caret"></span>'
        dom.append(f'<div class="hl mono{plate}" id="{oid}" style="top:{top}px; font-size:{size}px; color:{col};">{inner}</div>')
    elif anim == "glitch":
        fs, t = fit(text, size), esc(text)
        dom.append(f'<div class="hl{plate}" id="{oid}" style="top:{top}px; font-size:{fs}px; color:{col};"><div class="gl" id="{oid}-gl">'
                   f'<span data-layout-allow-overlap>{t}</span><span data-layout-allow-overlap>{t}</span><strong data-layout-allow-overlap>{t}</strong></div></div>')
    else:
        dom.append(f'<div class="hl{plate}" id="{oid}" style="top:{top}px; font-size:{fit(text, size)}px; color:{col};">{esc(text)}</div>')

    t_out = T(ov["out"]) if ov.get("out") is not None else None
    if anim == "slam":
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0, scale:1.32, filter:"blur(10px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:.34, ease:"power4.out" }}, {t_in:.3f});')
    elif anim == "snap":
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0, x:-140 }}, {{ opacity:1, x:0, duration:.42, ease:"expo.out" }}, {t_in:.3f});')
    elif anim == "rise":
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0, y:70 }}, {{ opacity:1, y:0, duration:.5, ease:"power3.out" }}, {t_in:.3f});')
    elif anim == "mono":
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0, x:-24 }}, {{ opacity:1, x:0, duration:.35, ease:"power2.out" }}, {t_in:.3f});')
    elif anim == "type":
        span = (t_out or d) - t_in
        blinks = max(0, math.floor(span / 0.56) * 2 - 1)
        js.append(f"""(function(){{ const full = {json.dumps(text)}; const el = document.getElementById("{oid}-txt"); const p = {{ n:0 }};
            el.textContent = "";
            tl.fromTo(p, {{ n:0 }}, {{ n:full.length, duration:{min(1.1, span * 0.6):.2f}, ease:"none", onUpdate(){{ el.textContent = full.slice(0, Math.round(p.n)); }} }}, {t_in:.3f});
            tl.fromTo("#{oid}-caret", {{ opacity:1 }}, {{ opacity:0, duration:.28, ease:"steps(1)", yoyo:true, repeat:{blinks} }}, {t_in:.3f});
          }})();""")
    elif anim == "glitch":
        reps = max(0, math.floor((d - t_in - 0.6) / 0.4) - 1)
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0, scale:1.18 }}, {{ opacity:1, scale:1, duration:.18, ease:"power4.out" }}, {t_in:.3f});')
        for n, sign in ((1, -1), (2, 1)):
            js.append(f'tl.fromTo("#{oid}-gl span:nth-child({n})", {{ x:0 }}, {{ x:{14 * sign}, duration:.05, ease:"steps(1)", yoyo:true, repeat:9 }}, {t_in:.3f});')
            js.append(f'tl.fromTo("#{oid}-gl span:nth-child({n})", {{ x:{-3 * sign} }}, {{ x:{3 * sign}, duration:.4, ease:"sine.inOut", yoyo:true, '
                      f'repeat:{reps}, immediateRender:false }}, {t_in + 0.55:.3f});')
    if t_out is not None:
        js.append(f'tl.to("#{oid}", {{ opacity:0, y:-20, duration:.22, ease:"power2.in" }}, {t_out:.3f});')


def _callouts(ov, oid, css, cam_layer, js, C, T, fonts):
    css.append(f"""#{oid} .box {{ position:absolute; border-radius:18px; box-shadow:0 0 0 3px {C('accent')}, 0 0 38px 8px {C('accent')}88, inset 0 0 40px {C('accent')}55; }}
      #{oid} .dim {{ position:absolute; border-radius:18px; background:rgba(4,10,24,.55); }}
      #{oid} .lab {{ position:absolute; display:flex; flex-direction:column; justify-content:center; padding:0 {ov.get('pad', 40)}px; box-sizing:border-box; transform-origin:30% 50%; }}
      #{oid} .idx {{ font-family:'{fonts['mono']}', monospace; font-weight:700; font-size:24px; letter-spacing:.14em; color:{C('accent')}; }}
      #{oid} .nm {{ font-family:'{fonts['display']}', sans-serif; font-size:{ov.get('title_size', 46)}px; line-height:1.02; letter-spacing:-0.02em; color:#ffffff; text-shadow:0 2px 14px rgba(0,10,30,.9); }}
      #{oid} .sub {{ margin-top:8px; font-family:'{fonts['mono']}', monospace; font-weight:700; font-size:24px; color:{C('warm')}; text-shadow:0 2px 10px rgba(0,10,30,.9); }}""")
    parts = [f'<div id="{oid}">']
    for k, b in enumerate(ov["boxes"]):
        geo = f'left:{b["x"]}px; top:{b["y"]}px; width:{b["w"]}px; height:{b["h"]}px;'
        name = esc(b["title"]) + (f"<br>{esc(b['title2'])}" if b.get("title2") else "")
        parts.append(f'<div class="dim" id="{oid}-dim{k}" style="{geo}"></div><div class="box" id="{oid}-box{k}" style="{geo}"></div>'
                     f'<div class="lab" id="{oid}-lab{k}" style="{geo}">'
                     + (f'<div class="idx">{esc(b["index"])}</div>' if b.get("index") else "")
                     + f'<div class="nm">{name}</div>' + (f'<div class="sub">{esc(b["sub"])}</div>' if b.get("sub") else "") + "</div>")
        t = T(b.get("at"), 0.3 + k * 0.8)
        js.append(f'tl.fromTo("#{oid}-dim{k}", {{ opacity:0 }}, {{ opacity:1, duration:.3, ease:"power2.out" }}, {t - 0.05:.3f});')
        js.append(f'tl.fromTo("#{oid}-box{k}", {{ opacity:0 }}, {{ opacity:1, duration:.12, ease:"power2.out" }}, {t - 0.05:.3f});')
        js.append(f'tl.to("#{oid}-box{k}", {{ opacity:.45, duration:.7, ease:"power2.inOut" }}, {t + 0.25:.3f});')
        js.append(f'tl.fromTo("#{oid}-lab{k}", {{ opacity:0, scale:.82 }}, {{ opacity:1, scale:1, duration:.45, ease:"back.out(2.2)" }}, {t:.3f});')
        if ov.get("confirm_at") is not None:
            js.append(f'tl.to("#{oid}-box{k}", {{ opacity:1, duration:.15, ease:"power2.out" }}, {T(ov["confirm_at"]) + k * 0.06:.3f});')
    parts.append("</div>")
    cam_layer.append("".join(parts))


def _flow(ov, oid, css, dom, js, C, T, fonts):
    arrow_col = C(ov.get("arrow_color"), "warm")
    css.append(f"""#{oid} {{ position:absolute; left:80px; top:{ov.get('top', 300)}px; width:940px; display:flex; align-items:center; gap:22px;
        font-family:'{fonts['display']}', sans-serif; font-size:{ov.get('size', 100)}px; line-height:1; letter-spacing:-0.03em; text-transform:uppercase; }}
      #{oid} .tok {{ display:block; }}
      #{oid} .arr {{ display:block; width:70px; height:70px; }}""")
    arrow = (f'<svg class="arr" viewBox="0 0 70 70"><path d="M8 35 H56 M38 17 L58 35 L38 53" fill="none" stroke="{arrow_col}" '
             f'stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    parts = [f'<div id="{oid}">']
    for k, tok in enumerate(ov["tokens"]):
        t = T(tok.get("at"), 0.3 + k * 0.5)
        if k:
            parts.append(f'<span id="{oid}-a{k}">{arrow}</span>')
            js.append(f'tl.fromTo("#{oid}-a{k}", {{ opacity:0, x:-30 }}, {{ opacity:1, x:0, duration:.3, ease:"expo.out" }}, {max(0, t - 0.15):.3f});')
        parts.append(f'<span class="tok" id="{oid}-t{k}" style="color:{C(tok.get("color"), "ink")}">{esc(tok["text"])}</span>')
        js.append(f'tl.fromTo("#{oid}-t{k}", {{ opacity:0, scale:1.4 }}, {{ opacity:1, scale:1, duration:.3, ease:"power4.out" }}, {t:.3f});')
    parts.append("</div>")
    dom.append("".join(parts))


# ====================================================================== captions
def caption_words(shot: dict, p: dict, shot_start: float) -> list[dict]:
    """Script tokens (with punctuation) aligned 1:1 to TTS words when counts match, else raw TTS words."""
    toks = (shot.get("vo") or "").split()
    words = p["words"]
    texts = toks if len(toks) == len(words) else [w["text"] for w in words]
    return [{"text": tx, "start": round(shot_start + w["s"], 3), "end": round(shot_start + w["e"], 3)} for tx, w in zip(texts, words)]


def captions_html(spec, timeline: list[dict]) -> str:
    cfg = spec.captions
    keywords = {norm_word(k): spec.color(v) for k, v in (cfg.get("keywords") or {}).items()}
    groups = []
    for shot, p in zip(spec.shots, timeline):
        zone = shot.get("captions", cfg["zone"])
        if zone == "off" or not p["words"]:
            continue
        limit = cfg["max_words"] if zone == "bottom" else max(2, cfg["max_words"] - 1)
        max_chars = 24 if zone == "bottom" else 18
        words, cur = caption_words(shot, p, p["start"]), []
        for i, w in enumerate(words):
            cur.append(w)
            nxt = words[i + 1] if i + 1 < len(words) else None
            if (nxt is None or re.search(r"[,.:!?]$", w["text"]) or nxt["start"] - w["end"] > 0.25
                    or len(cur) >= limit or sum(len(x["text"]) + 1 for x in cur) > max_chars):
                groups.append((zone, cur))
                cur = []
    total = sum(p["dur"] for p in timeline)
    dom, js = [], []
    for gi, (zone, g) in enumerate(groups):
        nxt = groups[gi + 1][1] if gi + 1 < len(groups) else None
        start = max(0, g[0]["start"] - 0.05)
        end = min(nxt[0]["start"] - 0.05, g[-1]["end"] + 0.35) if nxt else min(total, g[-1]["end"] + 0.5)
        spans = []
        for wi, w in enumerate(g):
            spans.append(f'<span class="w" id="cw-{gi}-{wi}">{esc(w["text"])}</span>')
            active = keywords.get(norm_word(w["text"]), "#FFFFFF")
            js.append(f'tl.fromTo("#cw-{gi}-{wi}", {{ color:"#8FA6BD" }}, {{ color:"{active}", duration:.08, ease:"none", immediateRender:false }}, {max(start, w["start"] - 0.04):.3f});')
        dom.append(f'<div class="grp {zone}" id="cg-{gi}"><div class="pill">{" ".join(spans)}</div></div>')
        js.append(f'tl.set("#cg-{gi}", {{ opacity:1 }}, {start:.3f});')
        js.append(f'tl.fromTo("#cg-{gi} .pill", {{ scale:.92, y:10 }}, {{ scale:1, y:0, duration:.16, ease:"power2.out", immediateRender:false }}, {start:.3f});')
        js.append(f'tl.set("#cg-{gi}", {{ opacity:0 }}, {end:.3f});')
    font = spec.theme["fonts"]["caption"]
    return f"""<!doctype html>
<html lang="{esc(spec.brief.get('language', 'en'))}">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template id="captions-template">
      <style>
        #captions {{ position:absolute; inset:0; pointer-events:none; }}
        #captions .grp {{ position:absolute; opacity:0; display:flex; }}
        #captions .grp.bottom {{ left:80px; width:920px; top:1318px; height:190px; align-items:center; justify-content:center; }}
        #captions .grp.top-right {{ left:470px; width:540px; top:236px; height:260px; align-items:flex-start; justify-content:flex-end; }}
        #captions .pill {{ display:block; max-width:100%; box-sizing:border-box; padding:14px 34px 16px; border-radius:22px; text-align:center;
          background:rgba(6,14,32,.82); border:2px solid rgba(63,216,234,.35); transform-origin:50% 50%;
          font-family:'{font}', sans-serif; font-weight:700; font-size:52px; line-height:1.18; color:#8FA6BD; }}
        #captions .grp.top-right .pill {{ font-size:44px; text-align:right; }}
        #captions .w {{ display:inline-block; }}
      </style>
      <div id="captions" data-composition-id="captions" data-width="{spec.width}" data-height="{spec.height}" data-duration="{total}">
        {''.join(dom)}
      </div>
      <script>
        (function () {{
          const tl = gsap.timeline({{ paused: true }});
          {chr(10).join('          ' + line for line in js).lstrip()}
          window.__timelines["captions"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
"""


# ====================================================================== index
def index_html(spec, timeline: list[dict], audio: dict) -> str:
    """audio = {"music": src|None, "voice": [{id, src, start, dur}], "sfx": [{id, src, start, dur, vol}]}"""
    total = sum(p["dur"] for p in timeline)
    hosts = "".join(
        f'\n      <div id="el-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
        f'data-start="{_num(p["start"])}" data-duration="{p["dur"]}" data-track-index="1" data-width="{spec.width}" data-height="{spec.height}"></div>'
        for sid, p in ((f"s-{p['id']}".replace("_", "-"), p) for p in timeline))
    tracks = ""
    if audio.get("music"):
        tracks += (f'\n      <audio id="bgm" src="{audio["music"]}" data-start="0" data-duration="{total}" data-track-index="11" '
                   f'data-volume="{spec.audio["music_volume"]}"></audio>')
    for v in audio["voice"]:
        tracks += f'\n      <audio id="{v["id"]}" src="{v["src"]}" data-start="{_num(v["start"])}" data-duration="{v["dur"]}" data-track-index="10" data-volume="1"></audio>'
    lanes: list[float] = []
    for s in sorted(audio["sfx"], key=lambda s: s["start"]):
        lane = next((i for i, end in enumerate(lanes) if end <= s["start"]), None)
        if lane is None:
            lanes.append(0.0)
            lane = len(lanes) - 1
        lanes[lane] = s["start"] + s["dur"]
        extra = f' data-media-start="{s["media_start"]}"' if s.get("media_start") else ""
        tracks += (f'\n      <audio id="{s["id"]}" src="{s["src"]}" data-start="{_num(s["start"])}" data-duration="{s["dur"]}"{extra} '
                   f'data-track-index="{14 + lane}" data-volume="{s["vol"]}"></audio>')
    grain = "".join(f'tl.set("#grain-tex", {{ x:{((k * 73) % 200) - 100}, y:{((k * 151) % 200) - 100} }}, {k / 12:.4f});' for k in range(int(total * 12)))
    bg = spec.theme["bg"]
    return f"""<!doctype html>
<html lang="{esc(spec.brief.get('language', 'en'))}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={spec.width}, height={spec.height}" />
    <title>{esc(spec.project)}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      body {{ margin:0; background:{bg}; }}
      #root {{ position:relative; width:100%; height:100%; overflow:hidden; background:{bg}; }}
      #root > div[data-composition-src] {{ position:absolute; inset:0; }}
      #grain {{ position:absolute; inset:0; pointer-events:none; overflow:hidden; opacity:.10; mix-blend-mode:overlay; }}
      #grain-tex {{ position:absolute; left:-200px; top:-200px; width:{spec.width + 400}px; height:{spec.height + 400}px;
        background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }}
      #vignette {{ position:absolute; inset:0; pointer-events:none; background:radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 55%, rgba(2,6,16,.55) 100%); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="{spec.width}" data-height="{spec.height}" data-duration="{total}">{hosts}
      <div id="vignette" data-layout-ignore></div>
      <div id="grain" data-layout-ignore><div id="grain-tex"></div></div>
      <div id="el-captions" data-track-kind="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{total}" data-track-index="3" data-width="{spec.width}" data-height="{spec.height}"></div>{tracks}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {grain}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def _stats(ov, oid, css, dom, js, C, T, fonts):
    cols = ov.get("columns", 2)
    size = ov.get("size", 88)
    plate = "background:rgba(6,12,26,.80); border-radius:22px; padding:26px 32px;" if ov.get("plate", True) else ""
    css.append(f"""#{oid} {{ position:absolute; left:80px; top:{ov.get('top', 900)}px; width:920px; box-sizing:border-box; {plate}
        display:grid; grid-template-columns:repeat({cols}, 1fr); gap:18px 24px; }}
      #{oid} .st {{ display:flex; flex-direction:column; transform-origin:0 50%; }}
      #{oid} .num {{ font-family:'{fonts['display']}', sans-serif; font-size:{size}px; line-height:1; letter-spacing:-0.02em;
          color:{C(ov.get('color'), 'accent')}; font-variant-numeric:tabular-nums; white-space:nowrap; }}
      #{oid} .lbl {{ margin-top:6px; font-family:'{fonts['mono']}', monospace; font-weight:700; font-size:28px; letter-spacing:.08em;
          text-transform:uppercase; color:{C('ink')}; }}""")
    parts = [f'<div id="{oid}">']
    for k, it in enumerate(ov["items"]):
        pre, suf = esc(it.get("prefix", "")), esc(it.get("suffix", ""))
        parts.append(f'<div class="st" id="{oid}-s{k}"><div class="num">{pre}<span id="{oid}-n{k}">{it["value"]}</span>{suf}</div>'
                     f'<div class="lbl">{esc(it.get("label", ""))}</div></div>')
        t = T(it.get("at"), 0.3 + k * 0.6)
        js.append(f'tl.fromTo("#{oid}-s{k}", {{ opacity:0, y:40 }}, {{ opacity:1, y:0, duration:.4, ease:"power3.out" }}, {t:.3f});')
        js.append(f"""(function(){{ const el = document.getElementById("{oid}-n{k}"); const p = {{ v:0 }}; el.textContent = "0";
            tl.fromTo(p, {{ v:0 }}, {{ v:{float(it['value'])}, duration:{it.get('count', 0.9)}, ease:"power2.out",
              immediateRender:false, onUpdate(){{ el.textContent = Math.round(p.v).toLocaleString("id-ID"); }} }}, {t:.3f}); }})();""")
    if ov.get("plate", True):
        first = min(T(it.get("at"), 0.3) for it in ov["items"])
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0 }}, {{ opacity:1, duration:.3, ease:"power2.out" }}, {max(0, first - 0.15):.3f});')
    parts.append("</div>")
    dom.append("".join(parts))


def _chips(ov, oid, css, dom, js, C, T, fonts):
    size = ov.get("size", 38)
    css.append(f"""#{oid} {{ position:absolute; left:80px; top:{ov.get('top', 960)}px; width:920px; display:flex; flex-wrap:wrap; gap:16px; }}
      #{oid} .chip {{ display:block; padding:14px 26px 16px; border-radius:999px; background:rgba(6,12,26,.84); border:3px solid {C('accent')};
          font-family:'{fonts['caption']}', sans-serif; font-weight:900; font-size:{size}px; line-height:1.1; color:{C('ink')};
          white-space:nowrap; transform-origin:0 50%; box-shadow:0 8px 30px rgba(0,0,0,.35); }}""")
    parts = [f'<div id="{oid}">']
    for k, it in enumerate(ov["items"]):
        col = C(it.get("color"), "ink")
        parts.append(f'<span class="chip" id="{oid}-c{k}" style="color:{col}">{esc(it["text"])}</span>')
        js.append(f'tl.fromTo("#{oid}-c{k}", {{ opacity:0, scale:.7 }}, {{ opacity:1, scale:1, duration:.4, ease:"back.out(2.4)" }}, {T(it.get("at"), 0.3 + k * 0.5):.3f});')
    parts.append("</div>")
    dom.append("".join(parts))


def _image(ov, oid, css, dom, js, T):
    w = ov.get("w", 420)
    left = f"calc(50% - {w / 2}px)" if ov.get("x", "center") == "center" else f"{ov['x']}px"
    plate = "background:rgba(6,12,26,.80); border-radius:24px; padding:28px 36px;" if ov.get("plate") else ""
    css.append(f"#{oid} {{ position:absolute; left:{left}; top:{ov.get('top', 960)}px; width:{w}px; {plate} box-sizing:content-box; transform-origin:50% 50%; }}"
               f"#{oid} img {{ display:block; width:100%; height:auto; }}")
    dom.append(f'<div id="{oid}"><img src="{ov["_src"]}" alt="" /></div>')
    t = T(ov.get("at"), 0.3)
    if ov.get("anim", "pop") == "pop":
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0, scale:.6 }}, {{ opacity:1, scale:1, duration:.55, ease:"back.out(2)" }}, {t:.3f});')
    else:
        js.append(f'tl.fromTo("#{oid}", {{ opacity:0, y:50 }}, {{ opacity:1, y:0, duration:.5, ease:"power3.out" }}, {t:.3f});')
