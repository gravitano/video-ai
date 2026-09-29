---
name: film-import
description: Jalan masuk pipeline film AI untuk materi milik user — naskah, skenario, treatment, atau brief yang sudah ditulis sendiri (file .md/.txt/.docx/.pdf/Fountain atau teks tempel). Merapikannya ke format 00-brief.md, 01-bible.md, dan 02-naskah.md TANPA mengubah kata-kata user; masalah produksi dicatat sebagai usulan yang diputuskan user. Pakai saat user bilang "ini naskah saya", "pakai skenario ini", "import naskah", "saya sudah punya script", atau melampirkan file naskah.
---

# Import naskah/brief milik user

Pengganti tahap 1–2 (`film-ide` + `film-naskah`) kalau user sudah punya materi sendiri. Prinsipnya: **isi kreatif milik user, Claude hanya merapikan format dan memberi catatan produksi.**

Baca dulu `.claude/skills/film-studio/references/formats.md`.

## 1. Simpan sumber asli

- Tentukan slug (kebab-case dari judul) dan buat folder: `mkdir -p films/<slug>/{source,assets/{ingredients,keyframes,clips,audio}}`.
- Simpan materi user apa adanya di `films/<slug>/source/` (salin file aslinya; teks tempel disimpan sebagai `source/naskah-asli.md`). File ini tidak pernah diubah dan jadi acuan kalau ada sengketa isi.
- File .docx/.pdf: baca dengan skill yang sesuai (`anthropic-skills:docx` / `anthropic-skills:pdf`), lalu simpan juga versi teksnya di `source/`.

## 2. Tanyakan hanya keputusan yang belum ada (satu putaran)

Ambil sebanyak mungkin dari materi. Tanyakan sekaligus dalam satu pesan (AskUserQuestion bila cocok) hanya yang belum diketahui:

- **Durasi target dan rasio** (16:9 atau 9:16)
- **Gaya visual** (live-action sinematik, animasi 3D, anime, dll.)
- **Generator dan model** (Google Flow, Higgsfield + model apa, atau lainnya). Baca profilnya di `references/generators/`, lalu tentukan `Batas klip` dan `Audio native`.
- **Mode narasi** kalau naskah punya narasi/V.O.

## 3. Tulis `00-brief.md`

Header `Status: draft` + `Sumber: user`. Judul, logline, dan sinopsis **diambil atau disarikan dari materi user**. Kalau materi tidak memuat logline, tulis usulan dengan label **(usulan AI)**. Isi field produksi (platform, rasio, durasi) dari jawaban langkah 2.

## 4. Tulis `01-bible.md`

- Daftar karakter dan lokasi diambil dari naskah. Nama harus sama persis dengan di naskah.
- **LOCK:CHAR/LOC/STYLE**: kalau user sudah mendeskripsikan penampilan, terjemahkan ke bahasa Inggris dengan setia. Detail yang belum ada (warna baju, potongan rambut, dll.) diisi Claude, dan di atas blok LOCK ditulis `Usulan AI: <detail yang ditambahkan>` supaya user tahu mana yang harus disetujui.
- Field Format mengikuti `formats.md` termasuk `Generator`, `Model video`, `Audio native`.
- Kalau `Audio native: tidak`, `Mode narasi` wajib `terpisah`.

## 5. Tulis `02-naskah.md`

Header `Status: draft` + `Sumber: user`. Ubah ke format naskah pipeline (lihat skill `film-naskah`: heading `## SCENE n — INT./EXT. LOKASI — WAKTU`, baris `Estimasi`, dialog `**NAMA**` + parenthetical, `**OVERLAY:**` untuk teks layar).

Aturan keras:
- **Jangan mengubah, memotong, atau menambah kata di dialog, narasi, dan deskripsi aksi user.** Yang boleh: memecah paragraf, memindahkan ke format heading/dialog, memperbaiki salah ketik yang jelas (catat di Catatan AI).
- `Estimasi` per scene dihitung Claude (kata bicara ÷ 2 + waktu aksi), bukan diminta ke user.
- Beat outline di atas naskah disusun Claude dari isi user, dengan label **(disusun AI dari naskah)**.

## 6. Catatan AI

Periksa naskah terhadap batasan produksi, lalu tulis tabel `## Catatan AI` di akhir `02-naskah.md` (format di `formats.md`). Yang dicek:

- Total estimasi vs durasi target (±10%)
- Baris dialog > 14 kata, atau lebih cepat dari ±2 kata/detik untuk durasi yang tersedia
- Dua pembicara bergantian cepat dalam satu momen (butuh shot/reverse-shot)
- Aksi yang berisiko untuk video AI (perkelahian rumit, kerumunan, tulisan yang harus terbaca, gerak tangan detail)
- Jumlah karakter/lokasi yang terlalu banyak untuk konsistensi (> 3 karakter utama, > 4 lokasi)
- Hal yang tidak bisa dibuat generator yang dipilih (misalnya dialog sinkron bibir kalau `Audio native: tidak` → perlu lip-sync saat edit)

Setiap baris berisi masalah dan **usulan konkret** (teks pengganti kalau menyangkut dialog). Kolom `Keputusan` dibiarkan `-`.

## 7. Gate

Tampilkan ke user:
1. Ringkasan: judul, durasi estimasi vs target, jumlah scene, karakter, lokasi, generator.
2. Daftar `Usulan AI` di bible.
3. Tabel Catatan AI, dan minta keputusan per nomor (`terima` / `tolak` / arahan lain).

Terapkan **hanya** usulan yang diterima. Isi kolom `Keputusan`, lalu set `Status: approved` di 00–02 setelah user setuju. Lanjut ke `film-shotlist`.

Selama proyek berjalan, semua perubahan pada naskah ber-`Sumber: user` harus lewat Catatan AI dan persetujuan user. `check_film.py` memberi ERROR kalau prompt motion berisi kalimat yang tidak ada di naskah ini.
