# Handoff klip — gits-profile → web MiniMax (Hailuo)

Buat klip image-to-video per shot di web MiniMax (Hailuo), lalu kembalikan ke pipeline.

## Pengaturan untuk semua shot

- Mode: **Image to Video**; unggah `<shot>.png` sebagai frame pertama (first frame).
- Referensi karakter (jika ada opsi subject/character reference): `reference-1.png`.
- Rasio: ikut gambar (vertikal 9:16). Resolusi: 768P atau lebih tinggi.
- Durasi: pilih yang **≥ durasi target**; kelebihan dipotong otomatis, kekurangan ditahan di frame terakhir.
- Matikan prompt enhancer / auto-optimize jika ada, agar batasan "no text, preserve identity" tidak diubah.
- Audio klip tidak dipakai (VO, musik, SFX dipasang oleh pipeline).

## Per shot

| # | File gambar | Durasi target | Prompt (salin dari file .txt) | Status |
| --- | --- | --- | --- | --- |
| 1 | `01_hook.png` | 4 dtk | `01_hook.txt` — Animate the supplied keyframe. Subject: Sari tilts her head thoughtful… |  |
| 2 | `02_intro.png` | 7 dtk | `02_intro.txt` — Animate the supplied keyframe. Subject: Sari waves hello and smiles wa… |  |
| 3 | `03_ai.png` | 8 dtk | `03_ai.txt` — Animate the supplied keyframe. Subject: Sari gestures to each floating… |  |
| 4 | `04_services.png` | 5 dtk | `04_services.txt` — Animate the supplied keyframe. Subject: Sari turns the phone toward th… |  |
| 5 | `05_numbers.png` | 6 dtk | `05_numbers.txt` — Animate the supplied keyframe. Subject: Sari points up and grins as th… |  |
| 6 | `06_trust.png` | 8 dtk | `06_trust.txt` — Animate the supplied keyframe. Subject: Sari lifts the tablet as the s… |  |
| 7 | `07_team.png` | 7 dtk | `07_team.txt` — Animate the supplied keyframe. Subject: Sari gestures to the map as th… |  |
| 8 | `08_cta.png` | 8 dtk | `08_cta.txt` — Animate the supplied keyframe. Subject: Sari extends an inviting hand … |  |

## Setelah generate

1. Unduh MP4 terbaik tiap shot ke folder `downloads/`, **beri nama diawali id shot**, mis. `01_hook.mp4`
   (variasi: `01_hook-2.mp4`).
2. Cek: wajah/kostum sama dengan keyframe, tangan wajar, tidak ada teks/logo muncul, tidak ada potongan adegan.
3. Jalankan dari folder proyek:

```bash
scene adopt clips handoff/downloads
scene review          # review/clips.jpg
scene build && scene check && scene render
```

Shot yang belum punya klip tetap tampil sebagai keyframe + kamera virtual, jadi bisa dikerjakan bertahap.
