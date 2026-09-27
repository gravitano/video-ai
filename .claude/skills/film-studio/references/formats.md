# Format file proyek film

Semua file diawali header berikut:

```
# <Judul file> — <Judul film>
Status: draft
```

`Status` bernilai `draft` atau `approved`. Script `scripts/check_film.py` mem-parse format di bawah, jadi **jangan ubah penanda (`<!-- LOCK:... -->`, kolom tabel, heading `## Sxx`)**.

---

## 01-bible.md

Setiap LOCK adalah komentar HTML yang **langsung** diikuti blok ```` ```text ````. Isi LOCK ditulis dalam bahasa Inggris (prompt), 1–3 kalimat padat, lalu disalin **verbatim** ke prompt.

```markdown
# Bible — Pulang
Status: draft

## Format
- Rasio: 16:9
- Durasi target: 90
- Batas klip: 8
- Bahasa dialog: Indonesia
- Mode narasi: in-video

## Style
<!-- LOCK:STYLE -->
```text
Cinematic 35mm film look, warm tungsten practical lighting, teal-orange grade, shallow depth of field, subtle film grain, realistic.
```

## Karakter
### Raka
Peran: anak rantau yang pulang setelah 10 tahun. Busur: kaku → luluh.
<!-- LOCK:CHAR:Raka -->
```text
Raka, a 30-year-old Indonesian man, lean build, short slightly messy black hair, light stubble, tired brown eyes, wearing a faded navy denim jacket over a plain white t-shirt, dark jeans.
```
<!-- LOCK:VOICE:Raka -->
```text
calm low male voice, speaks Indonesian with a soft Javanese accent, measured pace
```

## Lokasi
### Warung
<!-- LOCK:LOC:Warung -->
```text
a small old roadside warung in a Central Javanese village at night, wooden benches, glass jars of snacks, a single hanging bulb, rain on a tin roof.
```

## Narator (opsional)
<!-- LOCK:VOICE:Narator -->
```text
warm mature female narrator voice, Indonesian, gentle and unhurried
```

## Aturan tetap
- Tidak ada teks, logo, atau subtitle di gambar/video; semua teks ditambahkan saat editing.
- ...
```

Aturan field:
- `Rasio`: `16:9` atau `9:16`.
- `Durasi target`: angka dalam detik.
- `Batas klip`: durasi maksimum satu generate di Flow (default 8).
- `Mode narasi`: `in-video` (Veo membacakan narasi di dalam klip) atau `terpisah` (narasi direkam/TTS terpisah lalu digabung saat editing; lebih konsisten untuk narasi panjang).
- Nama karakter/lokasi dalam `LOCK:CHAR:<Nama>` / `LOCK:LOC:<Nama>` harus sama persis dengan yang dipakai di kolom shot list.

---

## 03-shotlist.md

Satu tabel dengan kolom **persis** seperti ini (urutan penting):

```markdown
| Shot | Scene | Durasi | Kamera | Aksi / visual | Karakter | Lokasi | Audio | Mode |
|---|---|---|---|---|---|---|---|---|
| S01 | 1 | 6 | Wide, static | Raka turun dari bus, hujan | Raka | Terminal | Narator: "Sepuluh tahun..." | Frames |
| S02 | 1 | 8 | MCU, slow dolly in | Raka menatap warung | Raka | Warung | SFX hujan | Frames |
```

- `Shot`: `S01`, `S02`, ... (dua digit, berurutan).
- `Durasi`: angka detik, ≤ `Batas klip`.
- `Karakter` / `Lokasi`: nama dari bible, dipisah koma; `-` kalau tidak ada.
- `Audio`: ringkas; `Nama: "dialog"`, `Narator: "..."`, `SFX ...`, atau `-`.
- `Mode`: salah satu `Frames` (Frames to Video dari keyframe), `Ingredients` (Ingredients to Video dari gambar referensi), `Text` (Text to Video), `Extend` (lanjutan klip sebelumnya).

Di bawah tabel boleh ada catatan bebas (transisi, musik, overlay teks).

---

## 04-keyframes.md

Dua bagian: ingredients (dibuat sekali) lalu keyframe per shot.

```markdown
## Ingredients

### CHAR-Raka
File: assets/ingredients/CHAR-Raka.png
```prompt
Character reference sheet ... <LOCK:CHAR:Raka verbatim> ... <LOCK:STYLE verbatim> ...
```

### LOC-Warung
File: assets/ingredients/LOC-Warung.png
```prompt
...
```

## Keyframes

## S01 — Raka turun dari bus
File: assets/keyframes/S01.png · Referensi: CHAR-Raka, LOC-Terminal
```prompt
...
```
```

- Heading shot **harus** `## Sxx — <judul>`.
- Satu blok ```` ```prompt ```` per shot/ingredient.
- Shot dengan mode `Text` boleh tidak punya keyframe; tulis `Tidak perlu keyframe (mode Text).` tanpa blok prompt.
- Shot dengan mode `Extend` tidak butuh keyframe.

---

## 05-motion.md

```markdown
## S01 — Raka turun dari bus
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S01.png · Durasi: 6 dtk
Audio: narasi (in-video)
```prompt
...
```
Narasi terpisah: "..."        ← hanya kalau Mode narasi = terpisah
Cek take: [ ] wajah konsisten [ ] tangan wajar [ ] tidak ada teks [ ] audio sinkron
Take terpilih: -
```

Di akhir file ada bagian `## Catatan edit` (urutan klip, transisi, musik, overlay teks, file narasi).
