# Generator: Google Flow (`Generator: flow`)

Flow (labs.google/flow) memakai model video **Veo** dan model gambar Google (Imagen / Gemini image). Fiturnya sering berubah. Kalau user melaporkan UI atau batasan yang berbeda, **ikuti laporan user** dan sesuaikan `Batas klip` di bible.

Aturan umum prompt ada di `../prompting.md`. File ini hanya berisi hal yang khusus Flow.

## Nilai bible yang disarankan

- `Batas klip: 8`
- `Audio native: ya`

## Pemetaan mode

| Mode generik | Di Flow | Catatan |
|---|---|---|
| `Frames` | **Frames to Video** | Upload keyframe sebagai frame awal; frame akhir opsional |
| `Ingredients` | **Ingredients to Video** | Upload beberapa gambar referensi (karakter, lokasi, objek) |
| `Text` | **Text to Video** | Prompt saja |
| `Extend` | **Extend** di Scenebuilder | Melanjutkan klip sebelumnya tanpa putus |

Lainnya:
- **Jump to** (Scenebuilder): shot baru dengan karakter yang sama. Tidak dipakai di pipeline ini karena keyframe + `Frames` lebih terkontrol.
- **Camera controls**: preset gerak kamera. Tetap tulis gerak kamera di prompt juga.
- Model *Fast* lebih murah kreditnya; model *Quality* untuk take final. Eksperimen dengan Fast dulu.
- Rasio 16:9 atau 9:16, set sebelum generate.

## Gambar

Generate di Flow sendiri (menu gambar) atau di Gemini app, lalu upload. Sertakan gambar ingredient karakter sebagai referensi saat membuat keyframe.

## Sintaks audio Veo

```
Raka says in Indonesian, in a calm low voice: "Bu, aku pulang."
Narrator voice-over in Indonesian, warm mature female voice: "Sepuluh tahun dia pergi."
Sound: heavy rain on a tin roof, distant thunder. No music.
```

- Selalu tambahkan `No subtitles, no on-screen text.` Veo kadang menambahkan caption sendiri.
- Nama diri dan istilah asing bisa salah ucap. Tulis fonetis kalau perlu, atau pakai mode narasi `terpisah`.

## Alur kerja di UI

Buka Scenebuilder → per shot pilih mode → upload frame/ingredient → tempel prompt → generate 2–4 take (Fast dulu) → unduh ke `handoff/flow/downloads/` dengan nama diawali ID shot → `film.py adopt`.
