---
name: film-studio
description: Orchestrator pipeline short movie / video AI profesional — ide atau naskah milik user → shot list & prompt → keyframe per scene → image-to-video + dialog/narasi → produksi di Google Flow, Higgsfield, atau generator lain → edit. Pakai saat user bilang "bikin film/video/short movie pakai AI", "pakai Google Flow/Higgsfield", "ini naskah saya", "lanjutkan film <judul>", "status film", atau ingin menjalankan seluruh pipeline. Mendeteksi tahap yang sudah selesai di films/<slug>/ lalu menjalankan tahap berikutnya lewat skill film-import/film-ide, film-naskah, film-shotlist, film-keyframe, film-motion, film-edit.
---

# Film Studio — pipeline film AI

Pipeline ini menghasilkan **paket produksi** (dokumen pra-produksi + prompt siap tempel) untuk generator video mana pun (Google Flow, Higgsfield, dll.), lalu membantu produksi dan edit. Claude menulis dan mengorganisasi; user yang meng-generate di platform, memilih take, dan memutuskan isi kreatif.

Prinsip (dari framework S.C.E.N.E. di repo ini): *AI generates the shots, editor creates the video.* Satu shot = satu klip pendek. Identitas visual dikunci sekali di bible, lalu dipakai ulang **kata per kata** di setiap prompt.

**Keputusan kreatif milik user.** Materi dari user (naskah, brief, deskripsi karakter) tidak diubah tanpa persetujuan: perubahan diajukan sebagai usulan (`## Catatan AI`, label `Usulan AI`) dan hanya diterapkan setelah diterima. Isi yang dibuat Claude selalu diberi label supaya user tahu mana yang perlu ditinjau.

## Tahapan

| # | Tahap | Skill | Output di `films/<slug>/` | Gate sebelum lanjut |
|---|---|---|---|---|
| 1–2 | **User punya naskah/brief sendiri** → rapikan + catatan produksi | `film-import` | `source/`, `00-brief.md`, `01-bible.md`, `02-naskah.md` | User memutuskan setiap usulan di Catatan AI |
| 1 | *atau* Ide → konsep + bible | `film-ide` | `00-brief.md`, `01-bible.md` | Logline, durasi, gaya, karakter, generator disetujui |
| 2 | *atau* Konsep → naskah | `film-naskah` | `02-naskah.md` | Cerita dan dialog disetujui |
| 3 | Naskah → shot list & prompt plan | `film-shotlist` | `03-shotlist.md` | Total durasi pas, tiap shot ≤ batas klip generator |
| 4 | Image per scene (ingredients + keyframe) | `film-keyframe` | `04-keyframes.md` | User sudah generate dan menyetujui keyframe |
| 5 | Image → video + dialog/narasi | `film-motion` | `05-motion.md` | Prompt siap, checklist take |
| 6 | Produksi & edit: handoff, adopt, pilih take, rough cut | `film-edit` | `handoff/`, `06-edit.md`, `out/` | User menyetujui cut |

Pilih jalan masuk dari pesan user: materi yang sudah ditulis (naskah, skenario, treatment, brief lengkap, file terlampir) → `film-import`; ide mentah → `film-ide`. Kalau ragu, tanyakan.

Setelah tahap 4 dan 5, jalankan `python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>`, lalu delegasikan review kontinuitas ke subagent `film-continuity-reviewer`. Perbaiki semua ERROR sebelum menyerahkan hasil ke user.

## Cara kerja

1. **Tentukan proyek.** Proyek disimpan di `films/<slug>/` (slug kebab-case dari judul). Kalau user tidak menyebut judul dan hanya ada satu proyek, pakai itu. Kalau ada beberapa, tanya yang mana. Kalau belum ada proyek, mulai dari tahap 1.
2. **Deteksi status.** Cek file mana yang sudah ada (00–06) dan baris `Status:` di header tiap file (`draft` / `approved`). Tahap berikutnya adalah file pertama yang belum ada atau masih `draft`.
3. **Jalankan tahap berikutnya** dengan memanggil skill tahap itu (Skill tool). Jangan menulis ulang logika tahap di sini.
4. **Gate.** Di akhir tiap tahap, tampilkan ringkasan singkat dan minta persetujuan. Kalau disetujui, ubah `Status: draft` menjadi `Status: approved`. Jangan lanjut ke tahap berikutnya tanpa persetujuan, **kecuali** user meminta mode otomatis ("langsung semua", "--auto"). Dalam mode otomatis, jalankan tahap 1–3 dan 5 berturut-turut, tapi tetap berhenti setelah tahap 4 karena keyframe harus di-generate user di platform. Mode otomatis tidak berlaku untuk usulan perubahan pada materi user. Tahap 5 tetap boleh ditulis sebelum keyframe ada. Beri tanda di output bahwa prompt motion belum dicek terhadap gambar asli.
5. **Revisi di hulu mengalir ke hilir.** Kalau user merevisi naskah setelah shot list dibuat, set file hilir (03–06) kembali ke `Status: draft` dan perbarui hanya shot yang terdampak.
6. **Ganti generator** di tengah jalan (misalnya dari Flow ke Higgsfield): ubah field `Generator`/`Model video`/`Batas klip`/`Audio native` di bible, lalu cek ulang shot list (durasi, mode) dan prompt motion (sintaks audio) terhadap profil generator baru.

## Struktur folder proyek

```
films/<slug>/
  00-brief.md        # tujuan, audiens, platform, durasi, logline
  01-bible.md        # LOCK: style, karakter, suara, lokasi — sumber kebenaran visual
  02-naskah.md       # naskah per scene (aksi, dialog, narasi)
  03-shotlist.md     # tabel shot: durasi, kamera, karakter, lokasi, audio, mode (Frames/Ingredients/Text/Extend)
  04-keyframes.md    # prompt ingredients + prompt keyframe per shot
  05-motion.md       # prompt image-to-video + dialog/narasi per shot + checklist take
  06-edit.md         # urutan edit, lapisan audio, log take (film-edit / film.py)
  source/            # materi asli dari user (film-import), tidak pernah diubah
  handoff/<generator>/{keyframes,clips}/   # paket upload + downloads/ (film.py handoff)
  assets/
    ingredients/     # CHAR-<Nama>.png, LOC-<Nama>.png ; kandidat di _raw/
    keyframes/       # S01.png, S02.png, ... ; kandidat di _raw/
    clips/           # S01_t1.mp4, S01_t2.mp4, ... ; take terpilih → S01.mp4
    audio/           # narasi/dialog TTS/VO, musik
  out/               # rough cut (tidak masuk git)
  review/            # strip dan contact sheet untuk review
```

Buat folder `assets/*` saat tahap 1 (`mkdir -p`).

## Referensi

- `references/prompting.md`: mode generik (Frames/Ingredients/Text/Extend), aturan gambar, audio, struktur prompt, masalah umum. **Baca sebelum tahap 3, 4, dan 5.**
- `references/generators/<Generator>.md`: pemetaan mode ke UI platform, batas klip, sintaks audio (`flow.md`, `higgsfield.md`, `generic.md` untuk platform lain). Pakai yang sesuai field `Generator` di bible.
- `scripts/film.py`: status, handoff, adopt, select, frame, roughcut (lihat skill `film-edit`).
- `references/formats.md`: format wajib tiap file (blok LOCK, tabel shot list, blok prompt). Script `check_film.py` bergantung pada format ini. **Baca sebelum menulis file apa pun.**

## Laporan status

Kalau user bertanya "status film X", jalankan `python3 .claude/skills/film-studio/scripts/film.py status films/<slug>` dan `check_film.py`, lalu laporkan: tahap saat ini, shot yang sudah punya keyframe dan klip terpilih, total kredit, usulan Catatan AI yang belum diputuskan, dan langkah berikutnya.
