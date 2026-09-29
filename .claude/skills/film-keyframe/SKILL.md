---
name: film-keyframe
description: Tahap 4 pipeline film AI — menulis prompt gambar untuk generator (Flow, Higgsfield, dll.) (04-keyframes.md) berisi ingredients (character sheet, lokasi) dan satu keyframe/frame awal per shot, dengan LOCK bible disalin verbatim agar karakter konsisten. Juga bisa me-review gambar keyframe yang sudah di-generate. Pakai saat user minta "prompt gambar per scene", "bikin keyframe", "image prompt", "cek keyframe", atau lanjutan setelah film-shotlist.
---

# Tahap 4 — Image per scene (ingredients + keyframe)

Baca `.claude/skills/film-studio/references/formats.md` dan `.claude/skills/film-studio/references/prompting.md` dan profil generator `references/generators/<Generator>.md` sesuai bible (bagian Gambar dan Struktur prompt). Input: `01-bible.md` dan `03-shotlist.md`. Output: `films/<slug>/04-keyframes.md`.

## A. Ingredients (dibuat sekali, dipakai di semua shot)

Buat satu entri per karakter dan per lokasi dari bible. Lewati entri yang file-nya sudah ada di `assets/ingredients/` (misalnya dari `personas/`), cukup tulis `File sudah ada.`

**Character sheet** (satu per karakter / varian outfit):
```
Character reference sheet of <LOCK:CHAR verbatim>. Full body front view and three-quarter view side by side, plus a head-and-shoulders close-up, neutral expression, standing on a plain light grey seamless background, even soft studio lighting. <LOCK:STYLE verbatim>. No text, no labels, no watermark.
```

**Location plate** (satu per lokasi, tanpa orang):
```
Empty establishing view of <LOCK:LOC verbatim>, <waktu & cahaya paling sering dipakai>, no people. <LOCK:STYLE verbatim>. Aspect ratio <rasio>. No text, no signage lettering, no watermark.
```

## B. Keyframe per shot

Keyframe = **frame pertama** shot, dengan rasio sama seperti video. Satu entri per shot dengan mode `Frames`. Shot `Text` dan `Extend` ditulis tanpa prompt. Shot `Ingredients` tidak butuh keyframe, cukup tulis ingredient mana yang harus diupload di tahap 5.

Template (urutan ini penting karena model memberi bobot lebih ke awal prompt):
```
<LOCK:STYLE verbatim>. <Shot type>, <lensa/sudut, mis. 35mm eye level / low angle>. <LOCK:CHAR verbatim untuk setiap karakter di kolom Karakter> <pose & ekspresi di AWAL aksi, posisi dalam frame>. <LOCK:LOC verbatim> <waktu, cuaca, arah cahaya>. <komposisi: rule of thirds, ruang kosong untuk arah gerak / overlay>. Aspect ratio <rasio>. No text, no captions, no logos, no watermark.
```

Aturan:
- Salin LOCK **kata per kata**, jangan diringkas atau diparafrase. `check_film.py` memeriksa hal ini.
- Kolom `Karakter` dan `Lokasi` di shot list menentukan LOCK mana yang wajib masuk.
- Deskripsikan **keadaan awal**, bukan aksi yang sedang terjadi. Kalau shot bercerita "Raka membuka pintu", keyframe-nya "Raka berdiri menghadap pintu, tangan kanan di gagang".
- Dua karakter dalam satu frame: sebutkan posisi masing-masing dengan jelas ("on the left... on the right...").
- Baris `Referensi:` menyebut ingredient yang harus diupload bersama prompt (misalnya `CHAR-Raka, LOC-Warung`).
- Untuk shot yang berakhir di keadaan sangat berbeda (misalnya transisi siang ke malam), boleh tambahkan blok kedua `Frame akhir (opsional)` untuk fitur frame akhir (kalau generator mendukung).

## C. Instruksi ke user

Di bagian atas file, tulis langkah singkat:
1. Generate semua ingredients dulu. Pilih yang terbaik, lalu simpan dengan nama file yang tertera.
2. Untuk tiap keyframe, upload ingredient yang disebut di `Referensi`, tempel prompt, dan generate 2–4 variasi.
3. Simpan yang terpilih sebagai `assets/keyframes/Sxx.png`.
4. Setelah semua tersimpan, minta Claude untuk "cek keyframe".

## D. Review keyframe (kalau gambar sudah ada)

Kalau `assets/keyframes/*.png|jpg` sudah ada dan user meminta review: buka (Read) character sheet dan tiap keyframe, lalu periksa:
- Wajah, rambut, dan outfit cocok dengan character sheet
- Lokasi dan palet cocok dengan location plate dan LOCK:STYLE
- Rasio benar; tidak ada teks atau watermark; tangan dan anatomi wajar
- Komposisi mendukung aksi shot (ada ruang untuk gerak)

Laporkan per shot: ✅ lolos, atau ❌ beserta masalahnya dan revisi prompt yang disarankan (misalnya tambahan "same face as reference image"). Perbarui prompt di file kalau diganti.

## Validasi dan gate

Jalankan `python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>` sampai tidak ada ERROR. Buat paket upload dengan `python3 .claude/skills/film-studio/scripts/film.py handoff films/<slug> --stage keyframes`, lalu minta user generate di platform dan mengunduh hasil ke folder `downloads/` paket itu. Hasilnya dimasukkan dengan `film.py adopt` dan dipilih dengan `film.py select ... --keyframe` (lihat skill `film-edit`). Tahap ini dianggap `approved` setelah keyframe di-review, atau setelah user menyatakan puas. Lanjut ke `film-motion` (prompt motion boleh ditulis sebelum gambar jadi; beri catatan bahwa prompt bisa disesuaikan setelah gambar ada).
