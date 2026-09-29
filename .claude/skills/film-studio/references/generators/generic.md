# Generator lain (`Generator: <nama bebas>`)

Untuk platform yang belum punya profil (Kling, Runway, Luma, Pika, MiniMax/Hailuo, dll.). Aturan umum prompt ada di `../prompting.md`.

## Sebelum tahap 3, tanyakan atau cek ke user

1. **Model** yang dipakai → tulis di `Model video:` bible.
2. **Durasi maksimum** satu generate → `Batas klip:`.
3. Apakah model **membuat audio/dialog** → `Audio native: ya|tidak`.
4. Fitur yang tersedia: start frame (dan end frame), gambar referensi, extend.

## Pemetaan mode

| Mode generik | Cari fitur bernama | Kalau tidak ada |
|---|---|---|
| `Frames` | Image to Video, first frame, start frame | (hampir semua platform punya) |
| `Ingredients` | reference, elements, character reference, subject | Ubah shot menjadi `Frames` |
| `Text` | Text to Video | Buat keyframe lalu `Frames` |
| `Extend` | extend, continue | Pecah menjadi dua shot `Frames`, frame awal shot kedua = frame terakhir shot pertama |

Kalau platform ini dipakai berulang, buat profil baru `generators/<nama>.md` dengan struktur yang sama seperti `flow.md`.
