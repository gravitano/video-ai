# Panduan prompt (berlaku untuk semua generator)

Hal yang spesifik per platform (nama mode di UI, batas durasi, sintaks audio) ada di `generators/<Generator>.md` sesuai field `Generator` di bible. Isi file ini berlaku untuk semua platform.

## Empat mode generik

Kolom `Mode` di shot list memakai nama generik. Tiap profil generator memetakan nama ini ke fitur di UI-nya.

| Mode | Artinya | Kapan dipakai |
|---|---|---|
| `Frames` | Image-to-video dari **frame awal** (opsional frame akhir) + prompt | **Default untuk shot berkarakter.** Komposisi dan identitas dikunci keyframe |
| `Ingredients` | Video dari beberapa **gambar referensi** (karakter, lokasi, objek) + prompt, tanpa frame awal | Gerak besar atau komposisi yang sulit dibuat sebagai keyframe |
| `Text` | Text-to-video, prompt saja | Establishing, landscape, B-roll tanpa karakter utama |
| `Extend` | Melanjutkan klip sebelumnya | Aksi kontinu yang melebihi batas klip |

## Gambar (keyframe & ingredients)

- Buat **character sheet** dulu: satu gambar, latar polos netral, tampak depan dan 3/4, full body. Ini jadi acuan semua shot. Selalu sertakan sebagai referensi saat membuat keyframe.
- Buat **location plate** tanpa orang untuk tiap lokasi.
- Keyframe = **frame pertama** shot. Tulis pose atau keadaan di *awal* aksi, bukan di tengah atau akhir.
- Keyframe **harus** berasio sama dengan video.
- Hindari teks di gambar. Model video cenderung merusak teks, dan teks yang berubah-ubah terlihat jelas "AI".

## Audio

Tergantung field `Audio native` di bible:

- **`ya`**: model membuat dialog, narasi, dan SFX di dalam klip. Sintaks per platform ada di profil generator. Aturan umum:
  - **Satu pembicara per klip.** Dua pembicara dalam satu klip sering tertukar suaranya.
  - Bahasa Indonesia sekitar **2–2,5 kata per detik**. Klip 8 detik → maksimal ±16 kata, idealnya 8–14.
  - Sebutkan bahasa (`in Indonesian`) dan deskripsi suara dari `LOCK:VOICE` secara verbatim. Suara tetap bisa berbeda antar-klip; kalau terlalu mengganggu, pakai dubbing/TTS saat editing.
  - Tulis musik secara eksplisit. Lebih baik `No music` di klip, lalu musik ditambahkan saat editing.
- **`tidak`**: prompt video hanya berisi gerak, plus `Silent clip, no dialogue, no voice-over.` Dialog ditulis di baris `Dialog terpisah:` di 05-motion, lalu dibuat di tahap edit: TTS/rekaman + lip-sync (untuk shot yang bibirnya terlihat) atau voice-over (untuk shot tanpa mulut terlihat). Rencanakan shot bicara sebagai close-up yang cocok untuk lip-sync.

**Mode narasi `terpisah`**: narasi direkam atau di-TTS terpisah (misalnya ElevenLabs, atau `edge-tts` dengan voice `id-ID-GadisNeural` / `id-ID-ArdiNeural` seperti di `personas/`). Klip cukup berisi ambience/SFX.

## Struktur prompt

**Keyframe (gambar)**
```
[LOCK:STYLE]. [Shot type & lensa & sudut]. [LOCK:CHAR ...] [pose/ekspresi di awal shot]. [LOCK:LOC ...] [waktu & cahaya]. [komposisi, ruang kosong]. Aspect ratio [rasio]. No text, no captions, no logos, no watermark.
```

**Image-to-video (`Frames`)**: fokus pada **gerak**, karena tampilan sudah ada di gambar.
```
[Gerak subjek, berurutan dengan tempo]. Camera: [gerak kamera]. Environment: [gerak lingkungan]. [Audio]. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```

**`Ingredients` / `Text`**: tidak ada frame yang mengunci tampilan, jadi sertakan **LOCK:STYLE + LOCK:CHAR + LOCK:LOC lengkap** ditambah gerak dan audio.

## Masalah umum dan solusinya

| Gejala | Solusi |
|---|---|
| Wajah berubah antar shot | Pakai `Frames` dari keyframe yang dibuat dengan referensi CHAR; salin LOCK verbatim; kurangi close-up ekstrem |
| Tangan atau jari aneh | Kurangi aksi tangan yang detail; tangan di luar frame atau memegang benda sederhana |
| Muncul teks atau subtitle | Tambahkan `No subtitles, no on-screen text`; regenerate |
| Kamera "melompat" atau ada cut | `No cuts, single continuous shot`; gerak kamera satu jenis saja |
| Dialog terpotong | Kurangi kata; tambahkan `he speaks right after the first second` |
| Suara karakter beda-beda | Deskripsi VOICE identik; atau dubbing/TTS saat editing |
| Gerak terlalu lambat atau diam | Tulis kata kerja aksi yang jelas dan urutannya (`first..., then...`) |
| Banyak orang atau adegan kacau | Maksimal 2 karakter utama per shot; figuran ditulis `blurred background people` |
| Morph/berubah bentuk di tengah klip | Potong bagian itu saat edit, atau regenerate dengan gerak lebih kecil |
