# Format file proyek film

Semua file diawali header berikut:

```
# <Judul file> — <Judul film>
Status: draft
```

`Status` bernilai `draft` atau `approved`. File yang isinya berasal dari user (lihat skill `film-import`) punya baris tambahan `Sumber: user` tepat di bawah `Status`. Script `scripts/check_film.py` mem-parse format di bawah, jadi **jangan ubah penanda (`<!-- LOCK:... -->`, kolom tabel, heading `## Sxx`)**.

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
- Generator: flow
- Model video: Veo 3 Fast (draf), Veo 3 Quality (final)
- Audio native: ya

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
- `Batas klip`: durasi maksimum satu generate di generator yang dipilih (default 8).
- `Mode narasi`: `in-video` (model video membacakan narasi di dalam klip) atau `terpisah` (narasi direkam/TTS terpisah lalu digabung saat editing; lebih konsisten untuk narasi panjang). Wajib `terpisah` kalau `Audio native: tidak`.
- `Generator`: platform produksi, sesuai nama file profil di `references/generators/` (`flow`, `higgsfield`) atau nama bebas (pakai `generic.md`). Default `flow` kalau field tidak ada.
- `Model video`: model yang dipakai di platform itu. Opsional, tapi dianjurkan untuk agregator seperti Higgsfield.
- `Audio native`: `ya` kalau model membuat dialog/SFX di dalam klip, `tidak` kalau klip bisu (dialog dibuat di tahap edit lewat TTS/rekaman + lip-sync). Default `ya`.
- Nama karakter/lokasi dalam `LOCK:CHAR:<Nama>` / `LOCK:LOC:<Nama>` harus sama persis dengan yang dipakai di kolom shot list.

---

## 02-naskah.md

Format naskah ada di skill `film-naskah`. Tambahan untuk naskah dari user (`Sumber: user`):

- Isi aksi dan dialog adalah milik user. Claude hanya merapikan format, **tidak mengubah kata-kata**.
- Masalah yang ditemukan Claude ditulis di bagian `## Catatan AI` di akhir file, sebagai tabel usulan:

```markdown
## Catatan AI
| # | Scene | Masalah | Usulan | Keputusan |
|---|---|---|---|---|
| 1 | 3 | Dialog Ibu 22 kata, tidak muat satu klip 8 dtk | Pecah jadi 2 shot, atau persingkat: "..." | - |
```

Kolom `Keputusan` diisi user (`terima` / `tolak` / catatan). Usulan hanya diterapkan setelah `terima`.

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
Mode: Frames · Frame awal: assets/keyframes/S01.png · Durasi: 6 dtk
Audio: narasi (in-video)
```prompt
...
```
Narasi terpisah: "..."        ← hanya kalau Mode narasi = terpisah
Dialog terpisah: Raka: "..."  ← hanya kalau Audio native = tidak (dibuat saat edit: TTS/rekaman + lip-sync)
Cek take: [ ] wajah konsisten [ ] tangan wajar [ ] tidak ada teks [ ] audio sinkron
Take terpilih: -
```

Di akhir file ada bagian `## Catatan edit` (urutan klip, transisi, musik, overlay teks, file narasi).

Baris `Mode` boleh memakai nama fitur di UI generator (misalnya `Mode Flow: Frames to Video`), asalkan mode generiknya jelas. Kalau `Audio native: tidak`, prompt tidak boleh berisi dialog atau narator; tulis `Silent clip, no dialogue, no voice-over.`

---

## 06-edit.md

Dibuat oleh skill `film-edit`. Dua tabel dibaca oleh `scripts/film.py`, jadi kolomnya harus persis.

```markdown
# Edit — Pulang
Status: draft

## Urutan edit
| Shot | Potong video | Audio | Transisi | Catatan |
|---|---|---|---|---|
| S01 | 0-1.7, 2.4-7 | 0-6.3 | cut | buang morph di 1,8–2,3 |
| S03 | 1-5 | klip | cut | |
| S02 | 0-6.5 | klip | dissolve 1 | senja ke malam |
| S04 | 1-6 | mute | cut | |

## Lapisan audio
| File | Mulai | Volume | Catatan |
|---|---|---|---|
| assets/audio/N01.mp3 | 0.5 | 1 | narasi |
| assets/audio/music.mp3 | 0 | 0.25 | musik, fade out otomatis di akhir |

## Log take
| Shot | Take | Jenis | File | Generator | Model | Kredit | Status | Catatan |
|---|---|---|---|---|---|---|---|---|
| S01 | 1 | klip | assets/clips/S01_t1.mp4 | flow | Veo 3 Fast | 20 | terpilih | |
```

Aturan kolom:
- **Urutan edit**: urutan baris = urutan di timeline. Shot boleh diurutkan ulang atau dilewati.
  - `Potong video`: satu atau beberapa rentang `awal-akhir` (detik, titik atau koma desimal boleh), dipisah `, `. Kosong/`-` = seluruh klip.
  - `Audio`: `klip` (audio klip mengikuti potongan video), rentang `awal-akhir` dari klip (dipakai utuh walau video dipotong-potong), atau `mute` (bisu; untuk klip tanpa audio native atau audio yang diganti).
  - `Transisi`: transisi ke shot **berikutnya**: `cut` atau `dissolve <detik>`.
- **Lapisan audio** (opsional): file audio yang ditumpuk di atas timeline (narasi terpisah, dialog TTS/lip-sync, musik). `Mulai` dalam detik dari awal video; `Volume` 0–1.
- **Log take**: ditulis oleh `film.py adopt` dan `film.py select`. User boleh mengisi `Kredit` dan `Catatan`. `Status`: `kandidat`, `terpilih`, `ditolak`.
