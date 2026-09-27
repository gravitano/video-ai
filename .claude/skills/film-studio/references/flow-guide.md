# Panduan Google Flow untuk pipeline ini

Flow (labs.google/flow) adalah tool pembuatan film dari Google yang memakai model video **Veo** dan model gambar Google (Imagen / Gemini image). Fiturnya sering berubah. Kalau user melaporkan UI atau batasan yang berbeda, **ikuti laporan user** dan sesuaikan `Batas klip` di bible.

## Mode pembuatan video

| Mode | Input | Kapan dipakai |
|---|---|---|
| **Text to Video** | prompt saja | Establishing shot, B-roll tanpa karakter utama |
| **Frames to Video** | frame awal (dan opsional frame akhir) + prompt | **Default untuk shot berkarakter.** Konsistensi paling tinggi karena komposisi sudah dikunci keyframe |
| **Ingredients to Video** | beberapa gambar referensi (karakter, objek, lokasi) + prompt | Shot dengan gerak besar atau komposisi yang sulit dibuat sebagai keyframe; karakter tetap dikenali dari referensi |
| **Extend** (di Scenebuilder) | klip sebelumnya | Melanjutkan aksi lebih dari satu batas klip tanpa putus |
| **Jump to** (di Scenebuilder) | klip sebelumnya | Shot baru di lokasi atau adegan berbeda dengan karakter yang sama |

Lainnya:
- **Camera controls**: preset gerak kamera. Tetap tulis gerak kamera di prompt juga.
- Satu generate menghasilkan klip pendek (umumnya **8 detik**). Shot yang lebih panjang dipecah atau diteruskan dengan Extend.
- Model *Fast* lebih murah kreditnya; model *Quality* untuk take final. Sarankan eksperimen dengan Fast dulu.
- Rasio 16:9 (film/YouTube) atau 9:16 (Reels/Shorts). Keyframe **harus** berasio sama dengan video.

## Gambar (keyframe & ingredients)

- Generate di Flow sendiri (menu gambar) atau di Gemini app, lalu upload. Selalu sertakan gambar ingredient karakter sebagai referensi saat membuat keyframe supaya wajah dan baju konsisten.
- Buat **character sheet** dulu: satu gambar, latar polos netral, tampak depan dan 3/4, full body. Ini jadi acuan semua shot.
- Hindari teks di gambar. Model video cenderung merusak teks, dan teks yang berubah-ubah terlihat jelas "AI".
- Keyframe = **frame pertama** shot. Tulis pose atau keadaan di *awal* aksi, bukan di tengah atau akhir.

## Audio native (dialog, narasi, SFX)

Veo menghasilkan audio bersama video. Sintaks yang andal:

```
Raka says in Indonesian, in a calm low voice: "Bu, aku pulang."
Narrator voice-over in Indonesian, warm mature female voice: "Sepuluh tahun dia pergi."
Sound: heavy rain on a tin roof, distant thunder. No music.
```

Aturan:
- **Satu pembicara per klip** kalau bisa. Dua pembicara dalam 8 detik sering tertukar suaranya.
- Panjang dialog: bahasa Indonesia sekitar **2–2,5 kata per detik**. Klip 8 detik → **maksimal ±16 kata**, idealnya 8–14 supaya ada jeda sebelum dan sesudah bicara.
- Sebutkan bahasa (`in Indonesian`) dan deskripsi suara dari `LOCK:VOICE`. Suara Veo tidak konsisten antar-klip; deskripsi yang sama persis membantu, tapi tidak menjamin.
- Selalu tambahkan `No subtitles, no on-screen text.` Veo kadang menambahkan caption sendiri.
- Tulis musik secara eksplisit (`No music` atau `soft piano score`). Lebih baik **tanpa musik** di klip, lalu musik ditambahkan saat editing supaya tidak terpotong-potong antar shot.
- Nama diri dan istilah asing bisa salah ucap. Tulis fonetis kalau perlu, atau pakai mode narasi `terpisah`.

**Mode narasi `terpisah`**: narasi panjang atau yang melintasi beberapa shot direkam atau di-TTS terpisah (misalnya ElevenLabs, atau `edge-tts` dengan voice `id-ID-GadisNeural` / `id-ID-ArdiNeural` seperti di `personas/`). Klip video cukup berisi ambience/SFX (`No dialogue, no voice-over.`).

## Struktur prompt

**Keyframe (gambar)**
```
[LOCK:STYLE]. [Shot type & lensa & sudut]. [LOCK:CHAR ...] [pose/ekspresi di awal shot]. [LOCK:LOC ...] [waktu & cahaya]. [komposisi, ruang kosong]. Aspect ratio [rasio]. No text, no captions, no logos, no watermark.
```

**Image-to-video (Frames)**: fokus pada **gerak**, karena tampilan sudah ada di gambar.
```
[Gerak subjek, berurutan dengan tempo]. Camera: [gerak kamera]. Environment: [gerak lingkungan]. [Audio: dialog/narasi/SFX]. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion. No cuts, no scene transition, no subtitles, no on-screen text.
```

**Ingredients / Text to Video**: tidak ada frame yang mengunci tampilan, jadi sertakan **LOCK:STYLE + LOCK:CHAR + LOCK:LOC lengkap** ditambah gerak dan audio.

## Masalah umum dan solusinya

| Gejala | Solusi |
|---|---|
| Wajah berubah antar shot | Pakai Frames to Video dari keyframe yang dibuat dengan referensi CHAR; salin LOCK verbatim; kurangi close-up ekstrem |
| Tangan atau jari aneh | Kurangi aksi tangan yang detail; tangan di luar frame atau memegang benda sederhana |
| Muncul teks atau subtitle | Tambahkan `No subtitles, no on-screen text`; regenerate |
| Kamera "melompat" atau ada cut | `No cuts, single continuous shot`; gerak kamera satu jenis saja |
| Dialog terpotong | Kurangi kata; tambahkan `he speaks right after the first second` |
| Suara karakter beda-beda | Deskripsi VOICE identik; atau dubbing/TTS saat editing |
| Gerak terlalu lambat atau diam | Tulis kata kerja aksi yang jelas dan urutannya (`first..., then...`) |
| Banyak orang atau adegan kacau | Maksimal 2 karakter utama per shot; figuran ditulis `blurred background people` |
