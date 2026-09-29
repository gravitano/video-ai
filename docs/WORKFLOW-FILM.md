# Workflow film AI (Flow, Higgsfield, dan generator lain)

Alur kerja profesional: **isi kreatif ditentukan user** (boleh dibantu AI), **produksi gambar dan video dikerjakan model AI** di platform pilihan, dan **editor manusia** yang memilih take dan memotong film.

```
 NASKAH USER ──► film-import ─┐
                              ├─► SHOT LIST ─► KEYFRAME ─► MOTION ─► PRODUKSI & EDIT
 IDE ──► film-ide ─► film-naskah ┘  film-shotlist  film-keyframe  film-motion  film-edit
                                     03-shotlist    04-keyframes   05-motion    06-edit, out/
 00-brief · 01-bible · 02-naskah                    ▼ generate      ▼ generate
                                                     di platform     di platform
```

| Tahap | Yang dikerjakan Claude | Yang dikerjakan Anda | Gate |
|---|---|---|---|
| 1–2. Naskah | **Punya naskah:** rapikan ke format pipeline tanpa mengubah kata, tulis catatan produksi sebagai usulan. **Hanya ide:** brief, bible, naskah | Putuskan tiap usulan (terima/tolak), setujui karakter, gaya, generator | ✅ approve |
| 3. Shot list | Pecah per klip ≤ batas klip generator: kamera, audio, mode | Cek alur dan durasi | ✅ approve |
| 4. Keyframe | Prompt character sheet, location plate, keyframe per shot; paket upload | Generate di platform, unduh ke `handoff/.../downloads/` | ✅ keyframe dipilih |
| 5. Motion | Prompt image-to-video + dialog/narasi/SFX per shot, checklist take | Cek prompt | ✅ approve |
| 6. Produksi & edit | Paket upload, adopt hasil, review take, susun `06-edit.md`, rough cut | Generate 2–4 take per shot, pilih take, setujui cut | ✅ cut final |
| Finishing | Urutan, trim, dan lapisan audio sudah ada di `06-edit.md` | Grading, teks, musik, export di DaVinci/CapCut | — |

## Cara pakai

Di Claude Code, dari root repo:

- Punya naskah sendiri: *"Ini naskah saya, jadikan film 60 detik 9:16 pakai Higgsfield"* + lampirkan file atau tempel teks.
- Mulai dari ide: *"Bikin short movie 90 detik pakai Google Flow, idenya: …"*
- Lanjut / cek progres: *"lanjutkan film <slug>"*, *"status film <slug>"*
- Hasil generate sudah diunduh: *"ini hasil generate S01–S05, review take-nya"*
- Satu tahap saja: `/film-import`, `/film-ide`, `/film-naskah`, `/film-shotlist`, `/film-keyframe`, `/film-motion`, `/film-edit`
- Review menyeluruh: *"review kontinuitas film <slug>"* (subagent `film-continuity-reviewer`)

Tambahkan *"langsung semua"* untuk menjalankan tahap 1–3 dan 5 tanpa berhenti di setiap gate. Usulan perubahan pada naskah Anda tetap selalu menunggu keputusan Anda.

## Perintah

```bash
S=.claude/skills/film-studio/scripts
python3 $S/check_film.py films/<slug>                          # validasi format, LOCK, durasi, dialog vs naskah
python3 $S/film.py status   films/<slug>                       # progres per shot + total kredit
python3 $S/film.py handoff  films/<slug> --stage keyframes     # paket upload gambar
python3 $S/film.py handoff  films/<slug>                       # paket upload video
python3 $S/film.py adopt    films/<slug> <folder> --credits 20 # hasil unduhan → take
python3 $S/film.py select   films/<slug> S03 2                 # pilih take
python3 $S/film.py frame    films/<slug> S03                   # frame terakhir → frame awal shot berikutnya
python3 $S/film.py roughcut films/<slug> roughcut-v1           # rakit out/roughcut-v1.mp4 dari 06-edit.md
```

## Generator

Field `Generator` di bible menentukan profil platform (`.claude/skills/film-studio/references/generators/`):

| Generator | Profil | Catatan |
|---|---|---|
| Google Flow (Veo) | `flow.md` | Audio native (dialog, narasi, SFX), klip ±8 dtk |
| Higgsfield | `higgsfield.md` | Agregator banyak model; kemampuan (audio, durasi, extend) tergantung model |
| Lainnya (Kling, Runway, dll.) | `generic.md` | Isi batas klip dan audio native sesuai model |

Kalau model tidak membuat audio (`Audio native: tidak`), dialog dibuat saat edit: TTS/rekaman + lip-sync, lalu ditumpuk lewat tabel `Lapisan audio` di `06-edit.md`.

## Kunci konsistensi

1. **Bible LOCK**: deskripsi karakter, lokasi, gaya, dan suara ditulis sekali, lalu disalin kata per kata ke setiap prompt (dicek otomatis).
2. **Character sheet dulu**, lalu setiap keyframe dibuat dengan character sheet sebagai referensi.
3. **Frame awal (mode `Frames`)** sebagai default untuk shot berkarakter.
4. **Satu pembicara per klip, ±2 kata/detik.**
5. **Tanpa teks di gambar dan video**; semua teks ditambahkan di editor.
6. **Satu model video untuk satu film**, supaya gaya gerak dan warna konsisten.
7. Musik ditambahkan saat editing, bukan di dalam klip.

## File

```
.claude/skills/film-studio/     orchestrator + references/ (formats, prompting, generators/) + scripts/ (check_film, film)
.claude/skills/film-import/     tahap 1–2 dari naskah milik user
.claude/skills/film-ide/        tahap 1 dari ide
.claude/skills/film-naskah/     tahap 2
.claude/skills/film-shotlist/   tahap 3
.claude/skills/film-keyframe/   tahap 4
.claude/skills/film-motion/     tahap 5
.claude/skills/film-edit/       tahap 6
.claude/agents/film-continuity-reviewer.md
films/<slug>/                   proyek film
personas/                       karakter siap pakai (Sari, Bito, Kai) — bisa dipakai ulang di bible
```
