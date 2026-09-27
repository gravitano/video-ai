# Workflow Short Movie AI dengan Google Flow

```
 IDE ──► NASKAH ──► SHOT LIST ──► IMAGE / SCENE ──► IMAGE → VIDEO + DIALOG ──► EDIT
 film-ide  film-naskah  film-shotlist   film-keyframe      film-motion            (CapCut/DaVinci)
   │           │            │               │                   │
 00-brief   02-naskah   03-shotlist    04-keyframes         05-motion
 01-bible                              ▼ generate di Flow   ▼ generate di Flow
                                       assets/keyframes     assets/clips
```

| Tahap | Yang dikerjakan Claude | Yang dikerjakan Anda | Gate |
|---|---|---|---|
| 1. Ide | Brief, logline, sinopsis, **bible** (LOCK style, karakter, suara, lokasi) | Pilih logline, setujui karakter dan gaya | ✅ approve |
| 2. Naskah | Naskah per scene: aksi, dialog, narasi, sesuai anggaran kata | Baca dan revisi | ✅ approve |
| 3. Shot list | Pecah per klip ≤ 8 dtk: kamera, audio, mode Flow | Cek alur dan durasi | ✅ approve |
| 4. Image per scene | Prompt character sheet, location plate, keyframe per shot | Generate di Flow, simpan `assets/keyframes/Sxx.png`, lalu minta "cek keyframe" | ✅ keyframe OK |
| 5. Image → video | Prompt motion + dialog/narasi/SFX per shot, checklist take, catatan edit | Generate di Flow (2–4 take), simpan `assets/clips/Sxx.mp4` | ✅ take terpilih |
| 6. Edit | (catatan edit sudah ada di 05) | Rakit, tambah musik, overlay, grading, lalu export | — |

## Cara pakai

Di Claude Code, dari folder ini:

- Mulai: *"Bikin short movie 90 detik pakai Google Flow, idenya: anak rantau pulang kampung setelah 10 tahun."*
- Lanjut ke tahap berikutnya: *"lanjutkan film pulang"*
- Cek progres: *"status film pulang"*
- Jalankan satu tahap saja: `/film-naskah`, `/film-keyframe`, dan seterusnya
- Review menyeluruh: *"review kontinuitas film pulang"* (subagent `film-continuity-reviewer`)
- Validasi cepat: `python3 .claude/skills/film-studio/scripts/check_film.py films/pulang`

Tambahkan *"langsung semua"* untuk menjalankan tahap 1–3 dan 5 tanpa berhenti di setiap gate.

## Kunci konsistensi

1. **Bible LOCK**: deskripsi karakter, lokasi, gaya, dan suara ditulis sekali, lalu disalin kata per kata ke setiap prompt (dicek otomatis oleh script).
2. **Character sheet dulu**, lalu setiap keyframe dibuat dengan character sheet sebagai referensi.
3. **Frames to Video** sebagai mode default untuk shot berkarakter.
4. **Satu pembicara per klip, ±2 kata/detik.**
5. **Tanpa teks di gambar dan video**; semua teks ditambahkan di editor.
6. Musik ditambahkan saat editing, bukan di dalam klip.

## File

```
.claude/skills/film-studio/     orchestrator + references/ (flow-guide, formats) + scripts/check_film.py
.claude/skills/film-ide/        tahap 1
.claude/skills/film-naskah/     tahap 2
.claude/skills/film-shotlist/   tahap 3
.claude/skills/film-keyframe/   tahap 4
.claude/skills/film-motion/     tahap 5
.claude/agents/film-continuity-reviewer.md
films/<slug>/                   proyek film
personas/                       karakter siap pakai (Sari, Bito, Kai) — bisa dipakai ulang di bible
```
