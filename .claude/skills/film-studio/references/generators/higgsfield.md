# Generator: Higgsfield (`Generator: higgsfield`)

Higgsfield (higgsfield.ai) adalah **agregator**: satu langganan untuk banyak model video (antara lain Veo, Kling, Sora, Seedance, WAN, MiniMax, dan model milik Higgsfield sendiri) dan model gambar. Karena itu **kemampuan tergantung model yang dipilih**, bukan platformnya. Katalog dan batasan model sering berubah; tanyakan user model apa yang dipakai, lalu cek di UI sebelum menetapkan nilai bible.

Aturan umum prompt ada di `../prompting.md`. File ini hanya berisi hal yang khusus Higgsfield.

## Nilai bible

- `Model video:` isi dengan model yang dipakai untuk take final (misalnya `Veo 3.1`, `Kling 3.0`). Satu model untuk seluruh film supaya gaya gerak dan warna konsisten.
- `Batas klip:` ikuti durasi maksimum model itu di UI.
- `Audio native:` `ya` hanya kalau model itu membuat audio (dan toggle audio dinyalakan). Kalau ragu, pakai `tidak`, lalu dialog dibuat di tahap edit (TTS + **Lipsync Studio** Higgsfield, atau alat lip-sync lain).

## Pemetaan mode

| Mode generik | Di Higgsfield | Catatan |
|---|---|---|
| `Frames` | **Image to Video** dengan **Start Frame** (opsional End Frame) | Upload keyframe sebagai start frame |
| `Ingredients` | Generasi berbasis **referensi** (nama fitur beda per model) | Kalau model yang dipilih tidak punya fitur referensi, ubah shot menjadi `Frames` |
| `Text` | **Text to Video** | |
| `Extend` | **Video continuation / extend** dari klip sebelumnya | Tidak semua model mendukung; kalau tidak, pecah jadi dua shot `Frames` |

## Tips

- Model gambar Higgsfield (misalnya Soul, Nano Banana Pro) bisa dipakai untuk character sheet dan keyframe. Tetap upload character sheet sebagai referensi di setiap keyframe.
- Kalau `Audio native: ya`, pakai sintaks audio yang sama seperti di `flow.md` (dialog dalam tanda kutip + deskripsi suara + `Sound:` + `No music`). Hasilnya tergantung model.
- Matikan *prompt enhancer* / auto-improve kalau ada, supaya kalimat LOCK dan batasan `No text` tidak diubah.
- Catat kredit per generate di log take (`film.py adopt --credits`), karena biaya berbeda per model.

## Alur kerja di UI

Pilih model → mode Image to Video → upload `Sxx.jpg` dari `handoff/higgsfield/` sebagai start frame → tempel `Sxx.txt` → generate 2–4 take → unduh ke `handoff/higgsfield/downloads/` dengan nama diawali ID shot → `film.py adopt`.
