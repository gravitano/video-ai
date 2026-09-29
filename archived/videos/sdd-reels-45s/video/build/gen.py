"""Generate the SDD Reels composition (index.html, scene sub-comps, captions, STORYBOARD.md).

Timing source of truth: transcript.json (edge-tts word boundaries) + SCENES below.
Run from the project root:  python3 build/gen.py
"""
import json, math, pathlib, re, subprocess


def media_dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return round(float(out), 3)

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H, TOTAL = 1080, 1920, 45

NAVY, INK, CYAN, AMBER, RED = "#0A1428", "#EAF4F8", "#3FD8EA", "#FFB35C", "#FF5A68"

# VO line placement (global seconds) — matches transcript.json offsets.
VO_STARTS = [0.4, 4.3, 9.4, 15.3, 20.6, 25.0, 33.2, 39.0]

SCRIPT = [
    "AI sekarang bisa nulis kode secepat kilat.",
    "Tinggal ketik prompt, ratusan baris kode langsung jadi. Tapi...",
    "AI nggak tahu apa yang sebenarnya kamu mau. Hasilnya? Error.",
    "Makin cepat kamu nge-prompt, makin cepat juga kamu bikin hal yang salah.",
    "Solusinya: sebelum coding, tulis spec dulu.",
    "Spec itu berisi requirement, alur, aturan bisnis, dan kriteria terima. Jelas apa yang dibangun, dan kapan dianggap selesai.",
    "Lalu AI mengimplementasikan spec itu, langkah demi langkah, dan tiap langkah bisa kamu cek.",
    "Itulah Spec Driven Development. Coba di proyek berikutnya: spec dulu, baru coding.",
]


def fit(text, size, width=920, k=0.80):
    """Largest size <= `size` whose estimated Archivo Black caps width fits `width`."""
    return int(min(size, width / (k * max(1, len(text)))))


# ---------------------------------------------------------------- scene specs
# lines: (text, top, size, color, t_in, anim, t_out|None)   anim: slam|snap|rise|glitch|mono
SCENES = [
    dict(n=1, name="hook", start=0, dur=4, img="01_hook.png", hud="01 — HOOK", hudc=CYAN,
         cam=(1.12, 1.24, 0, 0, 0, -12, "45% 42%"),
         lines=[("AI CODING", 292, 124, INK, 1.2, "slam", None),
                ("= CEPAT", 424, 124, CYAN, 1.66, "slam", None)],
         fx="glow", glow=("78%", "44%", CYAN)),
    dict(n=2, name="setup", start=4, dur=5, img="02_setup.png", hud="02 — SETUP", hudc=CYAN,
         cam=(1.12, 1.12, 44, -44, 0, 0, "50% 45%"),
         lines=[("> ai.generate(code)", 300, 44, CYAN, 0.25, "type", 3.55),
                ("TAPI...", 292, 170, AMBER, 3.77, "snap", None)],
         fx="bars", glow=("60%", "38%", CYAN)),
    dict(n=3, name="problem", start=9, dur=6, img="03_problem.png", hud="03 — PROBLEM", hudc=RED,
         cam=(1.10, 1.18, 0, 0, 0, 0, "58% 38%"),
         lines=[("AI NGGAK TAHU", 292, 104, INK, 0.9, "rise", 4.5),
                ("MAUMU", 410, 104, RED, 1.8, "rise", 4.5),
                ("ERROR", 300, 210, RED, 4.6, "glitch", None)],
         fx="red", pulses=[(0.2, 0.30), (2.4, 0.30), (4.6, 0.55)], shake=4.6, glow=("80%", "34%", RED)),
    dict(n=4, name="escalation", start=15, dur=5, img="04_escalation.png", hud="04 — ESCALATION", hudc=RED,
         cam=(1.26, 1.04, 0, 0, 0, 0, "50% 55%"), camEase="power2.out",
         lines=[("MAKIN CEPAT", 292, 118, INK, 0.62, "snap", None),
                ("MAKIN SALAH", 420, 118, RED, 3.0, "glitch", None)],
         fx="red", pulses=[(0.1, 0.25), (1.4, 0.3), (2.6, 0.35), (3.0, 0.5), (4.0, 0.4)],
         shake=3.0, flashOut=True, glow=("30%", "30%", RED)),
    dict(n=5, name="solution", start=20, dur=5, img="05_solution.png", hud="05 — SOLUTION", hudc=CYAN,
         cam=(1.04, 1.14, 0, 0, 0, 0, "50% 50%"),
         lines=[("SOLUSINYA:", 300, 44, CYAN, 0.65, "mono", None),
                ("TULIS", 372, 150, INK, 2.6, "rise", None),
                ("SPEC DULU", 520, 150, CYAN, 2.88, "slam", None)],
         fx="bloom", flashIn=True, glow=("50%", "46%", CYAN)),
    dict(n=6, name="spec", start=25, dur=8, img="06_spec.png", hud="06 — HOW IT WORKS", hudc=CYAN,
         cam=(1.03, 1.07, 0, 0, 0, 0, "62% 55%"), lines=[], fx="spec", glow=("62%", "55%", CYAN)),
    dict(n=7, name="transform", start=33, dur=6, img="07_transform.png", hud="07 — TRANSFORM", hudc=CYAN,
         cam=(1.08, 1.14, -26, 26, 0, 0, "40% 55%"), lines=[], fx="flow", glow=("45%", "62%", CYAN)),
    dict(n=8, name="result", start=39, dur=6, img="08_result.png", hud="SPEC DRIVEN DEVELOPMENT", hudc=CYAN,
         hudAt=0.43, cam=(1.04, 1.12, 0, 0, 0, 0, "60% 40%"),
         lines=[("SPEC DULU,", 300, 132, INK, 3.86, "slam", None),
                ("BARU CODING.", 436, 132, CYAN, 4.77, "slam", None)],
         fx="cta", glow=("25%", "30%", AMBER)),
]

# Spec board module boxes (keyframe 06 resized to 1080x1920): x, y, w, h
SPEC_BOXES = [(420, 547, 490, 228), (420, 820, 490, 220), (420, 1088, 490, 217), (420, 1345, 490, 235)]
SPEC_LABELS = [("01", "REQUIREMENT", None, "requirement", 0.78),
               ("02", "FLOW", None, "alur", 1.66),
               ("03", "RULES", None, "aturan bisnis", 2.32),
               ("04", "ACCEPTANCE", "CRITERIA", "kriteria terima", 3.54)]


def scene_html(s):
    sid = f"s{s['n']:02d}"
    d = s["dur"]
    s0, s1, x0, x1, y0, y1, origin = s["cam"]
    css, dom, js = [], [], []

    # ---------------- base layers
    css.append(f"""
      #{sid} {{ position:absolute; inset:0; overflow:hidden; background:{NAVY}; color:{INK}; }}
      #{sid} .cam {{ position:absolute; inset:0; transform-origin:{origin}; will-change:transform; }}
      #{sid} .drift {{ position:absolute; inset:0; will-change:transform; }}
      #{sid} .shake {{ position:absolute; inset:0; }}
      #{sid} .plate {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; display:block; }}
      #{sid} .glow {{ position:absolute; left:{s['glow'][0]}; top:{s['glow'][1]}; width:900px; height:900px; margin:-450px 0 0 -450px;
                      border-radius:50%; background:radial-gradient(circle, {s['glow'][2]}55 0%, {s['glow'][2]}00 65%); mix-blend-mode:screen; }}
      #{sid} .scrim-top {{ position:absolute; left:0; top:0; width:100%; height:860px;
                      background:linear-gradient(180deg, rgba(6,12,26,.90) 0%, rgba(6,12,26,.62) 42%, rgba(6,12,26,0) 100%); }}
      #{sid} .scrim-bot {{ position:absolute; left:0; bottom:0; width:100%; height:820px;
                      background:linear-gradient(0deg, rgba(6,12,26,.88) 0%, rgba(6,12,26,.45) 45%, rgba(6,12,26,0) 100%); }}
      #{sid} .hud {{ position:absolute; left:80px; top:228px; display:flex; align-items:center; gap:18px;
                      font-family:'JetBrains Mono', monospace; font-weight:700; font-size:26px; letter-spacing:.14em; color:{s['hudc']}; }}
      #{sid} .hud .rule {{ display:block; width:110px; height:3px; background:{s['hudc']}; transform-origin:0 50%; }}
      #{sid} .hl {{ position:absolute; left:80px; width:940px; font-family:'Archivo Black', sans-serif; text-transform:uppercase;
                      line-height:1; letter-spacing:-0.03em; white-space:nowrap; transform-origin:0 50%; }}
      #{sid} .hl.mono {{ font-family:'JetBrains Mono', monospace; font-weight:700; text-transform:none; letter-spacing:0; }}
      #{sid} .hl .caret {{ display:inline-block; width:.55em; height:1em; margin-left:.08em; vertical-align:-0.12em; background:{CYAN}; }}
      #{sid} .gl {{ position:relative; display:block; width:940px; }}
      #{sid} .gl span, #{sid} .gl strong {{ position:absolute; left:0; top:0; font-weight:400; }}
      #{sid} .gl strong {{ position:relative; }}
      #{sid} .gl span:nth-child(1) {{ color:#ff2d55; mix-blend-mode:screen; }}
      #{sid} .gl span:nth-child(2) {{ color:#22e1ff; mix-blend-mode:screen; }}
    """)
    dom.append(f"""
      <div class="cam" id="{sid}-cam" data-layout-allow-overflow><div class="drift" id="{sid}-drift"><div class="shake" id="{sid}-shake">
        <img class="plate" src="assets/keyframes/{s['img']}" alt="" />
      </div></div></div>
      <div class="glow" id="{sid}-glow" data-layout-ignore></div>
      {{FX_LAYERS}}
      <div class="scrim-top" data-layout-ignore></div>
      <div class="scrim-bot" data-layout-ignore></div>
      <div class="hud" id="{sid}-hud"><span class="rule" id="{sid}-rule"></span><span id="{sid}-hudtxt">{s['hud']}</span></div>
      {{CAM_EXTRA}}
      {{TOP_FX}}
    """)
    ease = s.get("camEase", "sine.inOut")
    js.append(f"""
      tl.fromTo("#{sid}-cam", {{ scale:{s0}, x:{x0}, y:{y0} }}, {{ scale:{s1}, x:{x1}, y:{y1}, duration:{d}, ease:"{ease}" }}, 0);
      tl.fromTo("#{sid}-drift", {{ scale:1.02, x:-7, y:5 }}, {{ scale:1.02, x:7, y:-5, duration:{d/2:.3f}, ease:"sine.inOut", yoyo:true, repeat:1 }}, 0);
      tl.fromTo("#{sid}-glow", {{ opacity:.55, scale:.9 }}, {{ opacity:.95, scale:1.08, duration:{d/2:.3f}, ease:"sine.inOut", yoyo:true, repeat:1 }}, 0);
      tl.fromTo("#{sid}-rule", {{ scaleX:0 }}, {{ scaleX:1, duration:.45, ease:"expo.out" }}, {s.get('hudAt', 0.08)});
      tl.fromTo("#{sid}-hudtxt", {{ opacity:0, x:-16 }}, {{ opacity:1, x:0, duration:.4, ease:"power3.out" }}, {s.get('hudAt', 0.08) + 0.12:.2f});
    """)

    cam_extra, fx_layers, top_fx = "", "", ""

    # ---------------- headlines
    for i, (text, top, size, color, t_in, anim, t_out) in enumerate(s["lines"]):
        lid = f"{sid}-l{i}"
        if anim in ("mono", "type"):
            inner = text if anim == "mono" else f'<span id="{lid}-txt"></span><span class="caret" id="{lid}-caret"></span>'
            dom.append(f'<div class="hl mono" id="{lid}" style="top:{top}px; font-size:{size}px; color:{color};">{inner}</div>')
        elif anim == "glitch":
            fs = fit(text, size)
            dom.append(f'<div class="hl" id="{lid}" style="top:{top}px; font-size:{fs}px; color:{color};">'
                       f'<div class="gl" id="{lid}-gl"><span data-layout-allow-overlap>{text}</span><span data-layout-allow-overlap>{text}</span><strong data-layout-allow-overlap>{text}</strong></div></div>')
        else:
            fs = fit(text, size)
            dom.append(f'<div class="hl" id="{lid}" style="top:{top}px; font-size:{fs}px; color:{color};">{text}</div>')

        if anim == "slam":
            js.append(f'tl.fromTo("#{lid}", {{ opacity:0, scale:1.32, filter:"blur(10px)" }}, {{ opacity:1, scale:1, filter:"blur(0px)", duration:.34, ease:"power4.out" }}, {t_in});')
        elif anim == "snap":
            js.append(f'tl.fromTo("#{lid}", {{ opacity:0, x:-140 }}, {{ opacity:1, x:0, duration:.42, ease:"expo.out" }}, {t_in});')
        elif anim == "rise":
            js.append(f'tl.fromTo("#{lid}", {{ opacity:0, y:70 }}, {{ opacity:1, y:0, duration:.5, ease:"power3.out" }}, {t_in});')
        elif anim == "mono":
            js.append(f'tl.fromTo("#{lid}", {{ opacity:0, x:-24 }}, {{ opacity:1, x:0, duration:.35, ease:"power2.out" }}, {t_in});')
        elif anim == "type":
            # discrete typing: one char per step, seek-safe via onUpdate from a proxy
            js.append(f"""
      (function(){{ const full = {json.dumps(text)}; const el = document.getElementById("{lid}-txt"); const p = {{ n:0 }};
        el.textContent = "";
        tl.fromTo(p, {{ n:0 }}, {{ n:full.length, duration:1.1, ease:"none", onUpdate(){{ el.textContent = full.slice(0, Math.round(p.n)); }} }}, {t_in});
        const caret = document.getElementById("{lid}-caret");
        tl.fromTo(caret, {{ opacity:1 }}, {{ opacity:0, duration:.28, ease:"steps(1)", yoyo:true, repeat:{max(0, math.floor(((t_out or d) - t_in) / 0.56) * 2 - 1)} }}, {t_in});
      }})();""")
            js.append(f'tl.set("#{lid}", {{ opacity:1 }}, 0);')
        elif anim == "glitch":
            js.append(f"""
      tl.fromTo("#{lid}", {{ opacity:0, scale:1.18 }}, {{ opacity:1, scale:1, duration:.18, ease:"power4.out" }}, {t_in});
      tl.fromTo("#{lid}-gl span:nth-child(1)", {{ x:0 }}, {{ x:-14, duration:.05, ease:"steps(1)", yoyo:true, repeat:9 }}, {t_in});
      tl.fromTo("#{lid}-gl span:nth-child(2)", {{ x:0 }}, {{ x:14, duration:.05, ease:"steps(1)", yoyo:true, repeat:9 }}, {t_in});
      tl.fromTo("#{lid}-gl span:nth-child(1)", {{ x:-3 }}, {{ x:3, duration:.4, ease:"sine.inOut", yoyo:true, repeat:{max(0, math.floor((d - t_in - 0.6) / 0.4) - 1)}, immediateRender:false }}, {t_in + 0.55:.2f});
      tl.fromTo("#{lid}-gl span:nth-child(2)", {{ x:3 }}, {{ x:-3, duration:.4, ease:"sine.inOut", yoyo:true, repeat:{max(0, math.floor((d - t_in - 0.6) / 0.4) - 1)}, immediateRender:false }}, {t_in + 0.55:.2f});""")
        if t_out is not None:
            js.append(f'tl.to("#{lid}", {{ opacity:0, y:-20, duration:.22, ease:"power2.in" }}, {t_out});')

    # ---------------- scene-specific effects
    fx = s["fx"]
    if fx == "red":
        css.append(f"""#{sid} .redwash {{ position:absolute; inset:0; background:radial-gradient(ellipse at 60% 40%, rgba(255,40,60,.55) 0%, rgba(120,0,20,.35) 55%, rgba(40,0,10,.5) 100%); mix-blend-mode:multiply; }}
      #{sid} .redglow {{ position:absolute; inset:0; background:radial-gradient(circle at 70% 30%, rgba(255,60,80,.5), rgba(255,60,80,0) 60%); mix-blend-mode:screen; }}""")
        fx_layers += f'<div class="redwash" id="{sid}-wash" data-layout-ignore></div><div class="redglow" id="{sid}-rg" data-layout-ignore></div>'
        js.append(f'tl.fromTo("#{sid}-wash", {{ opacity:.25 }}, {{ opacity:.6, duration:{d}, ease:"none" }}, 0);')
        pulses = s["pulses"]
        for k, (t, a) in enumerate(pulses):
            nxt = pulses[k + 1][0] if k + 1 < len(pulses) else d
            fade = max(0.1, min(0.6, nxt - t - 0.2))
            js.append(f'tl.fromTo("#{sid}-rg", {{ opacity:0 }}, {{ opacity:{a}, duration:.16, ease:"power2.out", immediateRender:{"true" if k == 0 else "false"} }}, {t});')
            js.append(f'tl.to("#{sid}-rg", {{ opacity:0, duration:{fade:.2f}, ease:"power2.in" }}, {t + 0.17:.2f});')
        if "shake" in s:
            t = s["shake"]
            offs = [(-14, 6), (12, -8), (-9, 10), (8, -5), (-5, 4), (3, -2), (0, 0)]
            for k, (sx, sy) in enumerate(offs):
                js.append(f'tl.set("#{sid}-shake", {{ x:{sx}, y:{sy} }}, {t + k * 0.045:.3f});')
    if s.get("flashOut"):
        css.append(f"#{sid} .flash {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 45%, #ffffff 0%, #bff6ff 45%, {CYAN} 100%); }}")
        top_fx += f'<div class="flash" id="{sid}-flash" data-layout-ignore></div>'
        js.append(f'tl.fromTo("#{sid}-flash", {{ opacity:0 }}, {{ opacity:1, duration:.22, ease:"power1.in" }}, {d - 0.22:.2f});')
    if s.get("flashIn"):
        css.append(f"#{sid} .flash {{ position:absolute; inset:0; background:radial-gradient(circle at 50% 45%, #ffffff 0%, #bff6ff 45%, {CYAN} 100%); }}")
        top_fx += f'<div class="flash" id="{sid}-flash" data-layout-ignore></div>'
        js.append(f'tl.fromTo("#{sid}-flash", {{ opacity:1 }}, {{ opacity:0, duration:.45, ease:"power2.out" }}, 0.08);')
    if fx == "bloom":
        css.append(f"#{sid} .bloom {{ position:absolute; left:50%; top:47%; width:1300px; height:700px; margin:-350px 0 0 -650px; border-radius:50%; background:radial-gradient(ellipse, {CYAN}66 0%, {CYAN}00 70%); mix-blend-mode:screen; }}")
        fx_layers += f'<div class="bloom" id="{sid}-bloom" data-layout-ignore></div>'
        js.append(f'tl.fromTo("#{sid}-bloom", {{ opacity:0, scale:.7 }}, {{ opacity:.9, scale:1, duration:1.6, ease:"power2.out" }}, .2);')
        js.append(f'tl.to("#{sid}-bloom", {{ opacity:.55, duration:1.2, ease:"sine.inOut", yoyo:true, repeat:1 }}, 1.8);')
    if fx == "bars":
        # abstract generated-code bars cascading beside the typed prompt
        css.append(f"""#{sid} .bars {{ position:absolute; left:80px; top:372px; width:560px; display:flex; flex-direction:column; gap:14px; }}
      #{sid} .bar {{ display:block; height:12px; border-radius:6px; background:{CYAN}; opacity:.85; transform-origin:0 50%; }}""")
        widths = [520, 380, 460, 300, 540, 410, 250, 480]
        bars = "".join(f'<span class="bar" id="{sid}-b{k}" style="width:{w}px"></span>' for k, w in enumerate(widths))
        dom.append(f'<div class="bars" id="{sid}-bars">{bars}</div>')
        for k in range(len(widths)):
            js.append(f'tl.fromTo("#{sid}-b{k}", {{ scaleX:0 }}, {{ scaleX:1, duration:.3, ease:"power3.out" }}, {1.35 + k * 0.22:.2f});')
        js.append(f'tl.to("#{sid}-bars", {{ opacity:0, y:-20, duration:.22, ease:"power2.in" }}, 3.55);')
    if fx == "spec":
        css.append(f"""#{sid} .box {{ position:absolute; border-radius:18px; box-shadow:0 0 0 3px {CYAN}, 0 0 38px 8px {CYAN}88, inset 0 0 40px {CYAN}55; }}
      #{sid} .lab {{ position:absolute; display:flex; flex-direction:column; justify-content:center; padding:0 40px; box-sizing:border-box; transform-origin:30% 50%; }}
      #{sid} .lab .idx {{ font-family:'JetBrains Mono', monospace; font-weight:700; font-size:24px; letter-spacing:.14em; color:{CYAN}; }}
      #{sid} .lab .nm {{ font-family:'Archivo Black', sans-serif; font-size:46px; line-height:1.02; letter-spacing:-0.02em; color:#ffffff; text-shadow:0 2px 14px rgba(0,10,30,.9); }}
      #{sid} .lab .sub {{ margin-top:8px; font-family:'JetBrains Mono', monospace; font-weight:700; font-size:24px; color:{AMBER}; text-shadow:0 2px 10px rgba(0,10,30,.9); }}
      #{sid} .dim {{ position:absolute; border-radius:18px; background:rgba(4,10,24,.55); }}""")
        for k, ((bx, by, bw, bh), (idx, nm, nm2, sub, t)) in enumerate(zip(SPEC_BOXES, SPEC_LABELS)):
            name = nm if not nm2 else f"{nm}<br>{nm2}"
            cam_extra += (f'<div class="dim" id="{sid}-dim{k}" style="left:{bx}px; top:{by}px; width:{bw}px; height:{bh}px;"></div>'
                          f'<div class="box" id="{sid}-box{k}" style="left:{bx}px; top:{by}px; width:{bw}px; height:{bh}px;"></div>'
                          f'<div class="lab" id="{sid}-lab{k}" style="left:{bx}px; top:{by}px; width:{bw}px; height:{bh}px;">'
                          f'<div class="idx">{idx}</div><div class="nm">{name}</div><div class="sub">{sub}</div></div>')
            js.append(f'tl.fromTo("#{sid}-box{k}", {{ opacity:0 }}, {{ opacity:1, duration:.12, ease:"power2.out" }}, {t - 0.05:.2f});')
            js.append(f'tl.to("#{sid}-box{k}", {{ opacity:.45, duration:.7, ease:"power2.inOut" }}, {t + 0.25:.2f});')
            js.append(f'tl.fromTo("#{sid}-lab{k}", {{ opacity:0, scale:.82 }}, {{ opacity:1, scale:1, duration:.45, ease:"back.out(2.2)" }}, {t:.2f});')
            js.append(f'tl.fromTo("#{sid}-dim{k}", {{ opacity:0 }}, {{ opacity:1, duration:.3, ease:"power2.out" }}, {t - 0.05:.2f});')
            # all four confirm together on "selesai"
            js.append(f'tl.to("#{sid}-box{k}", {{ opacity:1, duration:.15, ease:"power2.out" }}, {7.28 + k * 0.06:.2f});')
    if fx == "flow":
        css.append(f"""#{sid} .row {{ position:absolute; left:80px; top:300px; width:940px; display:flex; align-items:center; gap:22px;
                      font-family:'Archivo Black', sans-serif; font-size:100px; line-height:1; letter-spacing:-0.03em; text-transform:uppercase; }}
      #{sid} .tok {{ display:block; }}
      #{sid} .arr {{ display:block; width:70px; height:70px; }}
      #{sid} .chk {{ position:absolute; left:80px; top:440px; display:flex; align-items:center; gap:18px; padding:16px 30px 16px 20px; border-radius:999px;
                      background:rgba(63,216,234,.16); border:3px solid {CYAN}; font-family:'JetBrains Mono', monospace; font-weight:700; font-size:34px; color:{INK}; }}
      #{sid} .chk svg {{ width:44px; height:44px; display:block; }}""")
        arrow = f'<svg class="arr" viewBox="0 0 70 70"><path d="M8 35 H56 M38 17 L58 35 L38 53" fill="none" stroke="{AMBER}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        dom.append(f'<div class="row"><span class="tok" id="{sid}-t0" style="color:{CYAN}">SPEC</span>'
                   f'<span id="{sid}-a0">{arrow}</span><span class="tok" id="{sid}-t1" style="color:{INK}">AI</span>'
                   f'<span id="{sid}-a1">{arrow}</span><span class="tok" id="{sid}-t2" style="color:{INK}">APP</span></div>'
                   f'<div class="chk" id="{sid}-chk"><svg viewBox="0 0 44 44"><circle cx="22" cy="22" r="20" fill="{CYAN}"/>'
                   f'<path d="M12 23 L19 30 L32 15" fill="none" stroke="{NAVY}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                   f'<span>tiap langkah bisa dicek</span></div>')
        for el, t, a in [("t0", 0.3, "slam"), ("a0", 0.45, "snap"), ("t1", 0.5, "slam"), ("a1", 2.05, "snap"), ("t2", 2.2, "slam")]:
            if a == "slam":
                js.append(f'tl.fromTo("#{sid}-{el}", {{ opacity:0, scale:1.4 }}, {{ opacity:1, scale:1, duration:.3, ease:"power4.out" }}, {t});')
            else:
                js.append(f'tl.fromTo("#{sid}-{el}", {{ opacity:0, x:-30 }}, {{ opacity:1, x:0, duration:.3, ease:"expo.out" }}, {t});')
        js.append(f'tl.fromTo("#{sid}-chk", {{ opacity:0, y:30, scale:.9 }}, {{ opacity:1, y:0, scale:1, duration:.45, ease:"back.out(2)" }}, 4.45);')
    if fx == "cta":
        css.append(f"""#{sid} .cta {{ position:absolute; left:50%; top:1178px; transform-origin:50% 50%; display:flex; align-items:center; gap:18px; padding:26px 44px; border-radius:999px;
                      background:{CYAN}; color:{NAVY}; font-family:'Montserrat', sans-serif; font-weight:900; font-size:42px; white-space:nowrap; box-shadow:0 12px 50px rgba(63,216,234,.45); }}
      #{sid} .cta svg {{ width:44px; height:44px; display:block; }}""")
        dom.append(f'<div class="cta" id="{sid}-cta"><span>Coba di proyek berikutnya</span>'
                   f'<svg viewBox="0 0 44 44"><path d="M6 22 H36 M24 10 L37 22 L24 34" fill="none" stroke="{NAVY}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')
        js.append(f'tl.fromTo("#{sid}-cta", {{ opacity:0, xPercent:-50, y:40, scale:.9 }}, {{ opacity:1, xPercent:-50, y:0, scale:1, duration:.5, ease:"back.out(2)" }}, 2.42);')
        js.append(f'tl.to("#{sid}-cta", {{ scale:1.05, duration:.5, ease:"sine.inOut", yoyo:true, repeat:3 }}, 3.0);')

    if cam_extra:
        # overlay camera: same transforms as the plate camera, but stacked above the scrims
        cam_extra = (f'<div class="cam" id="{sid}-cam2" data-layout-allow-overflow><div class="drift" id="{sid}-drift2">'
                     f'{cam_extra}</div></div>')
        js.append(f"""
      tl.fromTo("#{sid}-cam2", {{ scale:{s0}, x:{x0}, y:{y0} }}, {{ scale:{s1}, x:{x1}, y:{y1}, duration:{d}, ease:"{ease}" }}, 0);
      tl.fromTo("#{sid}-drift2", {{ scale:1.02, x:-7, y:5 }}, {{ scale:1.02, x:7, y:-5, duration:{d/2:.3f}, ease:"sine.inOut", yoyo:true, repeat:1 }}, 0);""")
    html = f"""<!doctype html>
<html lang="id">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template id="{sid}-template">
      <style>{''.join(css)}
      </style>
      <div id="{sid}" data-composition-id="{sid}" data-width="{W}" data-height="{H}" data-duration="{d}">
        {''.join(dom).replace('{CAM_EXTRA}', cam_extra).replace('{FX_LAYERS}', fx_layers).replace('{TOP_FX}', top_fx)}
      </div>
      <script>
        (function () {{
          const tl = gsap.timeline({{ paused: true }});
          {''.join(js)}
          window.__timelines["{sid}"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
"""
    return sid, html


# ---------------------------------------------------------------- captions
KEYWORDS = {"spec": CYAN, "error": RED, "salah": RED, "development": CYAN}


def caption_words():
    words = json.loads((ROOT / "transcript.json").read_text())
    out = []
    for line_idx, text in enumerate(SCRIPT, 1):
        toks = text.split()
        lw = [w for w in words if w["line"] == line_idx]
        assert len(toks) == len(lw), (line_idx, toks, [w["text"] for w in lw])
        for tok, w in zip(toks, lw):
            out.append(dict(text=tok, start=w["start"], end=w["end"], line=line_idx))
    return out


def caption_groups(words):
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        chars = sum(len(x["text"]) + 1 for x in cur)
        limit = 3 if w["line"] == 6 else 4
        if (nxt is None or nxt["line"] != w["line"] or re.search(r"[,.:!?]$", w["text"])
                or nxt["start"] - w["end"] > 0.25 or len(cur) >= limit or chars > (18 if w["line"] == 6 else 24)):
            groups.append(cur)
            cur = []
    return groups


def captions_html():
    groups = caption_groups(caption_words())
    dom, js = [], []
    for gi, g in enumerate(groups):
        nxt = groups[gi + 1] if gi + 1 < len(groups) else None
        start = max(0, g[0]["start"] - 0.05)
        end = min(nxt[0]["start"] - 0.05, g[-1]["end"] + 0.35) if nxt else min(TOTAL, g[-1]["end"] + 0.5)
        zone = "top" if g[0]["line"] == 6 else "bot"
        spans = []
        for wi, w in enumerate(g):
            spans.append(f'<span class="w" id="cw-{gi}-{wi}">{w["text"]}</span>')
            key = re.sub(r"[^a-z]", "", w["text"].lower())
            active = KEYWORDS.get(key, "#FFFFFF")
            js.append(f'tl.fromTo("#cw-{gi}-{wi}", {{ color:"#8FA6BD" }}, {{ color:"{active}", duration:.08, ease:"none", immediateRender:false }}, {max(start, w["start"] - 0.04):.3f});')
        dom.append(f'<div class="grp {zone}" id="cg-{gi}"><div class="pill">{" ".join(spans)}</div></div>')
        js.append(f'tl.set("#cg-{gi}", {{ opacity:1 }}, {start:.3f});')
        js.append(f'tl.fromTo("#cg-{gi} .pill", {{ scale:.92, y:10 }}, {{ scale:1, y:0, duration:.16, ease:"power2.out", immediateRender:false }}, {start:.3f});')
        js.append(f'tl.set("#cg-{gi}", {{ opacity:0 }}, {end:.3f});')
    return f"""<!doctype html>
<html lang="id">
  <head><meta charset="UTF-8" /></head>
  <body>
    <template id="captions-template">
      <style>
        #captions {{ position:absolute; inset:0; pointer-events:none; }}
        #captions .grp {{ position:absolute; opacity:0; display:flex; }}
        #captions .grp.bot {{ left:80px; width:920px; top:1318px; height:190px; align-items:center; justify-content:center; }}
        #captions .grp.top {{ left:470px; width:540px; top:236px; height:260px; align-items:flex-start; justify-content:flex-end; }}
        #captions .pill {{ display:block; max-width:100%; box-sizing:border-box; padding:14px 34px 16px; border-radius:22px; text-align:center;
                           background:rgba(6,14,32,.82); border:2px solid rgba(63,216,234,.35); transform-origin:50% 50%;
                           font-family:'Montserrat', sans-serif; font-weight:700; font-size:52px; line-height:1.18; color:#8FA6BD; }}
        #captions .grp.top .pill {{ font-size:44px; text-align:right; }}
        #captions .w {{ display:inline-block; }}
      </style>
      <div id="captions" data-composition-id="captions" data-width="{W}" data-height="{H}" data-duration="{TOTAL}">
        {''.join(dom)}
      </div>
      <script>
        (function () {{
          const tl = gsap.timeline({{ paused: true }});
          {''.join(js)}
          window.__timelines["captions"] = tl;
        }})();
      </script>
    </template>
  </body>
</html>
"""


# ---------------------------------------------------------------- audio + index
SFX = [  # (t, file, volume)
    (0.05, "typing", .45), (1.5, "typing", .4), (1.15, "whoosh-short", .5), (1.6, "impact-bass-2", .3),
    (4.0, "whoosh-short", .4), (4.35, "key-press", .5), (5.35, "sparkle", .3), (7.72, "whoosh", .55),
    (9.0, "glitch-1", .35), (13.55, "error", .5), (13.6, "glitch-2", .35),
    (15.0, "glitch-1", .35), (17.95, "impact-bass-1", .5),
    (19.9, "impact-bass-2", .55), (22.85, "chime", .45),
    (25.0, "whoosh-short", .4), (25.78, "click", .55), (26.66, "click", .55), (27.32, "click", .55), (28.54, "click", .55), (32.25, "sparkle", .35),
    (33.0, "whoosh", .45), (33.3, "pop", .4), (33.5, "pop", .4), (35.2, "pop", .4), (37.45, "ping", .45),
    (39.0, "whoosh-short", .4), (39.45, "sparkle", .35), (41.42, "pop", .45), (42.85, "impact-bass-2", .35), (43.77, "chime", .4),
]


def index_html(scenes):
    hosts = "".join(
        f'\n      <div id="el-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" '
        f'data-start="{s["start"]}" data-duration="{s["dur"]}" data-track-index="1" data-width="{W}" data-height="{H}"></div>'
        for sid, s in scenes)
    vo = "".join(
        f'\n      <audio id="vo-{i:02d}" src="assets/vo/vo_{i:02d}.wav" data-start="{t}" data-duration="{media_dur(ROOT / f"assets/vo/vo_{i:02d}.wav")}" data-track-index="10" data-volume="1"></audio>'
        for i, t in enumerate(VO_STARTS, 1))
    lanes, sfx = [], ""
    for k, (t, f, v) in sorted(enumerate(SFX), key=lambda kv: kv[1][0]):
        dur = min(media_dur(ROOT / f"assets/audio/{f}.mp3"), TOTAL - t)
        lane = next((i for i, end in enumerate(lanes) if end <= t), None)
        if lane is None:
            lanes.append(0); lane = len(lanes) - 1
        lanes[lane] = t + dur
        sfx += f'\n      <audio id="sfx-{k:02d}" src="assets/audio/{f}.mp3" data-start="{t}" data-duration="{dur}" data-track-index="{14 + lane}" data-volume="{v}"></audio>'

    # riser: last 5s of the 10s file, peaking into the flash at 20s
    sfx += '\n      <audio id="sfx-riser" src="assets/audio/riser.mp3" data-start="15" data-duration="5" data-media-start="5" data-track-index="13" data-volume="0.4"></audio>'
    grain = "".join(
        f'tl.set("#grain-tex", {{ x:{((k * 73) % 200) - 100}, y:{((k * 151) % 200) - 100} }}, {k / 12:.4f});'
        for k in range(TOTAL * 12))
    return f"""<!doctype html>
<html lang="id">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>SDD Reels 45s</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      body {{ margin:0; background:{NAVY}; }}
      #root {{ position:relative; width:100%; height:100%; overflow:hidden; background:{NAVY}; }}
      #root > div[data-composition-src] {{ position:absolute; inset:0; }}
      #grain {{ position:absolute; inset:0; pointer-events:none; overflow:hidden; opacity:.10; mix-blend-mode:overlay; }}
      #grain-tex {{ position:absolute; left:-200px; top:-200px; width:1480px; height:2320px;
        background:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }}
      #vignette {{ position:absolute; inset:0; pointer-events:none; background:radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 55%, rgba(2,6,16,.55) 100%); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="{W}" data-height="{H}" data-duration="{TOTAL}">{hosts}
      <div id="vignette" data-layout-ignore></div>
      <div id="grain" data-layout-ignore><div id="grain-tex"></div></div>
      <div id="el-captions" data-track-kind="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" data-duration="{TOTAL}" data-track-index="3" data-width="{W}" data-height="{H}"></div>
      <audio id="bgm" src="assets/audio/bgm.wav" data-start="0" data-duration="{TOTAL}" data-track-index="11" data-volume="0.55"></audio>{vo}{sfx}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {grain}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def storyboard(scenes):
    out = ["---", 'format: 1080x1920', 'message: "Tulis spec sebelum AI coding"', 'audience: "Developer dan vibe coder"', "mode: autonomous", "---", "", "# SDD Reels 45s — Storyboard", ""]
    for (sid, s), vo in zip(scenes, SCRIPT):
        cite = {"hook": "multi-phase-camera + kinetic-beat-slam", "setup": "multi-phase-camera + discrete-text-sequence + stat-bars-and-fills",
                "problem": "multi-phase-camera + chromatic-glitch", "escalation": "multi-phase-camera + chromatic-glitch",
                "solution": "multi-phase-camera + ambient-glow-bloom + kinetic-beat-slam", "spec": "multi-phase-camera + spring-pop-entrance",
                "transform": "multi-phase-camera + kinetic-beat-slam + spring-pop-entrance", "result": "multi-phase-camera + kinetic-beat-slam + spring-pop-entrance"}[s["name"]]
        out += [f"## Frame {s['n']} — {s['name'].title()}", "",
                f"- status: animated", f"- src: compositions/{sid}.html", f"- duration: {s['dur']}s",
                f"- transition_in: {'flash' if s['n'] == 5 else 'cut'}", f"- voiceover: \"{vo}\"", f"- rules: {cite}", ""]
    return "\n".join(out)


def main():
    comp = ROOT / "compositions"
    comp.mkdir(exist_ok=True)
    scenes = []
    for s in SCENES:
        sid, html = scene_html(s)
        (comp / f"{sid}.html").write_text(html)
        scenes.append((sid, s))
    (comp / "captions.html").write_text(captions_html())
    (ROOT / "index.html").write_text(index_html(scenes))
    (ROOT / "STORYBOARD.md").write_text(storyboard(scenes))
    assert sum(s["dur"] for s in SCENES) == TOTAL
    print("generated", len(scenes), "scenes")


if __name__ == "__main__":
    main()
