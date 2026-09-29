# video-ai

Pipeline produksi video AI pendek berbasis framework **S.C.E.N.E.** (lihat `docs/Framework_SCENE_Produksi_Video_AI.pdf`), dijalankan bersama Claude Code. Prinsipnya: *AI generates the shots, editor creates the video.* Satu shot = satu klip pendek, dan identitas visual dikunci sekali lalu dipakai ulang di setiap prompt.

Baru pertama kali? Mulai dari [`docs/GETTING-STARTED.md`](docs/GETTING-STARTED.md).

Ada dua cara kerja:

| | Film pipeline (Google Flow) | `scene` CLI |
|---|---|---|
| Cocok untuk | Short movie naratif (dialog, narasi, banyak karakter) | Reels/Shorts/TikTok explainer & promo |
| Yang dikerjakan Claude | Brief, bible, naskah, shot list, prompt keyframe & motion | Menulis `scene.yaml`; CLI menjalankan semuanya |
| Generate gambar/video | Manual oleh Anda di Google Flow (Veo) | Otomatis (codex image, MiniMax H3), atau handoff ke Flow |
| Hasil akhir | Paket produksi + rough cut ffmpeg; edit final di CapCut/DaVinci | MP4 siap tayang (dirakit dengan HyperFrames) |
| Lokasi | `.claude/skills/film-*`, `films/<slug>/` | `scene-video-producer/`, `videos/<proyek>/` |

## 1. Film pipeline (Google Flow)

```
 IDE ──► NASKAH ──► SHOT LIST ──► KEYFRAME ──► IMAGE → VIDEO + DIALOG ──► EDIT
 00-brief  02-naskah  03-shotlist   04-keyframes   05-motion
 01-bible
```

Dari Claude Code di folder ini:

- Mulai: *"Bikin short movie 90 detik pakai Google Flow, idenya: …"*
- Lanjut / cek progres: *"lanjutkan film <judul>"*, *"status film <judul>"*
- Satu tahap saja: `/film-ide`, `/film-naskah`, `/film-shotlist`, `/film-keyframe`, `/film-motion`
- Review: *"review kontinuitas film <judul>"* (subagent `film-continuity-reviewer`)

Setiap tahap berhenti di gate untuk persetujuan Anda. Gambar hasil Flow disimpan sebagai `films/<slug>/assets/keyframes/Sxx.jpg|png`, klip sebagai `assets/clips/Sxx.mp4`.

```bash
# validasi format, LOCK verbatim, durasi, dan kepadatan dialog
python3 .claude/skills/film-studio/scripts/check_film.py films/<slug>

# rakit rough cut dari klip yang sudah ada → films/<slug>/out/
cd films/<slug> && python3 .gen/roughcut.py roughcut-v1
```

Panduan lengkap: [`docs/WORKFLOW-GOOGLE-FLOW.md`](docs/WORKFLOW-GOOGLE-FLOW.md). Format file: `.claude/skills/film-studio/references/formats.md`. Tips Flow/Veo: `.claude/skills/film-studio/references/flow-guide.md`.

Proyek saat ini: `films/dua-gelas-kopi/`.

## 2. `scene` CLI

```
scene.yaml ─► voice ─► keyframes ─► clips ─► review ─► build ─► check ─► render
```

```bash
cd scene-video-producer/pipeline && uv sync
alias scene="$PWD/.venv/bin/scene" && cd ../..

scene init videos/promo-x && cd videos/promo-x
scene voice && scene keyframes && scene review
scene estimate && scene clips --yes          # berbayar, dibatasi budget.video_usd
scene build && scene check && scene render   # → out/<project>.mp4
```

Kebutuhan: Python ≥ 3.11 + `uv`, `ffmpeg`, `node`/`npx` (HyperFrames), opsional `codex` untuk keyframe. API key MiniMax di `~/.minimax_key` atau `MINIMAX_API_KEY`. Pakai `providers.video.name: mock` untuk menguji tanpa biaya, atau `scene handoff` untuk generate klip manual di Flow lalu `scene adopt clips DIR`.

Dokumentasi lengkap: [`scene-video-producer/pipeline/README.md`](scene-video-producer/pipeline/README.md).

```bash
cd scene-video-producer/pipeline && uv run --group dev pytest -q
```

## Persona

`personas/` berisi karakter siap pakai (Sari, Bito, Kai): `persona.yaml` (look, suara, gaya bicara) + `sheet.png` + contoh suara. Dipakai di `scene.yaml` (`persona: ../../personas/<nama>`) atau sebagai acuan bible film. Gunakan hanya karakter dan suara original atau yang Anda punya izinnya.

## Struktur

```
.claude/skills/film-*          skill pipeline film + scripts/check_film.py
.claude/agents/                subagent film-continuity-reviewer
docs/                          framework S.C.E.N.E. (PDF) + panduan workflow Google Flow
films/<slug>/                  proyek film Google Flow
videos/<proyek>/               proyek video scene (scene.yaml, assets/, video/, out/)
personas/                      karakter & suara yang bisa dipakai ulang
scene-video-producer/          plugin Claude Code (skill create-video) + CLI scene (pipeline/)
```
