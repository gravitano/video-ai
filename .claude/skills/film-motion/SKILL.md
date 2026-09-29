---
name: film-motion
description: Tahap 5 pipeline film AI — menulis prompt image-to-video untuk generator video (Flow/Veo, Higgsfield, dll.) (05-motion.md) per shot, lengkap dengan dialog, narasi, SFX, arahan suara, checklist take, dan catatan edit. Pakai saat user minta "prompt video", "image to video", "prompt motion", "prompt dialog/narasi", "animasikan keyframe", atau lanjutan setelah film-keyframe.
---

# Tahap 5 — Image → Video + narasi/dialog

Baca `.claude/skills/film-studio/references/formats.md` dan `.claude/skills/film-studio/references/prompting.md` dan profil generator `references/generators/<Generator>.md` sesuai bible (bagian Mode, Audio, Struktur prompt; sintaks audio per platform ada di profil). Input: `01-bible.md`, `03-shotlist.md`, `04-keyframes.md`, dan gambar di `assets/keyframes/` kalau sudah ada. Output: `films/<slug>/05-motion.md`.

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

- **`Audio native: tidak`**: jangan tulis dialog atau narasi di prompt. Tulis `Silent clip, no dialogue, no voice-over.` (SFX juga tidak akan muncul; catat SFX di baris Audio untuk ditambahkan saat edit). Dialog dipindah ke baris `Dialog terpisah: <Nama>: "<dialog>"` di bawah blok prompt, dan gerak mulut ditulis di prompt (`he speaks softly, lips moving naturally`) supaya lip-sync di tahap edit lebih mudah.
- **Naskah `Sumber: user`**: dialog dan narasi disalin **persis** dari `02-naskah.md`. Kalau terlalu panjang untuk durasi shot, jangan dipersingkat sendiri; ajukan lewat Catatan AI di naskah.

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
3. Serahkan ke user: buat paket upload dengan `python3 .claude/skills/film-studio/scripts/film.py handoff films/<slug>`, jelaskan urutan kerja di UI dari profil generator (pilih mode → upload frame/ingredient → tempel prompt → generate 2–4 take, model murah dulu), dan minta hasil diunduh ke `downloads/` dengan nama diawali ID shot. Lanjut ke `film-edit` untuk adopt, review take, dan rough cut.
4. Kalau user melaporkan take yang gagal, diagnosis dengan tabel "Masalah umum" di `references/prompting.md`, lalu revisi prompt shot itu saja.
