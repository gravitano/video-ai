"""Export a manual-generation pack: everything needed to make the clips in a web UI, then bring them back
with `scene adopt clips <dir>`.

Targets:
  minimax  MiniMax / Hailuo web — Image to Video with the keyframe as first frame      → handoff/
  flow     Google Flow (Veo)   — Frames to Video (start frame) or Ingredients to Video → handoff-flow/
"""
from __future__ import annotations

import shutil

from ..timing import plan
from ..util import SceneError, log
from . import clips, keyframes


NO_DIALOGUE = (" The character does not speak: no dialogue, no lip-sync, mouth relaxed or smiling;"
               " only soft ambient room sound. No music.")

TARGETS = {
    "minimax": {"dir": "handoff", "title": "web MiniMax (Hailuo)", "suffix": "", "setup": [
        "- Mode: **Image to Video**; unggah `<shot>.png` sebagai frame pertama (first frame).",
        "- Referensi karakter (jika ada opsi subject/character reference): {refs}.",
        "- Rasio: ikut gambar (vertikal 9:16). Resolusi: 768P atau lebih tinggi.",
        "- Durasi: pilih yang **≥ durasi target**; kelebihan dipotong otomatis, kekurangan ditahan di frame terakhir.",
        "- Matikan prompt enhancer / auto-optimize jika ada, agar batasan \"no text, preserve identity\" tidak diubah.",
        "- Audio klip tidak dipakai (VO, musik, SFX dipasang oleh pipeline)."]},
    "flow": {"dir": "handoff-flow", "title": "Google Flow (Veo)", "suffix": NO_DIALOGUE, "setup": [
        "- Buat project baru di Flow; set **aspect ratio Portrait (9:16)** sebelum generate.",
        "- Mode utama: **Frames to Video** — `<shot>.png` sebagai *start frame*, end frame dikosongkan. Ini menjaga komposisi",
        "  tetap sama dengan keyframe (dan dengan posisi overlay di video).",
        "- Jika wajah/kostum berubah: coba **Ingredients to Video** dengan {refs} + `<shot>.png` sebagai ingredients",
        "  (identitas lebih kuat, tetapi komposisi awal tidak dikunci — cek ulang posisi teks setelah build).",
        "- Model: varian **Fast** untuk draf, **Quality** untuk final; biaya kredit terlihat saat memilih model.",
        "- Durasi: pilih yang **≥ durasi target** (Flow menawarkan 4/6/8 dtk, dan 10 dtk pada model tertentu).",
        "- Prompt `.txt` sudah ditambah instruksi *tanpa dialog* — Veo membuat audio & bisa membuat karakter berbicara;",
        "  audio klip tidak dipakai, VO dari pipeline.",
        "- Unduh MP4 (720p cukup; upscale 1080p jika tersedia)."]},
}


def run(spec, state, target: str = "minimax") -> None:
    if target not in TARGETS:
        raise SceneError(f"unknown handoff target '{target}' (available: {', '.join(TARGETS)})")
    cfg = TARGETS[target]
    out = spec.root / cfg["dir"]
    (out / "downloads").mkdir(parents=True, exist_ok=True)
    tl = {p["id"]: p for p in plan(spec, state)}
    rows = []
    for i, s in enumerate(spec.shots, 1):
        kf = keyframes.current(spec, state, s)
        if not kf:
            raise SceneError(f"{s['id']}: no current keyframe — run `scene keyframes` first")
        shutil.copyfile(kf, out / f"{s['id']}.png")
        dur = tl[s["id"]]["dur"]
        prompt = " ".join(s["motion_prompt"].split()) + cfg["suffix"]
        (out / f"{s['id']}.txt").write_text(prompt + "\n")
        done = "✓ sudah ada klip" if clips.selected_clip(spec, state, s) else ""
        rows.append((i, s["id"], dur, prompt, done))
    refs = []
    for k, img in enumerate(spec.persona_images()):
        name = f"reference-{k + 1}{img.suffix}"
        shutil.copyfile(img, out / name)
        refs.append(name)

    lines = [f"# Handoff klip — {spec.project} → {cfg['title']}", "",
             f"Buat klip image-to-video per shot di {cfg['title']}, lalu kembalikan ke pipeline.", "",
             "## Pengaturan untuk semua shot", "",
             *[l.format(refs=", ".join(f"`{r}`" for r in refs) if refs else "—") for l in cfg["setup"]], "",
             "## Per shot", "",
             "| # | File gambar | Durasi target | Prompt (salin dari file .txt) | Status |", "| --- | --- | --- | --- | --- |"]
    for i, sid, dur, prompt, done in rows:
        lines.append(f"| {i} | `{sid}.png` | {dur} dtk | `{sid}.txt` — {prompt[:70]}… | {done} |")
    lines += ["", "## Setelah generate", "",
              "1. Unduh MP4 terbaik tiap shot ke folder `downloads/`, **beri nama diawali id shot**, mis. `01_hook.mp4`",
              "   (variasi: `01_hook-2.mp4`).",
              "2. Cek: wajah/kostum sama dengan keyframe, tangan wajar, tidak ada teks/logo muncul, tidak ada potongan adegan.",
              "3. Jalankan dari folder proyek:", "",
              "```bash", f"scene adopt clips {cfg['dir']}/downloads", "scene review          # review/clips.jpg", "scene build && scene check && scene render", "```", "",
              "Shot yang belum punya klip tetap tampil sebagai keyframe + kamera virtual, jadi bisa dikerjakan bertahap."]
    (out / "README.md").write_text("\n".join(lines) + "\n")
    log(f"  wrote {out.relative_to(spec.root)}/ — {len(rows)} keyframes + prompts, {len(refs)} reference image(s), README.md")
    log(f"  put downloaded clips in {out.relative_to(spec.root)}/downloads/ then: scene adopt clips {cfg['dir']}/downloads")
