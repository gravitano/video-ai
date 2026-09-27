---
name: film-shotlist
description: Tahap 3 pipeline film AI — memecah naskah menjadi shot list (03-shotlist.md) per klip Google Flow, lengkap dengan durasi, kamera, aksi, karakter, lokasi, audio, dan mode Flow (Frames/Ingredients/Text/Extend). Ini tahap "naskah to prompt plan". Pakai saat user minta "breakdown naskah", "bikin shot list/storyboard", "naskah jadi prompt", atau lanjutan setelah film-naskah.
---

# Tahap 3 — Naskah → Shot list

Baca `.claude/skills/film-studio/references/formats.md` (format tabel wajib) dan `references/flow-guide.md` (mode Flow dan batas klip). Input: `01-bible.md` dan `02-naskah.md`. Output: `films/<slug>/03-shotlist.md`.

## Aturan pemecahan

1. **Satu shot = satu generate di Flow.** Durasi ≤ `Batas klip` di bible (default 8). Aksi yang lebih panjang dipecah menjadi beberapa shot dengan sudut berbeda (lebih sinematik), atau shot kedua ber-mode `Extend` kalau harus kontinu.
2. **Satu aksi utama per shot** dan **maksimal satu pembicara per shot**. Dialog bolak-balik dipecah menjadi shot/reverse-shot (S05 Raka bicara, S06 Ibu menjawab).
3. **Durasi mengikuti audio.** Durasi shot dengan dialog/narasi ≥ (jumlah kata ÷ 2,2) + 1,5 detik jeda. Shot tanpa suara 3–6 detik.
4. **Variasi shot:** buka scene dengan wide/establishing, lalu medium, lalu close-up untuk emosi. Hindari lebih dari 3 close-up berturut-turut.
5. **Kamera ditulis konkret:** jenis shot (EWS/WS/MS/MCU/CU/ECU/OTS/POV) + gerak (static, slow dolly in, pan left, handheld, crane up, orbit). Maksimal satu gerak kamera per shot.
6. **Pilih mode Flow:**
   - `Frames` (default) untuk shot yang menampilkan karakter utama.
   - `Ingredients` kalau komposisi sulit dibuat sebagai frame awal (karakter masuk frame dari luar, gerak kamera besar), atau user ingin cepat tanpa keyframe.
   - `Text` untuk establishing, landscape, atau B-roll tanpa karakter utama.
   - `Extend` hanya untuk melanjutkan shot tepat sebelumnya.
7. **Overlay teks** (judul, lokasi/waktu) tidak masuk kolom visual. Tulis di bagian catatan di bawah tabel.
8. Kalau mode narasi `terpisah`, kolom Audio tetap berisi narasinya, dengan awalan `Narator (terpisah):`.

## Isi file

```markdown
# Shot list — <Judul>
Status: draft

Total: 18 shot · 92 dtk (target 90) · Rasio 16:9

| Shot | Scene | Durasi | Kamera | Aksi / visual | Karakter | Lokasi | Audio | Mode |
|---|---|---|---|---|---|---|---|---|
| S01 | 1 | 5 | EWS, static | Bus tua berhenti di terminal sepi, hujan deras | - | Terminal | SFX hujan, mesin bus | Text |
| S02 | 1 | 7 | MS, slow push in | Raka turun dari bus, menatap sekitar | Raka | Terminal | Narator: "Sepuluh tahun dia tidak pulang." | Frames |
...

## Catatan
- Overlay: "Jawa Tengah, 2019" di S01.
- Transisi: ...
- Musik: ...
```

## Validasi

Jalankan `python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>` lalu perbaiki semua ERROR (durasi total, durasi melebihi batas klip, nama karakter atau lokasi yang tidak ada di bible).

## Gate

Tampilkan tabel ke user beserta total durasi dan jumlah shot per mode (misalnya "14 Frames, 3 Text, 1 Extend", berguna untuk memperkirakan kredit Flow). Setelah disetujui, set `Status: approved` dan sarankan lanjut ke `film-keyframe`.
