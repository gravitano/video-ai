# Arsip

Isi folder ini tidak lagi dikembangkan. Jalur utama repo adalah film pipeline (lihat [`../docs/WORKFLOW-FILM.md`](../docs/WORKFLOW-FILM.md)).

## `scene-video-producer/` — CLI `scene`

Pipeline otomatis untuk video explainer/promo berbasis voice-over (Reels/Shorts/TikTok): satu `scene.yaml` → TTS → keyframe → klip MiniMax H3 → dirakit dengan HyperFrames (overlay teks, caption) → MP4. Tidak mendukung dialog antar-karakter. Dokumentasi: [`scene-video-producer/pipeline/README.md`](scene-video-producer/pipeline/README.md).

Masih bisa dijalankan:

```bash
cd archived/scene-video-producer/pipeline && uv sync
alias scene="$PWD/.venv/bin/scene"
cd ../../videos/sdd-sari && scene status
uv run --group dev pytest -q        # dari folder pipeline/
```

`clips` memanggil API MiniMax berbayar (`--yes`, dibatasi `budget.video_usd`); API key di `~/.minimax_key` atau `MINIMAX_API_KEY`.

## `videos/` — proyek hasil `scene`

`sdd-reels-45s`, `sdd-pipeline-test`, `sdd-sari`, `gits-profile`. Masing-masing punya `scene.yaml` (sumber kebenaran), `assets/`, `video/` (proyek HyperFrames hasil generate, jangan diedit manual), dan `.scene/` (cache + ledger biaya). Persona dirujuk sebagai `persona: ../../../personas/<nama>`.
