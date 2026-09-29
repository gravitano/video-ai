# Getting Started

Panduan singkat dari clone sampai video pertama. Gambaran umum repo ada di [`README.md`](../README.md).

## 1. Persiapan

```bash
git clone https://github.com/gravitano/video-ai.git
cd video-ai
```

| Kebutuhan | Dipakai untuk | Wajib? |
|---|---|---|
| [Claude Code](https://claude.ai/code) | Menjalankan skill pipeline | Ya |
| Python 3 | `check_film.py`, script `.gen/` | Ya |
| `ffmpeg` | Rough cut film, audio/render `scene` | Ya |
| Akun Google Flow | Generate gambar & video (pipeline film) | Untuk film |
| `uv` (Python 3.12) | CLI `scene` | Untuk `scene` |
| `node` / `npx` | HyperFrames (build & render `scene`) | Untuk `scene` |
| `codex` | Keyframe otomatis di `scene` | Opsional |
| API key MiniMax | Klip image-to-video di `scene` (berbayar) | Opsional |

Di macOS: `brew install ffmpeg uv node`.

Pilih jalur yang sesuai:

- **Short movie naratif** (dialog, narasi, beberapa karakter) → [Jalur A: Film di Google Flow](#jalur-a-film-di-google-flow)
- **Reels/Shorts explainer atau promo** yang dirender otomatis → [Jalur B: CLI `scene`](#jalur-b-cli-scene)

## Jalur A: Film di Google Flow

Skill `film-*` ada di `.claude/skills/` dan otomatis terbaca saat Claude Code dibuka dari root repo.

```bash
claude
```

**1. Mulai dari ide.** Tulis ke Claude:

> Bikin short movie 60 detik pakai Google Flow, rasio 9:16, idenya: seorang ibu masih menyeduh dua gelas kopi setiap malam untuk anaknya yang merantau.

Claude membuat `films/<slug>/00-brief.md` dan `01-bible.md`, lalu berhenti untuk minta persetujuan. Setujui atau minta revisi.

**2. Lanjutkan tahap demi tahap** dengan *"lanjutkan film <slug>"*: naskah (`02`), shot list (`03`), prompt keyframe (`04`), prompt motion (`05`). Tiap tahap berhenti di gate. Tambahkan *"langsung semua"* kalau tidak mau berhenti di tiap gate.

**3. Generate di Google Flow** memakai prompt dari `04-keyframes.md`:
1. Buat *ingredients* dulu (character sheet `CHAR-*`, lokasi `LOC-*`), simpan di `assets/ingredients/`.
2. Buat keyframe per shot dengan ingredients sebagai referensi, simpan sebagai `assets/keyframes/S01.jpg`, `S02.jpg`, dst.
3. Minta Claude *"cek keyframe film <slug>"*.

**4. Animasikan** memakai prompt dari `05-motion.md` (mode *Frames to Video*, keyframe sebagai frame awal). Buat 2–4 take per shot, lalu simpan take terpilih sebagai `assets/clips/S01.mp4`, dst.

**5. Validasi dan rakit.**

```bash
python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>
cd films/<slug> && python3 .gen/roughcut.py roughcut-v1   # kalau proyek punya .gen/roughcut.py
```

Edit final (musik, teks, grading) dilakukan di CapCut atau DaVinci Resolve memakai catatan edit di `05-motion.md`.

Contoh proyek lengkap: `films/dua-gelas-kopi/`. Detail alur ada di [`WORKFLOW-GOOGLE-FLOW.md`](WORKFLOW-GOOGLE-FLOW.md).

## Jalur B: CLI `scene`

**1. Install CLI.**

```bash
cd scene-video-producer/pipeline
uv sync
alias scene="$PWD/.venv/bin/scene"
cd ../..
```

**2. (Opsional) API key MiniMax** untuk klip video. Simpan di file, jangan di chat atau kode:

```bash
printf '%s' 'KEY' > ~/.minimax_key && chmod 600 ~/.minimax_key
```

Tanpa key, pakai `providers.video.name: mock` (gratis) atau `scene run --no-clips` (still + kamera virtual).

**3. Buat proyek dan isi `scene.yaml`.**

```bash
scene init videos/promo-x
```

Buka Claude Code dengan plugin `scene-video-producer` (skill `create-video`), lalu minta Claude mengisi `videos/promo-x/scene.yaml` dari brief Anda:

```bash
claude --plugin-dir ./scene-video-producer
```

Untuk karakter yang konsisten, tambahkan `persona: ../../personas/sari` (atau `bito`, `kai`) di `scene.yaml`.

**4. Produksi.**

```bash
cd videos/promo-x
scene voice                 # TTS + timing kata
scene keyframes             # gambar per shot
scene review                # cek review/keyframes.jpg sebelum bayar video
scene estimate              # lihat biaya klip
scene clips --yes           # berbayar, dibatasi budget.video_usd
scene build && scene check && scene render   # → out/promo-x.mp4
scene status                # progres per shot + total pengeluaran
```

Mau generate klip di Google Flow saja? Jalankan `scene handoff`, generate di Flow sesuai README handoff, lalu `scene adopt clips <folder>`.

Contoh proyek: `videos/sdd-sari/`, `videos/gits-profile/`. Referensi lengkap: [`scene-video-producer/pipeline/README.md`](../scene-video-producer/pipeline/README.md).

## Tips

- Jangan edit `videos/*/video/` secara manual. Ubah `scene.yaml`, lalu `scene build` ulang.
- Jangan taruh teks di prompt gambar/video. Semua teks ditambahkan saat editing.
- File `*/out/*.mp4` tidak masuk git dan bisa dirender ulang kapan saja.
