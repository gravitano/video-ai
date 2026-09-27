---
name: film-studio
description: Orchestrator pipeline short movie / video AI untuk Google Flow — ide → naskah → shot list & prompt → image keyframe per scene → image-to-video + prompt narasi/dialog. Pakai saat user bilang "bikin film/video/short movie pakai AI", "pakai Google Flow", "lanjutkan film <judul>", "status film", atau ingin menjalankan seluruh pipeline. Mendeteksi tahap yang sudah selesai di films/<slug>/ lalu menjalankan tahap berikutnya lewat skill film-ide, film-naskah, film-shotlist, film-keyframe, film-motion.
---

# Film Studio — pipeline Google Flow

Pipeline ini menghasilkan **paket produksi siap-tempel ke Google Flow**, bukan video jadi. Claude menulis dokumen dan prompt; user yang meng-generate gambar/video di Flow lalu menaruh hasilnya di folder `assets/`.

Prinsip (dari framework S.C.E.N.E. di repo ini): *AI generates the shots, editor creates the video.* Satu shot = satu klip pendek. Identitas visual dikunci sekali di bible, lalu dipakai ulang **kata per kata** di setiap prompt.

## Tahapan

| # | Tahap | Skill | Output di `films/<slug>/` | Gate sebelum lanjut |
|---|---|---|---|---|
| 1 | Ide → konsep + bible | `film-ide` | `00-brief.md`, `01-bible.md` | Logline, durasi, gaya, dan karakter disetujui |
| 2 | Konsep → naskah | `film-naskah` | `02-naskah.md` | Cerita dan dialog disetujui |
| 3 | Naskah → shot list & prompt plan | `film-shotlist` | `03-shotlist.md` | Total durasi pas, tiap shot ≤ batas klip Flow |
| 4 | Image per scene (ingredients + keyframe) | `film-keyframe` | `04-keyframes.md` | User sudah generate dan menyetujui keyframe |
| 5 | Image → video + narasi/dialog | `film-motion` | `05-motion.md` | Checklist take dan edit |

Setelah tahap 4 dan 5, jalankan `python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>`, lalu delegasikan review kontinuitas ke subagent `film-continuity-reviewer`. Perbaiki semua ERROR sebelum menyerahkan hasil ke user.

## Cara kerja

1. **Tentukan proyek.** Proyek disimpan di `films/<slug>/` (slug kebab-case dari judul). Kalau user tidak menyebut judul dan hanya ada satu proyek, pakai itu. Kalau ada beberapa, tanya yang mana. Kalau belum ada proyek, mulai dari tahap 1.
2. **Deteksi status.** Cek file mana yang sudah ada (00–05) dan baris `Status:` di header tiap file (`draft` / `approved`). Tahap berikutnya adalah file pertama yang belum ada atau masih `draft`.
3. **Jalankan tahap berikutnya** dengan memanggil skill tahap itu (Skill tool). Jangan menulis ulang logika tahap di sini.
4. **Gate.** Di akhir tiap tahap, tampilkan ringkasan singkat dan minta persetujuan. Kalau disetujui, ubah `Status: draft` menjadi `Status: approved`. Jangan lanjut ke tahap berikutnya tanpa persetujuan, **kecuali** user meminta mode otomatis ("langsung semua", "--auto"). Dalam mode otomatis, jalankan tahap 1–3 dan 5 berturut-turut, tapi tetap berhenti setelah tahap 4 karena keyframe harus di-generate user di Flow. Tahap 5 tetap boleh ditulis sebelum keyframe ada. Beri tanda di output bahwa prompt motion belum dicek terhadap gambar asli.
5. **Revisi di hulu mengalir ke hilir.** Kalau user merevisi naskah setelah shot list dibuat, set file hilir (03–05) kembali ke `Status: draft` dan perbarui hanya shot yang terdampak.

## Struktur folder proyek

```
films/<slug>/
  00-brief.md        # tujuan, audiens, platform, durasi, logline
  01-bible.md        # LOCK: style, karakter, suara, lokasi — sumber kebenaran visual
  02-naskah.md       # naskah per scene (aksi, dialog, narasi)
  03-shotlist.md     # tabel shot: durasi, kamera, karakter, lokasi, audio, mode Flow
  04-keyframes.md    # prompt ingredients + prompt keyframe per shot
  05-motion.md       # prompt image-to-video + dialog/narasi per shot + checklist take
  assets/
    ingredients/     # CHAR-<Nama>.png, LOC-<Nama>.png  (hasil generate user)
    keyframes/       # S01.png, S02.png, ...
    clips/           # S01_t1.mp4, S01_t2.mp4, ... ; take terpilih → S01.mp4
    audio/           # narasi TTS/VO kalau mode narasi = terpisah
```

Buat folder `assets/*` saat tahap 1 (`mkdir -p`).

## Referensi

- `references/flow-guide.md`: fitur Google Flow, batasan klip, sintaks audio/dialog, dan masalah umum beserta solusinya. **Baca sebelum tahap 3, 4, dan 5.**
- `references/formats.md`: format wajib tiap file (blok LOCK, tabel shot list, blok prompt). Script `check_film.py` bergantung pada format ini. **Baca sebelum menulis file apa pun.**

## Laporan status

Kalau user bertanya "status film X", baca file-file proyek dan laporkan: tahap saat ini, shot mana yang sudah punya keyframe (`assets/keyframes/Sxx.*`) dan klip terpilih (`assets/clips/Sxx.mp4`), serta langkah berikutnya. Jalankan `check_film.py` untuk angka durasi.
