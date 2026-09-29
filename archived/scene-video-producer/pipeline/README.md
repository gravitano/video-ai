# scene — pipeline video AI S.C.E.N.E.

Dari satu `scene.yaml` menjadi MP4 Reels/Shorts/TikTok siap tayang:

```
scene.yaml ─► voice ─► keyframes ─► clips (MiniMax H3) ─► review ─► build (HyperFrames) ─► check ─► render
   S/C          VO +       E            N                    QC          E — edit & export
             timing kata
```

**Prinsip:** Claude (skill `create-video`) menulis dan merevisi `scene.yaml`; CLI hanya mengeksekusi. Setiap aset di-cache
berdasarkan isinya, jadi mengubah satu baris hanya membuat ulang bagian yang terdampak.

## Setup

```bash
cd pipeline && uv sync                     # Python 3.12 + dependensi
alias scene="$PWD/.venv/bin/scene"         # atau: uv run --project <pipeline> scene
```

Kebutuhan: `ffmpeg`, `node`/`npx` (HyperFrames), `codex` (keyframe via ChatGPT Images, opsional),
skill HyperFrames `media-use` (SFX bawaan) dan `hyperframes-audio` (carve musik) — terpasang lewat `npx hyperframes skills update`.

API key MiniMax (platform.minimax.io, pay-as-you-go) — simpan di file, jangan di chat/kode:

```bash
printf '%s' 'KEY' > ~/.minimax_key && chmod 600 ~/.minimax_key     # atau export MINIMAX_API_KEY=…
```

## Alur kerja

```bash
scene init videos/promo-x          # template scene.yaml (atau minta Claude mengisinya dari brief)
cd videos/promo-x
scene voice                        # TTS + timing kata → durasi shot (dibulatkan ke detik untuk H3)
scene keyframes                    # 00_reference lalu 1 keyframe/shot (paralel, referensi dilampirkan)
scene review                       # review/keyframes.jpg — setujui sebelum bayar video
scene estimate                     # biaya clip sebelum submit
scene clips --yes                  # MiniMax H3 image-to-video, dibatasi budget.video_usd
scene review --vision              # review/clips.jpg (+ QC otomatis opsional)
scene clips --shot 05_solution --retake --yes && scene select 05_solution 2
scene build && scene check && scene render      # → out/<project>.mp4
```

`scene run --yes` menjalankan semuanya berurutan; `scene run --no-clips` membuat versi still + kamera virtual ($0).
`scene status` menampilkan progres per shot dan total pengeluaran.

## Pengaman biaya

- Biaya dihitung **sebelum** submit (`$/detik × durasi`), ditolak bila melebihi `budget.video_usd` (kumulatif, dari ledger).
- Submit berbayar butuh `--yes` (atau konfirmasi interaktif).
- `task_id` disimpan ke `.scene/state.json` sebelum menunggu hasil → bila proses mati, jalankan perintah yang sama untuk
  **melanjutkan**, bukan submit ulang.
- Clip hanya dibuat ulang bila kuncinya berubah: model, resolusi, durasi, motion prompt, atau hash keyframe.
- Semua panggilan tercatat di `.scene/ledger.jsonl`.
- Provider `mock` (`providers.video.name: mock`) menguji seluruh pipeline tanpa biaya.

## Provider

| Jenis | Provider | Catatan |
| --- | --- | --- |
| video | `minimax` (MiniMax-H3 / H3-Max, API v2) · `mock` | H3: 4–15 dtk, 768P $0,08/dtk, 2K $0,13/dtk |
| image | `codex` · `manual` (`scene adopt keyframes DIR`) | referensi `00_reference` dilampirkan ke setiap shot |
| voice | `edge` (edge-tts, timing per kata) | contoh: `id-ID-ArdiNeural`, `rate: "+12%"` |
| music | `synth` (placeholder) · `file` · `none` | ganti dengan lagu berlisensi sebelum publish |

Klip dari luar pipeline (mis. web Hailuo) bisa dipakai: `scene adopt clips DIR` (nama file diawali id shot).

## Spec

Lihat `scene/templates/scene.yaml` (template berkomentar) dan `examples/sdd-reels-45s/scene.yaml` (video 45 detik lengkap).
Waktu overlay/SFX bisa ditulis relatif ke VO: `at: "w:kilat"`, `"w:langkah#2"`, `"w:spec+0.2"`, `"end-0.3"`.

Komponen visual yang tersedia: `headline` (slam/snap/rise/glitch/mono/type), `callouts`, `flow`, `badge`, `cta`,
dan efek `glow`, `alarm`, `flash_in`, `flash_out`, `bloom`, `bars`. Shot tanpa clip otomatis memakai keyframe + kamera virtual,
jadi video selalu bisa dirender dan naik kualitas per shot begitu clip tersedia.

## Persona (karakter & suara konsisten)

Satu persona dipakai ulang di banyak video. Folder persona berisi `persona.yaml` + `sheet.png` (turnaround + ekspresi):

```yaml
# personas/kai/persona.yaml
name: Kai
look: "Original anime-style … (deskripsi kostum & ciri yang tidak boleh berubah)"
sheet: sheet.png                      # dilampirkan ke setiap keyframe & dikirim sebagai reference_image ke MiniMax
refs: []                              # gambar tambahan (maks. 9 total)
voice: {name: edge, voice: id-ID-ArdiNeural, rate: "+15%", pitch: "+12Hz"}   # af: filter ffmpeg opsional
speaking_style: "…"                   # dipakai Claude saat menulis VO
catchphrases: ["…"]
```

Di `scene.yaml`: `persona: ../personas/kai`. Efeknya: prompt keyframe ditambah deskripsi karakter, sheet ikut dilampirkan,
klip MiniMax menerima sheet sebagai `reference_image` (matikan dengan `providers.video.persona_refs: false`), suara diambil
dari persona, dan QC `--vision` menilai identitas terhadap sheet. Mengganti sheet otomatis membuat ulang keyframe & klip terkait.

Gunakan karakter dan suara **original** (atau yang Anda punya lisensinya / izin pemilik suaranya) — bukan karakter franchise.

## Struktur proyek video

```
promo-x/
  scene.yaml            sumber kebenaran
  assets/               keyframes/ voice/ clips/<shot>/take-N.mp4 music/
  review/               keyframes.jpg clips.jpg qc.json
  video/                proyek HyperFrames hasil generate (jangan diedit manual — edit scene.yaml)
  out/<project>.mp4
  .scene/               state.json ledger.jsonl timeline.json
```

## Test

```bash
uv run --group dev pytest -q
```
