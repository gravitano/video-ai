# Handoff klip — gits-profile → Google Flow (Veo)

Buat klip image-to-video per shot di Google Flow (Veo), lalu kembalikan ke pipeline.

## Pengaturan untuk semua shot

- Buat project baru di Flow; set **aspect ratio Portrait (9:16)** sebelum generate.
- Mode utama: **Frames to Video** — `<shot>.png` sebagai *start frame*, end frame dikosongkan. Ini menjaga komposisi
  tetap sama dengan keyframe (dan dengan posisi overlay di video).
- Jika wajah/kostum berubah: coba **Ingredients to Video** dengan `reference-1.png` + `<shot>.png` sebagai ingredients
  (identitas lebih kuat, tetapi komposisi awal tidak dikunci — cek ulang posisi teks setelah build).
- Model: varian **Fast** untuk draf, **Quality** untuk final; biaya kredit terlihat saat memilih model.
- Durasi: pilih yang **≥ durasi target** (Flow menawarkan 4/6/8 dtk, dan 10 dtk pada model tertentu).
- Prompt `.txt` sudah ditambah instruksi *tanpa dialog* — Veo membuat audio & bisa membuat karakter berbicara;
  audio klip tidak dipakai, VO dari pipeline.
- Unduh MP4 (720p cukup; upscale 1080p jika tersedia).

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
scene adopt clips handoff-flow/downloads
scene review          # review/clips.jpg
scene build && scene check && scene render
```

Shot yang belum punya klip tetap tampil sebagai keyframe + kamera virtual, jadi bisa dikerjakan bertahap.
