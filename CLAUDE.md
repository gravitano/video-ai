# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Repo ini berisi dua pipeline produksi video AI pendek berbasis framework S.C.E.N.E. (`docs/Framework_SCENE_Produksi_Video_AI.pdf`: *AI generates the shots, editor creates the video*), plus proyek-proyek hasilnya. Dokumen dan prompt ditulis dalam bahasa Indonesia; isi prompt gambar/video (LOCK, prompt keyframe/motion) dalam bahasa Inggris.

## Dua pipeline, dua model kerja

### 1. Film pipeline (Google Flow) — `.claude/skills/film-*` + `films/<slug>/`

Claude **hanya menulis dokumen dan prompt**; user yang generate gambar/video di Google Flow (Veo) lalu menaruh hasilnya di `films/<slug>/assets/`. Alur dan gate dijelaskan di `docs/WORKFLOW-GOOGLE-FLOW.md`; orchestrator-nya skill `film-studio`, yang memanggil `film-ide` → `film-naskah` → `film-shotlist` → `film-keyframe` → `film-motion` (output `00-brief.md` … `05-motion.md`).

Hal yang tidak terlihat dari satu file saja:
- **Format file adalah kontrak parser.** `.claude/skills/film-studio/scripts/check_film.py` mem-parse penanda `<!-- LOCK:STYLE|CHAR:<Nama>|LOC:<Nama>|VOICE:<Nama>|PROP:<Nama> -->` + blok ```` ```text ````, tabel shot list 9 kolom persis, dan heading `## Sxx`. Baca `.claude/skills/film-studio/references/formats.md` sebelum menulis/mengubah file film apa pun.
- **LOCK di `01-bible.md` harus disalin verbatim** ke setiap prompt shot yang memakai karakter/lokasi itu; check_film memberi ERROR kalau tidak. Nama di `LOCK:CHAR:<Nama>` harus sama persis dengan kolom Karakter/Lokasi di shot list.
- Anggaran dialog ±2 kata/detik (WARN > 2,2, ERROR > 2,7); durasi shot ≤ `Batas klip` di bible.
- Header `Status: draft|approved` menentukan tahap berikutnya. Revisi di hulu → set file hilir kembali ke `draft`.
- `films/<slug>/.gen/gen_keyframes.py` dan `gen_motion.py` **meng-generate** `04-keyframes.md` / `05-motion.md` dengan menarik LOCK dari bible. Untuk proyek yang punya `.gen/`, edit script-nya lalu jalankan ulang, jangan edit file .md hasilnya langsung.
- `.gen/roughcut.py` merakit `assets/clips/Sxx.mp4` jadi `out/roughcut*.mp4` via ffmpeg (daftar `EDIT` = urutan + trim).
- Setelah tahap 4/5: jalankan check_film, lalu delegasikan review ke subagent `film-continuity-reviewer`.

```bash
python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>   # exit 1 kalau ada ERROR
python3 films/<slug>/.gen/gen_keyframes.py films/<slug>                 # regenerasi 04-keyframes.md
python3 films/<slug>/.gen/gen_motion.py films/<slug>                    # regenerasi 05-motion.md
cd films/<slug> && python3 .gen/roughcut.py roughcut-v2                 # rough cut → out/
```

### 2. `scene` CLI (otomatis end-to-end) — `scene-video-producer/`

Plugin Claude Code (`.claude-plugin/plugin.json`, skill `create-video`) + CLI Python di `scene-video-producer/pipeline/`. Satu `scene.yaml` adalah sumber kebenaran; Claude menulis/merevisi `scene.yaml`, CLI yang mengeksekusi: `voice` (edge-tts + timing kata) → `keyframes` (codex/manual) → `clips` (MiniMax H3, berbayar) → `review` → `build` (generate proyek HyperFrames di `video/`) → `check` → `render`. Proyek video ada di `videos/<proyek>/` (satu folder = satu `scene.yaml`); proyek baru dibuat dengan `scene init videos/<nama>` dari root repo.

- Aset di-cache berdasarkan hash isi; state di `<proyek>/.scene/` (`state.json`, `ledger.jsonl`, `timeline.json`). Menjalankan ulang perintah yang sama melanjutkan task yang tertunda, bukan submit ulang.
- **Biaya:** `clips` butuh `--yes` dan dibatasi `budget.video_usd` (kumulatif dari ledger). Jangan jalankan `clips --yes`/`run --yes` tanpa persetujuan user; pakai `scene estimate` dulu, atau provider `mock` untuk uji.
- `video/` hasil `scene build` jangan diedit manual — ubah `scene.yaml`, lalu build ulang.
- `scene handoff` menghasilkan folder `handoff*/` (PNG + prompt `.txt`) untuk generate klip manual di Flow; hasilnya dikembalikan lewat `scene adopt clips DIR`.
- Persona (`personas/<nama>/persona.yaml` + `sheet.png`) dirujuk dari `scene.yaml` via `persona: ../../personas/<nama>` (path relatif ke folder proyek); bisa juga dipakai ulang di bible film.
- API key MiniMax dibaca dari `~/.minimax_key` atau `MINIMAX_API_KEY`.

```bash
cd scene-video-producer/pipeline && uv sync
uv run --group dev pytest -q                                     # semua test
uv run --group dev pytest -q tests/test_pipeline.py::test_minimax_pricing   # satu test
cd videos/<proyek> && uv run --project ../../scene-video-producer/pipeline scene status
```

Spesifikasi `scene.yaml`: `scene-video-producer/pipeline/scene/templates/scene.yaml` (template berkomentar) dan `README.md` pipeline. Perintah CLI: `init status estimate adopt handoff clips voices search add select review build check render run`.

Folder `videos/<proyek>/video/` adalah proyek HyperFrames dengan `CLAUDE.md`-nya sendiri; kerja di sana pakai skill `/hyperframes*`.

## Git

Output render (`*/out/*.mp4`) di-ignore dan bisa dirender ulang. Aset gambar/klip hasil generate user di `films/*/assets/` tidak di-ignore.
