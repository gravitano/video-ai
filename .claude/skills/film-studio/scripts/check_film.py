#!/usr/bin/env python3
"""Validasi proyek film films/<slug>/ terhadap format di references/formats.md.

Pemakaian: python3 check_film.py films/<slug>
Exit code 1 kalau ada ERROR.
"""
import re
import sys
from pathlib import Path

from filmlib import (MODES, audio_native, generator_of, generator_profile, header_field, norm, norm_words,
                     parse_bible, parse_edit, parse_sections, parse_shotlist, parse_takes, read, spoken_lines)

WPS_WARN = 2.2  # kata per detik, bahasa Indonesia
WPS_ERROR = 2.7

findings = []


def report(level, where, msg):
    findings.append((level, where, msg))


def quoted_words(text):
    quotes = re.findall(r'"([^"]+)"', text) + re.findall(r"“([^”]+)”", text)
    return sum(len(q.split()) for q in quotes)


def lock_for(locks, kind, name):
    return locks.get(f"{kind}:{name}")


def require_locks(sid, prompt, shot, locks, what):
    p = norm(prompt)
    if "STYLE" in locks and locks["STYLE"] not in p:
        report("ERROR", sid, f"{what}: LOCK:STYLE tidak disalin verbatim")
    for c in shot["chars"]:
        lk = lock_for(locks, "CHAR", c)
        if lk and lk not in p:
            report("ERROR", sid, f"{what}: LOCK:CHAR:{c} tidak disalin verbatim")
    for loc in shot["locs"]:
        lk = lock_for(locks, "LOC", loc)
        if lk and lk not in p:
            report("ERROR", sid, f"{what}: LOCK:LOC:{loc} tidak disalin verbatim")


def check_words(sid, words, dur, what):
    if not words or not dur:
        return
    rate = words / dur
    if rate > WPS_ERROR:
        report("ERROR", sid, f"{what}: {words} kata dalam {dur:g} dtk ({rate:.1f} kata/dtk) — terlalu padat")
    elif rate > WPS_WARN:
        report("WARN", sid, f"{what}: {words} kata dalam {dur:g} dtk ({rate:.1f} kata/dtk) — mepet")


def main(root):
    bible_txt = read(root / "01-bible.md")
    if bible_txt is None:
        report("ERROR", "bible", "01-bible.md belum ada")
        return
    fields, locks = parse_bible(bible_txt)
    if "STYLE" not in locks:
        report("ERROR", "bible", "LOCK:STYLE tidak ditemukan")
    for f in ("Rasio", "Durasi target", "Batas klip", "Mode narasi"):
        if f not in fields:
            report("WARN", "bible", f"field '{f}' tidak ada di bagian Format")
    gen = generator_of(fields)
    prof = generator_profile(gen)
    if prof.stem != gen:
        report("INFO", "bible", f"generator '{gen}' belum punya profil — pakai references/generators/generic.md")
    native = audio_native(fields)
    target = float(fields.get("Durasi target", "0").split()[0] or 0)
    limit = float(fields.get("Batas klip", "8").split()[0])
    narr_sep = fields.get("Mode narasi", "in-video").lower().startswith("terpisah")
    ratio = fields.get("Rasio", "")
    if not native and not narr_sep:
        report("ERROR", "bible", "Audio native: tidak, jadi Mode narasi harus 'terpisah'")

    naskah_txt = read(root / "02-naskah.md")
    user_script = (header_field(naskah_txt, "Sumber") or "").lower() == "user"
    naskah_norm = norm_words(naskah_txt) if naskah_txt else None
    if user_script and "## Catatan AI" in naskah_txt:
        open_notes = [l for l in naskah_txt.split("## Catatan AI", 1)[1].splitlines()
                      if re.match(r"^\|\s*\d+\s*\|", l) and l.rstrip().rstrip("|").rsplit("|", 1)[-1].strip() in ("", "-")]
        if open_notes:
            report("WARN", "naskah", f"{len(open_notes)} usulan di 'Catatan AI' belum diputuskan user")
    char_names = {k.split(":", 1)[1] for k in locks if k.startswith("CHAR:")}
    loc_names = {k.split(":", 1)[1] for k in locks if k.startswith("LOC:")}

    sl_txt = read(root / "03-shotlist.md")
    if sl_txt is None:
        report("INFO", "shotlist", "03-shotlist.md belum ada — cek berhenti di bible")
        return
    shots = parse_shotlist(sl_txt, report)
    if not shots:
        report("ERROR", "shotlist", "tidak ada baris shot (| Sxx | ...)")
        return

    seen = set()
    for n, s in enumerate(shots, 1):
        sid = s["id"]
        if sid in seen:
            report("ERROR", sid, "ID shot duplikat")
        seen.add(sid)
        if sid != f"S{n:02d}":
            report("WARN", sid, f"urutan ID tidak berurutan (harusnya S{n:02d})")
        if s["mode"] not in MODES:
            report("ERROR", sid, f"mode '{s['mode']}' tidak valid ({', '.join(sorted(MODES))})")
        if s["dur"] > limit:
            report("ERROR", sid, f"durasi {s['dur']:g} dtk melebihi batas klip {limit:g} dtk")
        for c in s["chars"]:
            if c not in char_names:
                report("ERROR", sid, f"karakter '{c}' tidak ada LOCK:CHAR di bible")
        for loc in s["locs"]:
            if loc not in loc_names:
                report("ERROR", sid, f"lokasi '{loc}' tidak ada LOCK:LOC di bible")
        check_words(sid, quoted_words(s["audio"]), s["dur"], "audio shot list")

    total = sum(s["dur"] for s in shots)
    if target:
        diff = abs(total - target) / target
        level = "ERROR" if diff > 0.10 else ("WARN" if diff > 0.05 else "INFO")
        report(level, "shotlist", f"total {total:g} dtk vs target {target:g} dtk ({len(shots)} shot)")
    by_id = {s["id"]: s for s in shots}

    kf_txt = read(root / "04-keyframes.md")
    if kf_txt is not None:
        kf = parse_sections(kf_txt)
        for s in shots:
            sid = s["id"]
            if s["mode"] != "Frames":
                continue
            prompts = kf.get(sid)
            if not prompts:
                report("ERROR", sid, "shot mode Frames tapi tidak ada prompt keyframe di 04")
                continue
            require_locks(sid, prompts[0], s, locks, "keyframe")
            low = prompts[0].lower()
            if "no text" not in low:
                report("WARN", sid, "keyframe: tidak ada 'No text'")
            if ratio and ratio not in prompts[0]:
                report("WARN", sid, f"keyframe: rasio {ratio} tidak disebut")
        for sid in kf:
            if sid not in by_id:
                report("WARN", sid, "ada di 04-keyframes tapi tidak ada di shot list")

    mo_txt = read(root / "05-motion.md")
    if mo_txt is not None:
        mo = parse_sections(mo_txt)
        from filmlib import split_sections
        mo_sections = split_sections(mo_txt)
        for s in shots:
            sid = s["id"]
            prompts = mo.get(sid)
            if not prompts:
                report("ERROR", sid, "tidak ada prompt motion di 05")
                continue
            p = prompts[0]
            low = p.lower()
            if s["mode"] in ("Ingredients", "Text"):
                require_locks(sid, p, s, locks, f"motion ({s['mode']})")
            check_words(sid, quoted_words(p), s["dur"], "dialog/narasi prompt")
            if "subtitle" not in low:
                report("WARN", sid, "motion: tidak ada 'No subtitles'")
            if narr_sep and "narrator" in low and "no voice-over" not in low:
                report("ERROR", sid, "mode narasi 'terpisah' tapi prompt berisi narrator")
            if not native:
                if re.search(r"\bsays\b[^\"“]*[\"“]", p) or ("narrator" in low and "no voice-over" not in low):
                    report("ERROR", sid, "Audio native: tidak, tapi prompt berisi dialog/narasi — pindahkan ke 'Dialog terpisah:'")
                elif "no dialogue" not in low:
                    report("WARN", sid, "motion: klip bisu tanpa 'no dialogue'")
            if naskah_norm is not None:
                body = mo_sections[sid][1] if sid in mo_sections else p
                for line in spoken_lines(body):
                    if norm_words(line) not in naskah_norm:
                        report("ERROR" if user_script else "WARN", sid,
                               f"kalimat \"{line[:40]}…\" tidak ada di naskah" + (" (naskah milik user)" if user_script else ""))
            np = norm(p)
            for c in s["chars"]:
                voice = lock_for(locks, "VOICE", c)
                if voice and re.search(rf"\b{re.escape(c)}\b[^.\"]*\bsays\b", p) and voice not in np:
                    report("WARN", sid, f"motion: {c} bicara tapi LOCK:VOICE:{c} tidak disalin")
            nv = lock_for(locks, "VOICE", "Narator")
            if nv and "narrator" in low and not narr_sep and nv not in np:
                report("WARN", sid, "motion: narasi tanpa LOCK:VOICE:Narator")
        for sid in mo:
            if sid not in by_id:
                report("WARN", sid, "ada di 05-motion tapi tidak ada di shot list")

    edit_txt = read(root / "06-edit.md")
    if edit_txt is not None:
        edit, layers, errs = parse_edit(edit_txt)
        for where, msg in errs:
            report("ERROR", where, f"06-edit: {msg}")
        if not edit and not errs:
            report("WARN", "edit", "06-edit.md tidak punya baris di tabel 'Urutan edit'")
        for e in edit:
            if e["shot"] not in by_id:
                report("ERROR", e["shot"], "06-edit: shot tidak ada di shot list")
            elif not (root / "assets" / "clips" / f"{e['shot']}.mp4").exists():
                report("WARN", e["shot"], "06-edit: klip terpilih assets/clips/%s.mp4 belum ada" % e["shot"])
        for layer in layers:
            if not (root / layer["file"]).exists():
                report("WARN", "edit", f"lapisan audio {layer['file']} belum ada")
        takes = parse_takes(edit_txt)
        credits = sum(float(t["Kredit"].replace(",", ".")) for t in takes
                      if re.fullmatch(r"\d+([.,]\d+)?", t["Kredit"]))
        if takes:
            report("INFO", "edit", f"{len(takes)} take tercatat · kredit {credits:g}")

    assets = root / "assets"
    kfs = {p.stem for p in (assets / "keyframes").glob("S*.*")} if assets.exists() else set()
    clips = {p.stem for p in (assets / "clips").glob("S??.mp4")} if assets.exists() else set()
    need_kf = [s["id"] for s in shots if s["mode"] == "Frames"]
    report("INFO", "assets", f"keyframe {len([i for i in need_kf if i in kfs])}/{len(need_kf)} · "
                             f"klip terpilih {len([s for s in shots if s['id'] in clips])}/{len(shots)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Pemakaian: python3 check_film.py films/<slug>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        sys.exit(f"Folder tidak ditemukan: {root}")
    main(root)
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for level, where, msg in sorted(findings, key=lambda f: order[f[0]]):
        print(f"{level:5} [{where}] {msg}")
    errors = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    print(f"\n{errors} error, {warns} warning")
    sys.exit(1 if errors else 0)
