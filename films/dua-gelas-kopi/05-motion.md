# Motion — Dua Gelas Kopi
Status: draft

> ⚠️ Semua prompt **belum dicek terhadap keyframe**. Setelah `assets/keyframes/` terisi, minta Claude untuk "sesuaikan prompt motion dengan keyframe".

## Cara pakai di Google Flow
1. Buka proyek Flow, lalu pilih rasio **9:16**.
2. Per shot: pilih mode (**Frames to Video**, kecuali S04 yang memakai **Text to Video**), upload `assets/keyframes/Sxx.png` sebagai frame awal, lalu tempel prompt.
3. Pakai model **Fast** untuk mencoba; ulangi dengan model **Quality** untuk take yang sudah pas. Jumlah take yang disarankan tertulis di tiap shot.
4. Unduh semua take ke `assets/clips/Sxx_t1.mp4`, `Sxx_t2.mp4`, dan seterusnya. Salin take terpilih sebagai `assets/clips/Sxx.mp4`.
5. Cek tiap take dengan checklist di bawah prompt. Kalau gagal, ceritakan gejalanya ke Claude untuk revisi prompt shot itu.

## S01 — Raka sendirian di jalan senja
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S01.jpg · Durasi: 6 dtk · Take disarankan: 2
Audio: narasi (in-video)
```prompt
Raka stands still on the road as the distant blue minibus drives away from the camera up the winding road and its red taillights shrink into the dusk. He does not move; only his damp hair stirs in the breeze. Camera: very slow pull back, so he becomes smaller and more alone in the middle of the long wet road. Environment: coconut leaves swaying gently, thin mist drifting over the rice terraces, faint ripples in the puddles. Narrator voice-over in Indonesian, intimate close-mic male voice-over around 30 years old, low and soft-spoken, Indonesian with a light Javanese accent, reflective and slow, speaking softly, like a confession, after about one second: "Sepuluh tahun lalu, aku pergi tanpa pamit." Sound: minibus engine fading into the distance, crickets, water dripping from leaves. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S02 — Raka membetulkan ransel
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S02.jpg (belum dicek terhadap keyframe) · Durasi: 6 dtk · Take disarankan: 2
Audio: narasi (in-video)
```prompt
Raka takes a slow breath, tightens his grip and adjusts the backpack strap on his shoulder, then starts walking slowly toward the right side of the frame and out of frame. Camera: static. Environment: damp air after rain, occasional drops falling from the leaves, blue dusk light. Narrator voice-over in Indonesian, intimate close-mic male voice-over around 30 years old, low and soft-spoken, Indonesian with a light Javanese accent, reflective and slow, speaking quietly, after a short pause: "Terakhir kali, aku membanting pintu dan bilang nggak akan pulang." Sound: footsteps on wet asphalt, drops falling from leaves, crickets. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S03 — Sepatu melewati genangan
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S03.jpg (belum dicek terhadap keyframe) · Durasi: 4 dtk · Take disarankan: 2
Audio: SFX saja
```prompt
The right sneaker steps down into the puddle with a soft splash, shattering the reflection of the blue sky, then the left foot follows, walking from left to right. Camera: low tracking shot moving alongside at ground level at the same speed as the steps. Environment: ripples spreading across the puddle, the sky reflection wobbling. No dialogue, no voice-over. Sound: wet footsteps, a small splash, crickets. No music. Preserve the jeans, sneakers, the location, framing and visual style from the start frame. Keep the camera at ground level; do not reveal the face. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S04 — Warung di kejauhan
Mode Flow: Text to Video (tanpa gambar) · Durasi: 5 dtk · Take disarankan: 2
Audio: SFX saja
```prompt
Cinematic live-action film still, shot on 35mm film with anamorphic-style shallow depth of field, naturalistic Indonesian drama, cool blue dusk tones outside contrasted with warm amber tungsten light, soft film grain, gentle halation, photorealistic, emotionally quiet. Extreme wide shot, 35mm, static, vertical composition. the exterior of a small old wooden roadside coffee warung at night, green-painted wooden plank walls, a rusty corrugated tin roof dripping rainwater, a single bare yellow bulb hanging under the eave, a long wooden bench out front, surrounded by darkness and wet ground. Seen from far across a dark wet road, the warung is a small warm island of light in the lower center of the frame, with vast darkness and faint misty hills above. Rainwater drips steadily from the edge of the tin roof and a moth circles the bulb. No people. No dialogue, no voice-over. Sound: water dripping from the tin roof, crickets and frogs in the rice fields, a distant dog bark. No music. Aspect ratio 9:16. Single continuous shot. No cuts, no subtitles, no on-screen text, no signage lettering.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S05 — Raka menatap warung dari gelap
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S05.jpg (belum dicek terhadap keyframe) · Durasi: 6 dtk · Take disarankan: 2
Audio: narasi (in-video)
```prompt
Raka stands still, eyes fixed on the distant warung light; his chest rises with a slow breath and his expression softens with longing. Camera: very slow push in toward his face. Environment: faint mist drifting between him and the distant light, the warm glow flickering softly on his face. Raka's lips stay closed and still; the narration is an off-screen inner voice-over, not spoken by him. Narrator voice-over in Indonesian, intimate close-mic male voice-over around 30 years old, low and soft-spoken, Indonesian with a light Javanese accent, reflective and slow, speaking in a near whisper, after a short pause: "Lampunya... masih sama." Sound: crickets, water dripping. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S06 — Ibu menuang air ke dua gelas
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S06.jpg (belum dicek terhadap keyframe) · Durasi: 6 dtk · Take disarankan: 4
Audio: SFX saja
```prompt
Ibu Sarmi slowly tilts the kettle and pours hot water into the first glass mug, then moves to the second glass and fills it too; the dark coffee rises in each glass as it fills and steam billows up from both. Her movements are calm, slow and practiced. Camera: static. Environment: steam curling in the warm bulb light, the small kerosene stove flame flickering in the background. No dialogue, no voice-over. Sound: hot water pouring into glass, soft hiss of the kerosene stove, rain dripping outside. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S07 — Gelas di depan bangku kosong
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S07.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 3
Audio: SFX saja
```prompt
Ibu Sarmi gently sets the glass mug and its saucer down on the table in front of the empty bench, then carefully nudges it a little closer to the edge of the table, as if someone is about to sit there, and slowly withdraws her hands. Camera: slow push in toward the glass. Environment: steam rising and curling. No dialogue, no voice-over. Sound: glass softly touching the saucer, a faint creak of the wooden table. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S08 — Mata Raka berkaca-kaca
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S08.jpg (belum dicek terhadap keyframe) · Durasi: 6 dtk · Take disarankan: 3
Audio: narasi (in-video)
```prompt
Raka stands still; his eyes slowly fill with tears, he blinks once and swallows hard, holding back from crying. Camera: static. Environment: warm light flickering faintly on his face, mist in the dark behind him. Raka's lips stay closed and still; the narration is an off-screen inner voice-over, not spoken by him. Narrator voice-over in Indonesian, intimate close-mic male voice-over around 30 years old, low and soft-spoken, Indonesian with a light Javanese accent, reflective and slow, speaking with a slight tremble, after a short pause: "Aku baru tahu... setiap malam Ibu menyeduh dua gelas." Sound: crickets, water dripping. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S09 — Raka menunduk dan berbalik pergi
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S09.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 2
Audio: narasi (in-video)
```prompt
Raka exhales slowly with his head bowed, then turns his body away from the warung light and begins to walk toward the left into the darkness. Camera: static. Environment: cool blue night, the warm glow far behind him. Raka's lips stay closed and still; the narration is an off-screen inner voice-over, not spoken by him. Narrator voice-over in Indonesian, intimate close-mic male voice-over around 30 years old, low and soft-spoken, Indonesian with a light Javanese accent, reflective and slow, speaking heavily, as he turns away: "Aku belum pantas pulang." Sound: footsteps on the wet road, crickets. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S10 — Ibu menatap bangku kosong
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S10.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 3
Audio: dialog Ibu
```prompt
Ibu Sarmi gazes at the empty bench and the second glass as its last thin wisp of steam fades; she smiles sadly, speaks softly toward the empty seat, then lowers her eyes. Camera: static. Environment: the bulb glowing steadily, deep shadows. Ibu Sarmi says in Indonesian, gentle, slightly hoarse elderly female voice around 60 years old, speaking Indonesian with a soft Central Javanese accent, calm and tender, softly with a sad smile, after a short pause: "Kopimu dingin lagi, Le." Sound: the quiet ticking of an old wall clock, rain dripping outside. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S11 — Raka pergi, lalu berhenti
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S11.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 3
Audio: SFX saja
```prompt
Raka walks slowly toward the camera with his head down, then suddenly stops mid-step as if he heard something. He stands frozen for a moment, then slowly turns around to face the glowing warung behind him. Camera: static. Environment: water dripping from the roof in the background, reflections on the wet ground. No dialogue, no voice-over. Sound: footsteps on wet ground that stop abruptly, then only dripping water and crickets. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S12 — Raka melangkah ke cahaya
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S12.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 3
Audio: dialog Raka
```prompt
Raka steps forward out of the darkness into the circle of warm light, one slow step and then another; his face becomes lit, eyes wet, and he speaks. Camera: slow dolly back, keeping him slightly left of center. Environment: the bulb swaying slightly, light rippling on the wet ground. Raka says in Indonesian, low, soft-spoken male voice around 30 years old, speaking Indonesian with a light Javanese accent, slow and hesitant pace, with a trembling voice, after two steps: "Bu..." Sound: footsteps on wet ground, rain dripping. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S13 — Ibu terpaku
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S13.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 3
Audio: SFX saja
```prompt
Ibu Sarmi turns her head toward the doorway on the left and freezes; her eyes widen and her lips part. The glass mug in her right hand trembles slightly, clinking softly against its saucer. Camera: static. Environment: still air, only a faint thin wisp of steam from the glass. No dialogue, no voice-over. Sound: faint clinking of glass on the saucer, the wall clock ticking, a held silence. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S14 — Ibu mempersilakan duduk
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S14.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 3
Audio: dialog Ibu
```prompt
Ibu Sarmi slowly sets her glass down on its saucer, then opens her right hand in a gentle gesture toward the empty bench across the table, looking up at someone off-screen on the left with tearful, tender eyes, and speaks. Camera: static. Environment: only a faint thin wisp of steam from the glasses. Ibu Sarmi says in Indonesian, gentle, slightly hoarse elderly female voice around 60 years old, speaking Indonesian with a soft Central Javanese accent, calm and tender, calmly while holding back tears, after a short pause: "Duduk. Kopimu masih anget." Sound: the glass set down on its saucer, the wall clock ticking. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S15 — Raka menangis memegang kopi
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S15.jpg (belum dicek terhadap keyframe) · Durasi: 6 dtk · Take disarankan: 4
Audio: dialog Raka
```prompt
Raka sits with his head bowed over the glass mug held in both hands; he breathes shakily, his shoulders begin to tremble as he cries quietly, and he speaks without lifting his head. Camera: slow push in. Environment: a faint wisp of steam from the glass in the warm light. Raka says in Indonesian, low, soft-spoken male voice around 30 years old, speaking Indonesian with a light Javanese accent, slow and hesitant pace, crying, voice breaking, after a short pause: "Maafin Raka, Bu." Sound: shaky breathing, quiet sobbing. No music. Preserve the character's face, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S16 — Ibu menggenggam tangan Raka
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S16.jpg (belum dicek terhadap keyframe) · Durasi: 5 dtk · Take disarankan: 4
Audio: dialog Ibu
```prompt
Ibu Sarmi's hand reaches across the table and rests gently on top of Raka's hands around the glass, squeezing softly. His head stays bowed. She speaks warmly. Camera: static. Environment: only a faint thin wisp of steam from the glasses, warm bulb light. Ibu Sarmi says in Indonesian, gentle, slightly hoarse elderly female voice around 60 years old, speaking Indonesian with a soft Central Javanese accent, calm and tender, warmly and gently, after a short pause: "Sudah. Yang penting kamu pulang." Sound: a quiet sniffle, the wall clock ticking, rain dripping outside. No music. Preserve both characters' faces, clothing, the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## S17 — Dua gelas kopi berdampingan
Mode Flow: Frames to Video · Frame awal: assets/keyframes/S17.jpg (belum dicek terhadap keyframe) · Durasi: 6 dtk · Take disarankan: 2
Audio: narasi (in-video)
```prompt
The two glass mugs sit still side by side while thick steam rises from both; the two streams of steam curl toward each other and intertwine. Camera: very slow push in. Environment: the warm bulb glowing in soft bokeh. Narrator voice-over in Indonesian, intimate close-mic male voice-over around 30 years old, low and soft-spoken, Indonesian with a light Javanese accent, reflective and slow, speaking gently, after a short pause: "Malam itu, kopinya tidak dingin lagi." Sound: soft rain outside, quiet room tone. No music. Preserve the location, framing and visual style from the start frame. Natural, controlled motion, single continuous shot. No cuts, no subtitles, no on-screen text.
```
Cek take: [ ] wajah & baju konsisten [ ] gerak wajar (tangan) [ ] tidak ada teks/subtitle [ ] audio jelas & tidak terpotong [ ] tanpa musik
Take terpilih: -

## Catatan edit
- **Urutan klip:** S01 → S17 (`assets/clips/Sxx.mp4`), timeline 9:16, 1080×1920.
- **Trim:** potong 0,3–0,5 dtk di awal klip yang geraknya "mulai dari diam". Potong juga ekor klip setelah dialog atau narasi selesai, kecuali S10, S13, dan S17 yang sengaja dibiarkan hening.
- **Transisi:** semua cut langsung, kecuali **S03 → S04 dissolve 1 dtk** (senja ke malam). S17 fade to black 1,5 dtk.
- **Overlay teks:** di S17, judul **DUA GELAS KOPI** (serif tipis, putih hangat, sepertiga atas) fade in di 2 dtk terakhir. Kartu akhir opsional di layar hitam: *Kapan terakhir kamu pulang?* (2–3 dtk).
- **Musik:** gitar akustik atau piano tipis. Masuk pelan di S06, naik di S12, puncak di S16, fade out di S17. S01–S05 hanya ambience. Musik selalu di bawah dialog (sekitar −18 dB sampai −22 dB saat ada suara).
- **Audio:** samakan level suara narator antar klip (S01, S02, S05, S08, S09, S17). Kalau suara narator atau karakter terlalu berbeda antar klip, pilih take yang suaranya paling mirip atau ganti dengan rekaman/TTS.
- **Color:** acuan senja = S02 (biru), acuan malam = S10 (kuning tungsten). Samakan grade S05, S08, S09, S11, dan S12 (luar malam) supaya biru-kuningnya konsisten.
- **Export:** 1080×1920, 9:16, 24 fps (rasa film) atau 30 fps, H.264, bitrate ≥ 12 Mbps. Cek safe area Reels/TikTok (teks tidak di 15% bawah).
