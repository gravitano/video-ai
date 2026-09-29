---
name: film-edit
description: Tahap 6 pipeline film AI — produksi & pasca-produksi. Membuat paket handoff per generator (Flow, Higgsfield, dll.), memasukkan hasil unduhan sebagai take, me-review dan memilih take, menyusun 06-edit.md (urutan, trim, transisi, lapisan audio), lalu merakit rough cut dengan ffmpeg. Pakai saat user bilang "siapkan upload ke Flow/Higgsfield", "ini hasil generate-nya", "adopt klip", "review take", "pilih take", "rakit film", "rough cut", "edit film", atau lanjutan setelah film-motion.
---

# Tahap 6 — Produksi & edit

Alat utama: `python3 .claude/skills/film-studio/scripts/film.py <perintah> films/<slug>` (jalankan dari root repo; `--help` untuk detail). Semua perintah tidak menghapus take. Format `06-edit.md` ada di `references/formats.md`. Panduan platform: `references/generators/<Generator>.md` sesuai bible.

## A. Handoff ke generator

```bash
python3 .claude/skills/film-studio/scripts/film.py handoff films/<slug> --stage keyframes   # ingredients + keyframe yang belum ada
python3 .claude/skills/film-studio/scripts/film.py handoff films/<slug>                     # klip yang belum punya take terpilih
```

Hasilnya `films/<slug>/handoff/<generator>/<stage>/`: prompt `.txt` per item, frame awal, gambar referensi di `refs/`, dan `README.md` berisi tabel kerja. Sampaikan ke user langkah dari profil generator (mode di UI, model, rasio) dan minta hasil diunduh ke `downloads/` dengan **nama diawali ID** (`S03.mp4`, `S03-b.mp4`, `CHAR-Raka.png`).

## B. Adopt hasil unduhan

```bash
python3 .claude/skills/film-studio/scripts/film.py adopt films/<slug> <folder-unduhan> --credits <kredit per take> [--model "<model>"]
```

Klip menjadi `assets/clips/Sxx_tN.mp4`, keyframe menjadi `assets/keyframes/_raw/Sxx_vN.*`, ingredient menjadi `assets/ingredients/_raw/<nama>_vN.*`, dan semuanya tercatat di tabel `Log take` di `06-edit.md`. File yang sudah pernah di-adopt dilewati.

## C. Review take (Claude)

Untuk tiap shot yang punya take baru:

1. Ambil beberapa frame per take: `ffmpeg -v error -i <take> -vf "fps=2,scale=-2:360,tile=8x1" -frames:v 1 films/<slug>/review/takes/<shot>_tN.jpg` (buat foldernya dulu), lalu buka gambarnya (Read). Bandingkan dengan keyframe dan character sheet.
2. Periksa checklist di `05-motion.md` (`Cek take`): wajah/outfit konsisten, tangan wajar, tidak ada teks/subtitle, tidak ada cut/morph, gerak sesuai prompt. Untuk audio: `ffmpeg -i <take> -af volumedetect -f null -` untuk memastikan ada suara, dan dengarkan ulang oleh user untuk dialog.
3. Laporkan per shot: take mana yang terbaik, rentang detik yang bisa dipakai (misalnya "0–1,7 lalu 2,4–7 karena morph di 1,8–2,3"), dan masalah yang butuh regenerate beserta revisi prompt (diagnosis dengan tabel "Masalah umum" di `references/prompting.md`).
4. **User yang memutuskan take.** Setelah user setuju:

```bash
python3 .claude/skills/film-studio/scripts/film.py select films/<slug> S03 2              # klip
python3 .claude/skills/film-studio/scripts/film.py select films/<slug> S03 1 --keyframe   # keyframe
python3 .claude/skills/film-studio/scripts/film.py select films/<slug> CHAR-Raka 2         # ingredient
```

`select` menyalin take ke nama final (`Sxx.mp4`, `Sxx.jpg`), memperbarui status di log, dan mengisi `Take terpilih:` di `05-motion.md`. File final lama yang bukan salinan take dicadangkan sebagai `*_lama*`.

Shot `Extend` atau shot yang harus menyambung: `film.py frame films/<slug> S03` mengambil frame terakhir klip terpilih sebagai frame awal shot berikutnya.

## D. Susun `06-edit.md`

Isi tabel `Urutan edit` dari `Catatan edit` di `05-motion.md` dan hasil review take:
- Satu baris per shot sesuai urutan tayang (boleh berbeda dari urutan shot list kalau itu memperbaiki alur; jelaskan di Catatan).
- `Potong video`: buang awal/akhir yang "mulai dari diam", bagian morph, atau gerak yang tidak diinginkan.
- `Audio`: `klip` untuk audio native, rentang tertentu kalau video dipotong di tengah tapi dialog/narasi harus utuh, `mute` untuk klip bisu atau audio yang diganti.
- `Transisi`: default `cut`; `dissolve 0.5–1` hanya untuk pergantian waktu/tempat.

`Lapisan audio`: narasi terpisah, dialog TTS/lip-sync, dan musik. Kalau user ingin TTS, tawarkan `edge-tts` dengan voice dari bible/persona, dan jalankan hanya setelah disetujui. Musik harus berlisensi; kalau belum ada, biarkan barisnya sebagai pengingat.

Validasi: `python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>`.

## E. Rough cut

```bash
python3 .claude/skills/film-studio/scripts/film.py roughcut films/<slug> roughcut-v1            # draf 720p
python3 .claude/skills/film-studio/scripts/film.py roughcut films/<slug> final --res 1080 --fps 24
```

Hasil: `out/<nama>.mp4` (loudness dinormalisasi ke -16 LUFS, fade out di akhir) dan `review/<nama>-strip.jpg`. Buka strip-nya, cek urutan dan kontinuitas, lalu laporkan ke user: durasi vs target, shot yang belum punya klip, dan usulan perbaikan.

## F. Serah terima

Rough cut adalah untuk review. Finishing (grading, teks/overlay, mix musik, subtitle) biasanya di DaVinci Resolve atau CapCut: berikan urutan klip, trim, dan lapisan audio dari `06-edit.md`. Laporkan juga total kredit dari `film.py status`.

Set `Status: approved` di `06-edit.md` setelah user menyetujui cut final.
