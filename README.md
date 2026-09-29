# video-ai

Pipeline produksi film dan video AI pendek berbasis framework **S.C.E.N.E.** (lihat `docs/Framework_SCENE_Produksi_Video_AI.pdf`), dijalankan bersama Claude Code. Prinsipnya: *AI generates the shots, editor creates the video.*

Baru pertama kali? Mulai dari [`docs/GETTING-STARTED.md`](docs/GETTING-STARTED.md).

## Film pipeline (jalur utama)

Alur kerja profesional untuk short movie, iklan naratif, atau konten berkarakter:

- **Isi kreatif ditentukan Anda.** Bawa naskah sendiri, atau kembangkan dari ide bersama Claude. Perubahan pada materi Anda selalu diajukan sebagai usulan yang Anda putuskan.
- **Produksi oleh model AI** di platform pilihan: Google Flow (Veo), Higgsfield (Kling, Veo, Sora, Seedance, dll.), atau generator lain. Claude menyiapkan prompt dan paket upload; Anda yang generate.
- **Konsistensi dijaga sistematis:** deskripsi karakter, lokasi, dan gaya dikunci di bible dan disalin kata per kata ke setiap prompt, lalu diperiksa otomatis.
- **Pasca-produksi terstruktur:** log take, pemilihan take, urutan edit, lapisan audio, dan rough cut otomatis dengan ffmpeg.

```
 naskah Anda ─► film-import ─┐
                             ├─► shot list ─► keyframe ─► motion ─► produksi & edit
 ide ─► film-ide ─► film-naskah ┘
```

Dari Claude Code di folder ini:

- *"Ini naskah saya, jadikan film 60 detik 9:16 pakai Higgsfield"* (lampirkan atau tempel naskahnya)
- *"Bikin short movie 90 detik pakai Google Flow, idenya: …"*
- *"lanjutkan film <slug>"*, *"status film <slug>"*, *"ini hasil generate-nya, review take"*

```bash
S=.claude/skills/film-studio/scripts
python3 $S/check_film.py films/<slug>              # validasi
python3 $S/film.py status films/<slug>             # progres + kredit
python3 $S/film.py handoff films/<slug>            # paket upload ke generator
python3 $S/film.py adopt films/<slug> <folder>     # hasil unduhan → take
python3 $S/film.py roughcut films/<slug>           # rakit rough cut dari 06-edit.md
```

Panduan lengkap: [`docs/WORKFLOW-FILM.md`](docs/WORKFLOW-FILM.md). Contoh proyek: `films/dua-gelas-kopi/`.

## `scene` CLI (explainer/Reels otomatis)

Jalur sekunder untuk video explainer atau promo berbasis voice-over (Reels/Shorts/TikTok) yang dirender otomatis dari satu `scene.yaml`: TTS → keyframe → klip MiniMax → rakit dengan HyperFrames (overlay teks, caption) → MP4. Tidak mendukung dialog antar-karakter. Proyek di `videos/<proyek>/`.

```bash
cd scene-video-producer/pipeline && uv sync
alias scene="$PWD/.venv/bin/scene" && cd ../..
scene init videos/promo-x && cd videos/promo-x
scene voice && scene keyframes && scene review && scene estimate
scene clips --yes                             # berbayar, dibatasi budget.video_usd
scene build && scene check && scene render    # → out/<project>.mp4
```

Dokumentasi: [`scene-video-producer/pipeline/README.md`](scene-video-producer/pipeline/README.md). Test: `cd scene-video-producer/pipeline && uv run --group dev pytest -q`.

## Persona

`personas/` berisi karakter siap pakai (Sari, Bito, Kai): `persona.yaml` (look, suara, gaya bicara) + `sheet.png` + contoh suara. Dipakai sebagai acuan bible film, atau di `scene.yaml` (`persona: ../../personas/<nama>`). Gunakan hanya karakter dan suara original atau yang Anda punya izinnya.

## Struktur

```
.claude/skills/film-*          skill pipeline film (import, ide, naskah, shotlist, keyframe, motion, edit, studio)
.claude/skills/film-studio/    references/ (format, prompting, profil generator) + scripts/ (check_film, film)
.claude/agents/                subagent film-continuity-reviewer
docs/                          getting started, workflow film, framework S.C.E.N.E. (PDF)
films/<slug>/                  proyek film
videos/<proyek>/               proyek scene (scene.yaml, assets/, video/, out/)
personas/                      karakter & suara yang bisa dipakai ulang
scene-video-producer/          plugin Claude Code (skill create-video) + CLI scene (pipeline/)
```
