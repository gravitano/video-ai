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
| Python 3 | `check_film.py`, `film.py` | Ya |
| `ffmpeg` | Rough cut, review take | Ya |
| Akun generator: Google Flow, Higgsfield, atau lainnya | Generate gambar & video | Ya |

Di macOS: `brew install ffmpeg`.

## Membuat film

Skill `film-*` ada di `.claude/skills/` dan otomatis terbaca saat Claude Code dibuka dari root repo.

```bash
claude
```

Perintah `film.py` di bawah dijalankan dari root repo di terminal lain (atau minta Claude yang menjalankannya). Supaya ringkas, set dulu:

```bash
S=.claude/skills/film-studio/scripts
```

**1. Mulai dari naskah Anda, atau dari ide.**

> Ini naskah saya (lampirkan file atau tempel teks). Jadikan film 60 detik, 9:16, pakai Higgsfield model Kling.

Claude menyimpan naskah asli di `films/<slug>/source/`, lalu merapikannya ke `00-brief.md`, `01-bible.md`, dan `02-naskah.md` **tanpa mengubah kata-kata Anda**. Masalah produksi (dialog terlalu panjang untuk satu klip, aksi yang sulit untuk AI, durasi tidak pas) ditulis sebagai tabel usulan `Catatan AI`. Anda memutuskan tiap usulan: terima, tolak, atau beri arahan lain.

Belum punya naskah? Mulai dari ide:

> Bikin short movie 60 detik pakai Google Flow, rasio 9:16, idenya: seorang ibu masih menyeduh dua gelas kopi setiap malam untuk anaknya yang merantau.

**2. Lanjutkan tahap demi tahap** dengan *"lanjutkan film <slug>"*: shot list (`03`), prompt keyframe (`04`), prompt motion (`05`). Tiap tahap berhenti di gate untuk persetujuan Anda.

**3. Generate gambar di platform.**

```bash
python3 $S/film.py handoff films/<slug> --stage keyframes
```

Buka `films/<slug>/handoff/<generator>/keyframes/README.md`. Generate *ingredients* dulu (character sheet `CHAR-*`, lokasi `LOC-*`), lalu keyframe per shot dengan gambar di `refs/` sebagai referensi. Unduh hasilnya ke `downloads/` dengan nama diawali ID (`CHAR-Raka.png`, `S01.png`, `S01-b.png`), lalu:

```bash
python3 $S/film.py adopt films/<slug> films/<slug>/handoff/<generator>/keyframes/downloads
```

Minta Claude *"cek keyframe film <slug>"*, lalu pilih versi terbaik (`film.py select films/<slug> S01 2 --keyframe`).

**4. Generate video.** Sama seperti langkah 3, dengan `film.py handoff films/<slug>` (tanpa `--stage`). Buat 2–4 take per shot, unduh ke `downloads/`, lalu `film.py adopt ... --credits <kredit per take>`. Minta Claude *"review take film <slug>"*, dan pilih dengan `film.py select films/<slug> S01 2`.

**5. Rakit.** Minta Claude *"rakit film <slug>"*. Claude menyusun `06-edit.md` (urutan, potongan, transisi, lapisan audio seperti narasi/TTS/musik), lalu:

```bash
python3 $S/film.py roughcut films/<slug> roughcut-v1         # draf 720p → out/ + review/ strip
python3 $S/film.py roughcut films/<slug> final --res 1080    # versi 1080p
python3 $S/film.py status films/<slug>                       # progres + total kredit
```

Finishing (grading, teks, musik final) di DaVinci Resolve atau CapCut, memakai urutan dan potongan dari `06-edit.md`.

Contoh proyek: `films/dua-gelas-kopi/`. Detail alur dan pilihan generator ada di [`WORKFLOW-FILM.md`](WORKFLOW-FILM.md).

## Tips

- Jangan taruh teks di prompt gambar/video. Semua teks ditambahkan saat editing.
- Pakai satu model video untuk satu film supaya gaya gerak dan warna konsisten.
- Validasi kapan saja dengan `python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>`.
- File `out/*.mp4` tidak masuk git dan bisa dirender ulang kapan saja.
- Pipeline lama `scene` (explainer/Reels otomatis) ada di `archived/`; lihat [`archived/README.md`](../archived/README.md).
