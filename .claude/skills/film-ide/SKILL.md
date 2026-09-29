---
name: film-ide
description: Tahap 1 pipeline film AI — mengubah ide mentah menjadi creative brief (00-brief.md) dan bible visual (01-bible.md) berisi LOCK style, karakter, suara, dan lokasi untuk generator video (Google Flow, Higgsfield, dll.). Kalau user sudah punya naskah/brief sendiri, pakai film-import. Pakai saat user punya ide film/video pendek dan ingin mulai, atau bilang "kembangkan ide ini", "bikin konsep film", "bikin karakter/bible". Biasanya dipanggil oleh film-studio.
---

# Tahap 1 — Ide → Brief + Bible

Baca dulu `.claude/skills/film-studio/references/formats.md` (format 01-bible.md wajib diikuti).

## 1. Gali ide (maksimal satu putaran pertanyaan)

Ambil dari pesan user sebanyak mungkin. Tanyakan **sekaligus dalam satu pesan** (AskUserQuestion bila cocok) hanya hal yang belum diketahui dan benar-benar mengubah hasil:

- **Genre dan mood** (drama, komedi, horor, sci-fi, iklan/promo, edukasi)
- **Durasi dan platform**: short movie 1–3 menit (16:9) atau Reels/Shorts 30–60 detik (9:16)
- **Gaya visual**: live-action sinematik, animasi 3D, anime, claymation, dll.
- **Bahasa dialog** (default Indonesia) dan **mode narasi**: `in-video` atau `terpisah`
- **Generator dan model**: Google Flow, Higgsfield (model apa), atau lainnya. Baca profilnya di `.claude/skills/film-studio/references/generators/` untuk mengisi `Batas klip` dan `Audio native`.

Sisanya boleh diasumsikan. Tulis asumsi itu di brief dengan label **Asumsi**.

**Karakter yang sudah ada:** cek `personas/*/persona.yaml`. Kalau ada yang cocok atau user menyebut namanya, tawarkan untuk dipakai ulang. Ubah field `look` menjadi LOCK:CHAR, `voice`/`speaking_style` menjadi LOCK:VOICE, dan catat `sheet.png` sebagai ingredient yang sudah jadi (salin ke `assets/ingredients/CHAR-<Nama>.png`).

## 2. Tulis `films/<slug>/00-brief.md`

Isi:
- **Judul** (kerja) dan **logline** (1 kalimat: tokoh + keinginan + hambatan + taruhan)
- Genre, mood, audiens, platform, rasio, durasi target
- **Pesan/tema** yang harus dirasakan penonton
- **Sinopsis** 1 paragraf (awal–tengah–akhir, termasuk ending)
- Referensi rasa (film atau gaya yang mirip), opsional
- Asumsi

Tawarkan **3 variasi logline** kalau idenya masih kabur, lalu minta user memilih sebelum lanjut. Kalau user sudah menulis sebagian (logline, sinopsis, deskripsi karakter), pakai kata-katanya apa adanya; isi yang ditambahkan Claude diberi label **(usulan AI)**.

## 3. Tulis `films/<slug>/01-bible.md`

Ikuti format di `formats.md`. Panduan isi:

- **Batasi skala.** Short movie AI yang bagus biasanya punya **1–3 karakter** dan **1–4 lokasi**. Makin sedikit, makin konsisten. Kalau ide user butuh lebih banyak, sarankan untuk dipangkas.
- **LOCK:CHAR** harus spesifik dan kasatmata: usia, etnis, bentuk badan, rambut (potongan dan warna), ciri wajah khas, **satu outfit tetap** (warna dan bahan). Hindari kata abstrak ("cantik", "keren"). Kalau outfit berganti di tengah cerita, buat LOCK terpisah (`LOCK:CHAR:Raka-Kemeja`).
- **LOCK:VOICE**: jenis kelamin, rentang usia, warna suara, logat, tempo.
- **LOCK:STYLE**: medium (film/animasi), lensa atau film stock, palet warna, pencahayaan, grain/tekstur. Jangan memasukkan komposisi per shot di sini.
- **LOCK:LOC**: tempat, era, benda khas, sumber cahaya. Waktu (siang/malam) boleh masuk kalau lokasi selalu dipakai di waktu yang sama. Kalau tidak, waktu ditulis per shot.
- Semua isi LOCK ditulis dalam **bahasa Inggris**. Penjelasan untuk manusia (peran, busur karakter) ditulis dalam bahasa Indonesia di luar blok.
- Isi field Format lengkap sesuai `formats.md`, termasuk `Generator`, `Model video`, dan `Audio native`. Kalau `Audio native: tidak`, `Mode narasi` wajib `terpisah`.
- Tutup dengan **Aturan tetap**: minimal "tanpa teks/logo/subtitle di gambar dan video".

Buat juga folder aset: `mkdir -p films/<slug>/assets/{ingredients,keyframes,clips,audio}`.

## 4. Gate

Tampilkan ke user: logline, sinopsis, daftar karakter (1 baris per karakter), gaya, dan durasi. Minta persetujuan atau revisi. Setelah disetujui, set `Status: approved` di kedua file dan sarankan lanjut ke `film-naskah`.
