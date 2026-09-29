# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Repo ini berisi dua pipeline produksi video AI pendek berbasis framework S.C.E.N.E. (`docs/Framework_SCENE_Produksi_Video_AI.pdf`: *AI generates the shots, editor creates the video*), plus proyek-proyek hasilnya. **Film pipeline adalah jalur utama**; `scene` CLI jalur sekunder untuk explainer/Reels berbasis VO. Dokumen dan prompt ditulis dalam bahasa Indonesia; isi prompt gambar/video (LOCK, prompt keyframe/motion) dalam bahasa Inggris.

## Dua pipeline

### 1. Film pipeline (jalur utama) — `.claude/skills/film-*` + `films/<slug>/`

Claude menulis dokumen pra-produksi dan prompt, menyiapkan paket upload, lalu membantu review take dan rough cut. User yang memutuskan isi kreatif, generate di platform (Google Flow, Higgsfield, dll.), dan memilih take. Alur dan gate: `docs/WORKFLOW-FILM.md`. Orchestrator: skill `film-studio` → (`film-import` untuk naskah milik user | `film-ide` → `film-naskah`) → `film-shotlist` → `film-keyframe` → `film-motion` → `film-edit` (output `00-brief.md` … `06-edit.md`).

Hal yang tidak terlihat dari satu file saja:
- **Format file adalah kontrak parser.** `scripts/filmlib.py` (dipakai `check_film.py` dan `film.py`) mem-parse penanda `<!-- LOCK:STYLE|CHAR:<Nama>|LOC:<Nama>|VOICE:<Nama>|PROP:<Nama> -->` + blok ```` ```text ````, field Format bible, tabel shot list 9 kolom persis, heading `## Sxx`, dan tabel `Urutan edit` / `Lapisan audio` / `Log take` di `06-edit.md`. Baca `.claude/skills/film-studio/references/formats.md` sebelum menulis/mengubah file film apa pun.
- **Materi user tidak diubah tanpa persetujuan.** File ber-header `Sumber: user` (dari `film-import`) hanya diubah lewat baris `## Catatan AI` yang kolom Keputusan-nya `terima`. check_film memberi ERROR kalau kalimat yang diucapkan di `05-motion.md` tidak ada di naskah user. Materi asli disimpan di `films/<slug>/source/`.
- **Generator dipisah dari aturan prompt.** Field `Generator` di bible memilih profil `references/generators/<nama>.md` (`flow`, `higgsfield`, `generic` sebagai fallback); aturan umum ada di `references/prompting.md`. Kolom Mode shot list memakai nama generik (`Frames/Ingredients/Text/Extend`). `Audio native: tidak` berarti prompt motion tanpa dialog (baris `Dialog terpisah:`), dan `Mode narasi` wajib `terpisah`.
- **LOCK di `01-bible.md` harus disalin verbatim** ke setiap prompt shot yang memakai karakter/lokasi itu; check_film memberi ERROR kalau tidak. Nama di `LOCK:CHAR:<Nama>` harus sama persis dengan kolom Karakter/Lokasi di shot list.
- Anggaran dialog ±2 kata/detik (WARN > 2,2, ERROR > 2,7); durasi shot ≤ `Batas klip` di bible.
- Header `Status: draft|approved` menentukan tahap berikutnya. Revisi di hulu → set file hilir kembali ke `draft`.
- **Take:** `film.py adopt` menyalin unduhan (nama diawali `Sxx`/`CHAR-`/`LOC-`/`PROP-`) ke `assets/clips/Sxx_tN.mp4`, `assets/keyframes/_raw/Sxx_vN.*`, atau `assets/ingredients/_raw/`, dan mencatatnya di `Log take`. `film.py select` menyalin take ke nama final (`Sxx.mp4`, `Sxx.jpg`); file final lama yang bukan salinan take dicadangkan sebagai `*_lama*`. Tidak ada perintah yang menghapus take.
- `film.py roughcut` membaca `06-edit.md`. Mix audio dan encode final sengaja dua langkah: `loudnorm` di dalam `filter_complex` bersama filter video membuat paket audio melompat ±3 dtk.
- `films/dua-gelas-kopi/.gen/` berisi script lama khusus proyek itu (generator 04/05 dan `roughcut.py`). Kalau proyek punya `.gen/gen_*.py`, edit script-nya lalu jalankan ulang, jangan edit file .md hasilnya langsung. Untuk rough cut pakai `film.py roughcut`.
- Setelah tahap 4/5: jalankan check_film, lalu delegasikan review ke subagent `film-continuity-reviewer`.

```bash
S=.claude/skills/film-studio/scripts
python3 $S/check_film.py films/<slug>                    # exit 1 kalau ada ERROR
python3 $S/film.py status films/<slug>
python3 $S/film.py handoff films/<slug> [--stage keyframes] [--shots S01,S02] [--all]
python3 $S/film.py adopt films/<slug> <folder> [--credits N] [--model M]
python3 $S/film.py select films/<slug> S03 2 [--keyframe]
python3 $S/film.py frame films/<slug> S03 [--at DTK]
python3 $S/film.py roughcut films/<slug> [nama] [--res 720|1080] [--fps 24]
```

Script film hanya memakai stdlib Python + `ffmpeg`/`ffprobe`; tidak ada test otomatis. Uji perubahan pada salinan proyek di scratchpad (mis. salin `films/dua-gelas-kopi`), bukan pada proyek asli.

### 2. `scene` CLI (explainer/Reels otomatis) — `scene-video-producer/`

Untuk video berbasis voice-over + overlay teks; tidak mendukung dialog antar-karakter (handoff ke Flow sengaja menambahkan "no dialogue").

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

Output render (`**/out/*.mp4`) di-ignore dan bisa dirender ulang. Aset gambar/klip hasil generate user di `films/*/assets/` tidak di-ignore.
