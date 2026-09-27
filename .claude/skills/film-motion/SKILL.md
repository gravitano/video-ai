---
name: film-motion
description: Tahap 5 pipeline film AI — menulis prompt image-to-video untuk Google Flow/Veo (05-motion.md) per shot, lengkap dengan dialog, narasi, SFX, arahan suara, checklist take, dan catatan edit. Pakai saat user minta "prompt video", "image to video", "prompt motion", "prompt dialog/narasi", "animasikan keyframe", atau lanjutan setelah film-keyframe.
---

# Tahap 5 — Image → Video + narasi/dialog

Baca `.claude/skills/film-studio/references/formats.md` dan `references/flow-guide.md` (bagian Mode, Audio native, Struktur prompt). Input: `01-bible.md`, `03-shotlist.md`, `04-keyframes.md`, dan gambar di `assets/keyframes/` kalau sudah ada. Output: `films/<slug>/05-motion.md`.

## Kalau keyframe sudah ada

Buka (Read) setiap `assets/keyframes/Sxx.*` sebelum menulis prompt shot itu. Deskripsi gerak harus cocok dengan yang **benar-benar** ada di gambar: posisi karakter, arah pandang, dan benda yang dipegang. Kalau keyframe belum ada, tulis prompt dari shot list dan beri catatan `(belum dicek terhadap keyframe)` di baris Mode.

## Prompt per mode

**Frames** (paling sering). Fokus pada gerak; jangan mendeskripsikan ulang penampilan:
```
<Gerak subjek berurutan dengan tempo: "Raka slowly lowers his bag, then looks up toward the warung.">. Camera: <satu gerak kamera>. Environment: <hujan, asap, cahaya berkedip, figuran>. <AUDIO>. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```

**Ingredients / Text**: tidak ada frame, jadi tulis lengkap:
```
<LOCK:STYLE>. <Shot type & kamera>. <LOCK:CHAR ...> <aksi>. <LOCK:LOC ...> <waktu/cahaya>. <AUDIO>. Single continuous shot. No cuts, no subtitles, no on-screen text.
```
Sebutkan ingredient yang diupload di baris Mode.

**Extend**: prompt singkat berisi kelanjutan aksi dan audio. Tulis "continues seamlessly from the previous clip".

## Blok AUDIO

Susun dari kolom Audio di shot list:
- **Dialog**: `<Nama> says in Indonesian, <LOCK:VOICE verbatim>: "<dialog>"`. Tambahkan arahan emosi dari parenthetical naskah ("quietly, holding back tears").
- **Narasi, mode `in-video`**: `Narrator voice-over in Indonesian, <LOCK:VOICE:Narator verbatim>: "<narasi>"`.
- **Narasi, mode `terpisah`**: jangan masukkan narasi ke prompt. Tulis `No dialogue, no voice-over.` dan pindahkan narasinya ke baris `Narasi terpisah:` di bawah blok.
- **SFX/ambience**: `Sound: <suara spesifik>.` Selalu tutup dengan `No music.` kecuali user meminta musik di klip.
- **Timing**: untuk shot yang dimulai dengan aksi, tulis "He speaks after a short pause" supaya dialog tidak terpotong di awal klip.

Batas panjang: jumlah kata dalam tanda kutip ≤ durasi shot × 2,2. Kalau lebih, persingkat dialognya (beri tahu user bahwa naskah berubah) atau pecah shot-nya.

## Isi file

Per shot mengikuti format di `formats.md` (heading `## Sxx — judul`, baris Mode, baris Audio, satu blok ```` ```prompt ````, lalu `Cek take` dan `Take terpilih`).

Tutup file dengan:

```markdown
## Catatan edit
- Urutan klip: S01 → S18 (file assets/clips/Sxx.mp4)
- Trim: potong 0,5 dtk awal/akhir klip yang geraknya "mulai dari diam"
- Transisi: ...
- Overlay teks: ...
- Musik: ... (masuk di S.., keluar di S..)
- Narasi terpisah: daftar baris + file assets/audio/Nxx.mp3 (kalau mode terpisah)
- Color: samakan grade antar shot; acuan = S02
- Export: 1920×1080 (16:9) atau 1080×1920 (9:16), 24/30 fps, H.264
```

Kalau mode narasi `terpisah`, tawarkan untuk membuat file TTS (misalnya `edge-tts` dengan voice dari bible atau persona). Jangan langsung menjalankannya tanpa persetujuan user.

## Validasi dan gate

1. `python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>`: perbaiki semua ERROR, dan tinjau WARN.
2. Delegasikan ke subagent `film-continuity-reviewer` untuk review menyeluruh, lalu terapkan temuan yang valid.
3. Serahkan ke user dengan urutan kerja di Flow: buka Scenebuilder → per shot pilih mode → upload frame/ingredient → tempel prompt → generate 2–4 take (pakai model Fast dulu) → simpan `assets/clips/Sxx_t1.mp4` dan seterusnya → take terpilih disalin sebagai `Sxx.mp4`.
4. Kalau user melaporkan take yang gagal, diagnosis dengan tabel "Masalah umum" di flow-guide, lalu revisi prompt shot itu saja.
