---
name: film-naskah
description: Tahap 2 pipeline film AI — menulis naskah (02-naskah.md) per scene dengan aksi, dialog, dan narasi dari brief dan bible yang sudah disetujui, dengan panjang dialog yang realistis untuk klip Google Flow. Pakai saat user minta "tulis naskah", "bikin script/skenario", "revisi dialog", atau lanjutan setelah film-ide.
---

# Tahap 2 — Brief → Naskah

Input: `00-brief.md` dan `01-bible.md` (seharusnya `Status: approved`; kalau masih draft, konfirmasi dulu ke user). Output: `films/<slug>/02-naskah.md`.

## Hitung anggaran dulu

- **Jumlah shot kasar** = durasi target ÷ ±5 detik (film AI terasa hidup dengan shot 3–8 detik). Contoh: 90 detik → 15–20 shot.
- **Anggaran kata bicara** (dialog + narasi) ≈ durasi total × 1,5 kata/detik. Jangan semua detik diisi suara; film butuh jeda. 90 detik → maksimal ±135 kata.
- Satu baris dialog sebaiknya **≤ 14 kata** supaya muat dalam satu klip Flow bersama aksinya. Kalimat panjang dipecah ke beberapa shot atau diganti dengan aksi.

## Struktur cerita

Pilih sesuai genre di brief:
- **Short movie naratif**: Setup (±20%) → Insiden pemicu → Konfrontasi/eskalasi (±50%) → Klimaks → Resolusi, ditutup dengan gambar akhir yang kuat.
- **Promo/edukasi (S.C.E.N.E.)**: Hook (≤3 dtk) → Problem → Escalation → Solution → How it works → Payoff → CTA.
- **Mood piece/puisi visual**: rangkaian gambar yang dirangkai narasi, dengan 3 babak emosi.

Tulis beat outline singkat (1 baris per beat) di bagian atas naskah.

## Format naskah

```markdown
# Naskah — <Judul>
Status: draft

## Beat outline
1. Setup — ...
2. ...

## SCENE 1 — EXT. TERMINAL BUS — MALAM, HUJAN
Estimasi: 15 dtk · Karakter: Raka · Lokasi: Terminal

Hujan deras. Bus tua berhenti. RAKA (30) turun sambil menenteng tas ransel lusuh, menatap sekeliling.

**NARATOR (V.O.)**
Sepuluh tahun dia tidak pulang.

Raka menarik napas, lalu berjalan ke arah cahaya warung di ujung jalan.

## SCENE 2 — INT. WARUNG — MALAM
...
**RAKA**
*(pelan)*
Bu... aku pulang.
```

Aturan menulis untuk AI video:
- **Tulis yang terlihat dan terdengar**, bukan isi pikiran. "Raka ragu" → "Raka berhenti di ambang pintu, tangannya menggantung di gagang."
- **Aksi sederhana dan satu per satu.** Hindari perkelahian rumit, kerumunan, tulisan yang harus terbaca, atau tangan yang melakukan gerakan detail (mengetik cepat, main gitar) sebagai momen utama.
- Nama karakter dan lokasi **harus sama** dengan bible. Kalau cerita butuh karakter atau lokasi baru, tambahkan dulu ke bible (dengan LOCK) dan beri tahu user.
- Heading scene memakai format standar `INT./EXT. LOKASI — WAKTU` dan baris `Estimasi` (jumlah estimasi semua scene ≈ durasi target).
- Dialog ditulis dalam bahasa dialog di bible. Parenthetical (`*(berbisik)*`) boleh, karena akan dipakai sebagai arahan suara.
- Teks di layar (judul, keterangan waktu) ditulis sebagai `**OVERLAY:** ...` karena akan ditambahkan di editor, bukan oleh AI.

## Self-check sebelum menyerahkan

- [ ] Total estimasi scene = durasi target (±10%)
- [ ] Jumlah kata bicara ≤ anggaran
- [ ] Tidak ada baris dialog > 14 kata tanpa alasan
- [ ] Semua karakter dan lokasi ada di bible
- [ ] Ending sesuai sinopsis di brief

## Gate

Tampilkan beat outline, jumlah scene, total durasi, dan jumlah kata bicara. Tawarkan untuk membacakan naskah lengkap. Setelah disetujui, set `Status: approved` dan sarankan lanjut ke `film-shotlist`.
