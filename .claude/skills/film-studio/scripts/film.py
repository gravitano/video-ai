#!/usr/bin/env python3
"""Alat produksi & edit untuk proyek films/<slug>/ (tahap 4–6).

  status   films/<slug>                         progres per shot + total kredit
  handoff  films/<slug> [--stage clips|keyframes] [--shots S01,S03] [--all]
                                                paket prompt + gambar untuk diunggah ke generator
  adopt    films/<slug> <folder> [--credits N] [--model M]
                                                ambil hasil unduhan (nama diawali Sxx) jadi take baru
  select   films/<slug> Sxx N [--keyframe]      jadikan take N sebagai versi terpilih
  frame    films/<slug> Sxx [--at DTK]          ambil satu frame klip terpilih (default frame terakhir)
  roughcut films/<slug> [nama] [--res 720] [--fps 24]
                                                rakit out/<nama>.mp4 dari tabel di 06-edit.md

Semua perintah tidak menghapus file; take lama tetap disimpan.
"""
import argparse
import filecmp
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from filmlib import (TAKE_COLS, audio_native, generator_of, generator_profile, parse_bible, parse_edit,
                     parse_shotlist, parse_takes, prompts_in, read, section, split_sections)

VIDEO_EXT = {".mp4", ".mov", ".webm", ".m4v"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


class Film:
    def __init__(self, root):
        self.root = Path(root)
        if not self.root.is_dir():
            sys.exit(f"Folder tidak ditemukan: {self.root}")
        bible = read(self.root / "01-bible.md")
        if bible is None:
            sys.exit("01-bible.md belum ada")
        self.fields, self.locks = parse_bible(bible)
        self.title = (re.search(r"^# .*?—\s*(.+)$", bible, re.M) or [None, self.root.name])[1].strip()
        self.generator = generator_of(self.fields)
        self.shots = parse_shotlist(read(self.root / "03-shotlist.md") or "")
        self.kf = split_sections(read(self.root / "04-keyframes.md") or "")
        self.mo = split_sections(read(self.root / "05-motion.md") or "")
        self.clips = self.root / "assets" / "clips"
        self.keyframes = self.root / "assets" / "keyframes"
        self.edit_path = self.root / "06-edit.md"

    def shot(self, sid):
        for s in self.shots:
            if s["id"] == sid:
                return s
        sys.exit(f"{sid} tidak ada di 03-shotlist.md")

    def keyframe(self, sid):
        found = sorted(p for p in self.keyframes.glob(f"{sid}.*") if p.suffix.lower() in IMAGE_EXT)
        return found[0] if found else None

    def refs(self, sid):
        """Ingredient yang disebut di baris 'Referensi:' 04-keyframes, sebagai path yang ada."""
        body = self.kf.get(sid, ("", ""))[1]
        m = re.search(r"Referensi:\s*(.+)", body)
        out = []
        for tok in (m.group(1).split(",") if m else []):
            name = tok.strip().split(" ")[0].strip("`")
            if not name or name == "-":
                continue
            for base in (self.root / "assets" / "ingredients", self.keyframes):
                hits = [p for p in base.glob(f"{Path(name).stem}.*") if p.suffix.lower() in IMAGE_EXT]
                if hits:
                    out.append(sorted(hits)[0])
                    break
            else:
                print(f"  ! {sid}: referensi '{name}' belum ada filenya")
        return out

    # ---------- 06-edit.md ----------

    def edit_text(self):
        txt = read(self.edit_path)
        if txt is None:
            txt = (f"# Edit — {self.title}\nStatus: draft\n\n## Urutan edit\n"
                   "| Shot | Potong video | Audio | Transisi | Catatan |\n|---|---|---|---|---|\n\n"
                   "## Lapisan audio\n| File | Mulai | Volume | Catatan |\n|---|---|---|---|\n\n")
        if "## Log take" not in txt:
            txt = txt.rstrip() + "\n\n## Log take\n| " + " | ".join(TAKE_COLS) + " |\n" + "|---" * len(TAKE_COLS) + "|\n"
        return txt

    def write_takes(self, rows):
        txt = self.edit_text()
        table = "| " + " | ".join(TAKE_COLS) + " |\n" + "|---" * len(TAKE_COLS) + "|\n"
        table += "".join("| " + " | ".join(r[c] for c in TAKE_COLS) + " |\n" for r in rows)
        body = section(txt, "Log take")
        notes = "\n".join(l for l in body.splitlines() if l.strip() and not l.lstrip().startswith("|"))
        new = "\n" + table + (("\n" + notes + "\n") if notes else "") + "\n"
        txt = txt.replace("## Log take\n" + body, "## Log take\n" + new.lstrip("\n"), 1) if body else \
            txt.replace("## Log take", "## Log take\n" + new.lstrip("\n"), 1)
        self.edit_path.write_text(txt.rstrip() + "\n", encoding="utf-8")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def probe(path, entry="format=duration"):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", entry, "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


def duration(path):
    return float(probe(path))


def has_audio(path):
    return "audio" in probe(path, "stream=codec_type")


# ---------- perintah ----------

def cmd_status(f, a):
    rows = parse_takes(read(f.edit_path) or "")
    edit, _, _ = parse_edit(read(f.edit_path) or "")
    in_edit = {e["shot"] for e in edit}
    print(f"{f.title} · generator {f.generator} ({generator_profile(f.generator).name})"
          f" · audio native {'ya' if audio_native(f.fields) else 'tidak'}\n")
    print(f"{'Shot':5} {'Mode':12} {'Dur':>4}  {'Keyframe':8} {'Take':>4}  {'Terpilih':8} Edit")
    for s in f.shots:
        sid = s["id"]
        need_kf = s["mode"] == "Frames"
        kf = "✓" if f.keyframe(sid) else ("·" if need_kf else "n/a")
        takes = len([r for r in rows if r["Shot"] == sid and r["Jenis"] == "klip"]) or \
            len(list(f.clips.glob(f"{sid}_t*.mp4")))
        sel = "✓" if (f.clips / f"{sid}.mp4").exists() else "·"
        print(f"{sid:5} {s['mode']:12} {s['dur']:>4g}  {kf:8} {takes:>4}  {sel:8} {'✓' if sid in in_edit else '·'}")
    credits = sum(float(r["Kredit"].replace(",", ".")) for r in rows if re.fullmatch(r"\d+([.,]\d+)?", r["Kredit"]))
    done = sum((f.clips / f"{s['id']}.mp4").exists() for s in f.shots)
    print(f"\nKlip terpilih {done}/{len(f.shots)} · take tercatat {len(rows)} · kredit {credits:g}")


def cmd_handoff(f, a):
    stage = a.stage
    only = set(a.shots.split(",")) if a.shots else None
    out = f.root / "handoff" / f.generator / stage
    (out / "downloads").mkdir(parents=True, exist_ok=True)
    (out / "refs").mkdir(exist_ok=True)
    rows, copied = [], set()

    def add_ref(p):
        if p.name not in copied:
            shutil.copyfile(p, out / "refs" / p.name)
            copied.add(p.name)
        return p.name

    if stage == "keyframes":
        ing = re.search(r"^## Ingredients\s*\n(.*?)(?=^## (?!#))", read(f.root / "04-keyframes.md") or "", re.S | re.M)
        for name, body in re.findall(r"^### (\S+)[^\n]*\n(.*?)(?=^### |\Z)", ing.group(1) if ing else "", re.S | re.M):
            ps = prompts_in(body)
            exists = any(p.suffix.lower() in IMAGE_EXT for p in (f.root / "assets" / "ingredients").glob(f"{name}.*"))
            if ps and (a.all or not exists):
                (out / f"{name}.txt").write_text(ps[0].strip() + "\n", encoding="utf-8")
                rows.append((name, "gambar", "-", "-", f"{name}.txt"))
    for s in f.shots:
        sid = s["id"]
        if only and sid not in only:
            continue
        if stage == "keyframes":
            if s["mode"] != "Frames" or (f.keyframe(sid) and not a.all):
                continue
            ps = prompts_in(f.kf.get(sid, ("", ""))[1])
            if not ps:
                print(f"  ! {sid}: tidak ada prompt di 04-keyframes.md")
                continue
            refs = [add_ref(p) for p in f.refs(sid)]
            (out / f"{sid}.txt").write_text(ps[0].strip() + "\n", encoding="utf-8")
            rows.append((sid, "keyframe", "-", ", ".join(refs) or "-", f"{sid}.txt"))
        else:
            if (f.clips / f"{sid}.mp4").exists() and not a.all:
                continue
            ps = prompts_in(f.mo.get(sid, ("", ""))[1])
            if not ps:
                print(f"  ! {sid}: tidak ada prompt di 05-motion.md")
                continue
            frame, refs = "-", []
            if s["mode"] == "Frames":
                kf = f.keyframe(sid)
                if kf:
                    shutil.copyfile(kf, out / f"{sid}{kf.suffix}")
                    frame = f"{sid}{kf.suffix}"
                else:
                    frame = "BELUM ADA"
            elif s["mode"] == "Ingredients":
                refs = [add_ref(p) for p in f.refs(sid)]
            (out / f"{sid}.txt").write_text(ps[0].strip() + "\n", encoding="utf-8")
            rows.append((sid, s["mode"], f"{s['dur']:g} dtk", frame if s["mode"] == "Frames" else (", ".join(refs) or "-"),
                         f"{sid}.txt"))
    if not rows:
        print("Tidak ada yang perlu di-handoff (pakai --all untuk menyertakan yang sudah selesai).")
        return
    prof = generator_profile(f.generator)
    model = f.fields.get("Model video", "-")
    lines = [f"# Handoff {stage} — {f.title} → {f.generator}", "",
             f"- Generator: **{f.generator}** · Model: {model} · Rasio: {f.fields.get('Rasio', '-')}"
             f" · Audio native: {'ya' if audio_native(f.fields) else 'tidak'}",
             f"- Panduan platform: `.claude/skills/film-studio/references/generators/{prof.name}`",
             "- Gambar referensi ada di `refs/`. Prompt ada di file `.txt`; tempel apa adanya (matikan prompt enhancer).", "",
             "| Item | Mode | Durasi | Frame awal / referensi | Prompt |", "|---|---|---|---|---|",
             *[f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | `{r[4]}` |" for r in rows], "",
             "## Setelah generate", "",
             f"1. Unduh hasil ke `downloads/`, **nama diawali ID** (`S03.mp4`, `S03-b.mp4`, `CHAR-Raka.png`).",
             "2. Dari root repo jalankan:", "", "```bash",
             f"python3 .claude/skills/film-studio/scripts/film.py adopt {f.root} {out / 'downloads'} --credits <kredit per take>",
             f"python3 .claude/skills/film-studio/scripts/film.py status {f.root}", "```",
             "3. Minta Claude me-review take, lalu `film.py select` untuk take terbaik."]
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK {out.relative_to(f.root)}/ · {len(rows)} item · {len(copied)} referensi")


def cmd_adopt(f, a):
    src = Path(a.folder)
    if not src.is_dir():
        sys.exit(f"Folder tidak ditemukan: {src}")
    rows = parse_takes(f.edit_text())
    seen = {(r["Shot"], r["Catatan"]) for r in rows}
    model = a.model or f.fields.get("Model video", "")
    added = 0
    known = sorted(set(re.findall(r"^### ((?:CHAR|LOC|PROP)-\S+)", read(f.root / "04-keyframes.md") or "", re.M))
                   | {q.stem for q in (f.root / "assets" / "ingredients").glob("*-*")}, key=len, reverse=True)
    for p in sorted(src.iterdir()):
        ext = p.suffix.lower()
        if ext not in VIDEO_EXT | IMAGE_EXT:
            continue
        m = re.match(r"^S\d+", p.name, re.I)
        if m:
            item = m.group(0).upper()
        else:
            item = next((k for k in known if p.stem == k or re.match(rf"{re.escape(k)}[-_ ]", p.stem)), None)
            m2 = re.match(r"^(?:CHAR|LOC|PROP)-[A-Za-z0-9]+", p.name)
            item = item or (m2.group(0) if m2 else None)
            if not item:
                continue
        note = f"dari {p.name}"
        if (item, note) in seen:
            continue
        if not item.startswith("S"):
            dst_dir = f.root / "assets" / "ingredients" / "_raw"
            kind, stem = "ingredient", item
        elif ext in VIDEO_EXT:
            dst_dir, kind, stem = f.clips, "klip", f"{item}_t"
        else:
            dst_dir, kind, stem = f.keyframes / "_raw", "keyframe", f"{item}_v"
        dst_dir.mkdir(parents=True, exist_ok=True)
        if kind == "ingredient":
            n = 1 + len([r for r in rows if r["Shot"] == item])
            dst = dst_dir / f"{item}_v{n}{ext}"
        else:
            nums = [int(mm.group(1)) for q in dst_dir.glob(f"{stem}*") if (mm := re.match(rf"{stem}(\d+)", q.name))]
            n = max(nums, default=0) + 1
            dst = dst_dir / f"{stem}{n}{'.mp4' if kind == 'klip' and ext == '.mp4' else ext}"
        if kind == "klip" and ext != ".mp4":
            ffmpeg("-i", p, "-c:v", "libx264", "-crf", "18", "-c:a", "aac", dst.with_suffix(".mp4"))
            dst = dst.with_suffix(".mp4")
        else:
            shutil.copyfile(p, dst)
        rows.append({"Shot": item, "Take": str(n), "Jenis": kind, "File": str(dst.relative_to(f.root)),
                     "Generator": f.generator, "Model": model, "Kredit": a.credits or "", "Status": "kandidat",
                     "Catatan": note})
        added += 1
        print(f"  + {item} take {n} ({kind}) ← {p.name}")
    if added:
        f.write_takes(rows)
    print(f"OK {added} take baru dicatat di 06-edit.md" if added else "Tidak ada file baru (nama harus diawali Sxx / CHAR- / LOC- / PROP-).")


def cmd_select(f, a):
    sid, n = a.shot.upper(), a.take
    rows = parse_takes(f.edit_text())
    kind = "keyframe" if a.keyframe else "klip"
    if not sid.startswith("S"):
        kind, sid = "ingredient", a.shot
    row = next((r for r in rows if r["Shot"] == sid and r["Jenis"] == kind and r["Take"] == str(n)), None)
    if row:
        src = f.root / row["File"]
    elif kind == "klip":
        src = f.clips / f"{sid}_t{n}.mp4"
    else:
        hits = list((f.keyframes / "_raw").glob(f"{sid}_v{n}.*"))
        src = hits[0] if hits else f.keyframes / "_raw" / f"{sid}_v{n}.jpg"
    if not src.exists():
        sys.exit(f"Take tidak ditemukan: {src}")
    if kind == "klip":
        dst = f.clips / f"{sid}.mp4"
        olds = [dst]
    else:
        base = f.keyframes if kind == "keyframe" else f.root / "assets" / "ingredients"
        dst = base / f"{sid}{src.suffix.lower()}"
        olds = [q for q in base.glob(f"{sid}.*") if q.suffix.lower() in IMAGE_EXT]
    takes = [f.root / r["File"] for r in rows if r["Shot"] == sid and r["Jenis"] == kind]
    for old in olds:
        if not old.exists() or any(t.exists() and filecmp.cmp(old, t, shallow=False) for t in takes + [src]):
            continue
        k = 1
        while (bak := old.with_name(f"{sid}_lama{k}{old.suffix}")).exists():
            k += 1
        old.rename(bak)
        print(f"  cadangan: {bak.relative_to(f.root)}")
    for old in olds:
        if old.exists() and old != dst:
            old.unlink()  # identik dengan salah satu take, jadi tidak ada yang hilang
    shutil.copyfile(src, dst)
    for r in rows:
        if r["Shot"] == sid and r["Jenis"] == kind:
            if r["Take"] == str(n):
                r["Status"] = "terpilih"
            elif r["Status"] == "terpilih":
                r["Status"] = "kandidat"
    if not row:
        rows.append({"Shot": sid, "Take": str(n), "Jenis": kind, "File": str(src.relative_to(f.root)),
                     "Generator": f.generator, "Model": "", "Kredit": "", "Status": "terpilih", "Catatan": ""})
    f.write_takes(rows)
    if kind == "klip":
        mo_path = f.root / "05-motion.md"
        txt = read(mo_path)
        if txt and sid in f.mo:
            _, body = f.mo[sid]
            m = re.search(r"^Take terpilih:\s*(.*)$", body, re.M)
            if m:
                old = m.group(1)
                keep = old.split(" — ", 1)[1] if old.startswith(f"{sid}_t{n}") and " — " in old else ""
                new_body = body.replace(m.group(0), f"Take terpilih: {sid}_t{n}" + (f" — {keep}" if keep else ""), 1)
                mo_path.write_text(txt.replace(body, new_body, 1), encoding="utf-8")
    print(f"OK {dst.relative_to(f.root)} ← {src.relative_to(f.root)}")


def cmd_frame(f, a):
    sid = a.shot.upper()
    clip = f.clips / f"{sid}.mp4"
    if not clip.exists():
        sys.exit(f"{clip} belum ada")
    at = a.at if a.at is not None else max(duration(clip) - 0.05, 0)
    out = Path(a.out) if a.out else f.keyframes / "_raw" / f"{sid}_frame_{at:.2f}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg("-ss", f"{at:.3f}", "-i", clip, "-frames:v", "1", "-q:v", "2", out)
    print(f"OK {out}")


def cmd_roughcut(f, a):
    edit_txt = read(f.edit_path)
    if edit_txt is None:
        sys.exit("06-edit.md belum ada — minta Claude menjalankan tahap film-edit")
    edit, layers, errs = parse_edit(edit_txt)
    for where, msg in errs:
        print(f"ERROR [{where}] {msg}")
    if errs or not edit:
        sys.exit("Perbaiki tabel 'Urutan edit' di 06-edit.md dulu")
    ratio = f.fields.get("Rasio", "9:16")
    short = a.res - a.res % 2
    w, h = (short, round(short * 16 / 9 / 2) * 2) if ratio.startswith("9") else (round(short * 16 / 9 / 2) * 2, short)
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={a.fps},format=yuv420p"
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    out_dir = f.root / "out"
    out_dir.mkdir(exist_ok=True)
    used, skipped = [], []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        segs, pending = [], 0.0
        for e in edit:
            sid, src = e["shot"], f.clips / f"{e['shot']}.mp4"
            if not src.exists():
                skipped.append(sid)
                pending = 0.0
                continue
            parts = e["video"] or [(0.0, duration(src))]
            total = sum(b - x for x, b in parts)
            vchain = "".join(f"[0:v]trim={x}:{b},setpts=PTS-STARTPTS,{vf}[v{i}];" for i, (x, b) in enumerate(parts))
            vchain += "".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]"
            inputs = ["-i", src]
            if e["audio"] == "mute" or not has_audio(src):
                inputs += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
                achain = "[1:a]anull[a]"
            elif e["audio"] == "klip":
                achain = "".join(f"[0:a]atrim={x}:{b},asetpts=PTS-STARTPTS[a{i}];" for i, (x, b) in enumerate(parts))
                achain += "".join(f"[a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[a]"
            else:
                x, b = e["audio"]
                achain = f"[0:a]atrim={x}:{b},asetpts=PTS-STARTPTS,apad,atrim=0:{total:.3f}[a]"
            seg = tmp / f"{len(segs):02d}_{sid}.mp4"
            ffmpeg(*inputs, "-filter_complex", vchain + ";" + achain, "-map", "[v]", "-map", "[a]", *enc, seg)
            if pending and segs:
                prev = segs.pop()
                off = duration(prev) - pending
                merged = tmp / f"x{len(segs):02d}_{sid}.mp4"
                ffmpeg("-i", prev, "-i", seg, "-filter_complex",
                       f"[0:v][1:v]xfade=transition=fade:duration={pending}:offset={off:.3f}[v];"
                       f"[0:a][1:a]acrossfade=d={pending}[a]", "-map", "[v]", "-map", "[a]", *enc, merged)
                seg = merged
            segs.append(seg)
            used.append(sid)
            pending = e["xfade"]
        if not segs:
            sys.exit("Belum ada klip terpilih (assets/clips/Sxx.mp4) untuk shot di urutan edit")
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{s}'\n" for s in segs))
        joined = tmp / "joined.mp4"
        ffmpeg("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined)
        total = duration(joined)
        fade = f"afade=t=out:st={max(total - 0.8, 0):.3f}:d=0.8"
        inputs, mix = ["-i", joined], "[0:a]anull[m0];"
        present = [l for l in layers if (f.root / l["file"]).exists()]
        for l in layers:
            if l not in present:
                print(f"  ! lapisan audio {l['file']} belum ada, dilewati")
        for i, l in enumerate(present, 1):
            inputs += ["-i", f.root / l["file"]]
            ms = int(l["start"] * 1000)
            mix += f"[{i}:a]adelay={ms}|{ms},volume={l['volume']}[m{i}];"
        mix += "".join(f"[m{i}]" for i in range(len(present) + 1))
        mix += f"amix=inputs={len(present) + 1}:normalize=0:duration=first[a]"
        mixed = tmp / "mixed.wav"
        ffmpeg(*inputs, "-filter_complex", mix, "-map", "[a]", "-ar", "48000", mixed)
        # loudnorm punya lookahead ±3 dtk; jangan digabung dengan filter video dalam satu filter_complex
        # (paket audio jadi melompat). -vf/-af terpisah aman.
        final = out_dir / f"{a.name}.mp4"
        ffmpeg("-i", joined, "-i", mixed, "-map", "0:v", "-map", "1:a",
               "-vf", f"fade=t=out:st={max(total - 0.8, 0):.3f}:d=0.8",
               "-af", f"loudnorm=I=-16:TP=-1.5:LRA=11,{fade}", "-shortest", *enc, final)
    review = f.root / "review"
    review.mkdir(exist_ok=True)
    strip = review / f"{a.name}-strip.jpg"
    n = 12
    ffmpeg("-i", final, "-vf", f"fps={n / duration(final):.5f},scale=-2:240,tile={n}x1", "-frames:v", "1", strip)
    print(f"OK {final.relative_to(f.root)} · {duration(final):.1f} dtk · {w}x{h} {a.fps} fps")
    print(f"Strip  : {strip.relative_to(f.root)}")
    print("Dipakai:", " ".join(used))
    print("Belum ada klip:", " ".join(skipped) or "-")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("status"); p.add_argument("film")
    p = sub.add_parser("handoff"); p.add_argument("film")
    p.add_argument("--stage", choices=["clips", "keyframes"], default="clips")
    p.add_argument("--shots", help="mis. S01,S03")
    p.add_argument("--all", action="store_true", help="sertakan yang sudah punya versi terpilih")
    p = sub.add_parser("adopt"); p.add_argument("film"); p.add_argument("folder")
    p.add_argument("--credits", default=""); p.add_argument("--model")
    p = sub.add_parser("select"); p.add_argument("film"); p.add_argument("shot"); p.add_argument("take", type=int)
    p.add_argument("--keyframe", action="store_true")
    p = sub.add_parser("frame"); p.add_argument("film"); p.add_argument("shot")
    p.add_argument("--at", type=float); p.add_argument("--out")
    p = sub.add_parser("roughcut"); p.add_argument("film"); p.add_argument("name", nargs="?", default="roughcut")
    p.add_argument("--res", type=int, default=720, help="sisi pendek (720 = draf, 1080 = final)")
    p.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()
    f = Film(a.film)
    globals()[f"cmd_{a.cmd}"](f, a)


if __name__ == "__main__":
    main()
