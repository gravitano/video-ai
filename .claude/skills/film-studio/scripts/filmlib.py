"""Parser bersama untuk check_film.py dan film.py. Format lengkap: references/formats.md."""
import re
from pathlib import Path

MODES = {"Frames", "Ingredients", "Text", "Extend"}
REFS_DIR = Path(__file__).resolve().parent.parent / "references"


def read(path):
    path = Path(path)
    return path.read_text(encoding="utf-8") if path.exists() else None


def norm(text):
    return re.sub(r"\s+", " ", text).strip().rstrip(".").strip()


def norm_words(text):
    """Normalisasi longgar untuk membandingkan dialog: huruf kecil, tanpa tanda baca."""
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def header_field(text, name):
    m = re.search(rf"^{name}:\s*(.+?)\s*$", text or "", re.M)
    return m.group(1).strip() if m else None


def parse_bible(text):
    fields = dict(re.findall(
        r"^- (Rasio|Durasi target|Batas klip|Mode narasi|Bahasa dialog|Generator|Model video|Audio native):\s*(.+?)\s*$",
        text, re.M))
    locks = {}
    for key, body in re.findall(r"<!--\s*LOCK:([^>]+?)\s*-->\s*```text\s*\n(.*?)\n\s*```", text, re.S):
        locks[key.strip()] = norm(body)
    return fields, locks


def generator_of(fields):
    return fields.get("Generator", "flow").strip().lower()


def audio_native(fields):
    return not fields.get("Audio native", "ya").strip().lower().startswith(("tidak", "no"))


def generator_profile(name):
    p = REFS_DIR / "generators" / f"{name}.md"
    return p if p.exists() else REFS_DIR / "generators" / "generic.md"


def table_rows(text, first_cell=r"S\d+"):
    """Baris tabel markdown yang sel pertamanya cocok dengan first_cell, sebagai list sel."""
    rows = []
    for line in (text or "").splitlines():
        if re.match(rf"^\|\s*{first_cell}\s*\|", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def parse_shotlist(text, report=lambda *a: None):
    shots = []
    for cells in table_rows(text):
        if len(cells) != 9:
            report("ERROR", cells[0], f"baris shot list punya {len(cells)} kolom, harus 9")
            continue
        sid, scene, dur, cam, action, chars, locs, audio, mode = cells
        try:
            dur = float(dur.replace(",", "."))
        except ValueError:
            report("ERROR", sid, f"durasi bukan angka: {dur!r}")
            dur = 0.0
        split = lambda s: [x.strip() for x in s.split(",") if x.strip() and x.strip() != "-"]
        shots.append({"id": sid, "dur": dur, "chars": split(chars), "locs": split(locs),
                      "audio": audio, "mode": mode, "action": action})
    return shots


def split_sections(text):
    """Map Sxx -> (judul, isi) untuk heading '## Sxx — judul'."""
    sections = {}
    parts = re.split(r"^## (S\d+)\b[ \t]*(?:[—-][ \t]*)?([^\n]*)\n", text or "", flags=re.M)
    for i in range(1, len(parts), 3):
        body = re.split(r"^## ", parts[i + 2], maxsplit=1, flags=re.M)[0]
        sections[parts[i]] = (parts[i + 1].strip(), body)
    return sections


def prompts_in(body):
    return re.findall(r"```prompt\s*\n(.*?)\n\s*```", body, re.S)


def parse_sections(text):
    """Map Sxx -> list of prompt blocks."""
    return {sid: prompts_in(body) for sid, (_, body) in split_sections(text).items()}


def spoken_lines(text):
    """Kalimat yang diucapkan di prompt motion atau baris 'Dialog/Narasi terpisah'."""
    pat = r"(?:\bsays\b|voice-over|terpisah:)[^\"“\n]*?(?:\w+:\s*)?[\"“]([^\"”]+)[\"”]"
    return re.findall(pat, text, re.I)


# ---------- 06-edit.md ----------

def _num(s):
    return float(s.strip().replace(",", "."))


def parse_ranges(cell):
    """'0-1.7, 2.4-7' -> [(0.0, 1.7), (2.4, 7.0)]; kosong/'-' -> None (seluruh klip)."""
    cell = cell.strip()
    if cell in ("", "-"):
        return None
    out = []
    for part in re.split(r",\s+|;\s*", cell):
        a, b = re.split(r"\s*[-–]\s*", part.strip(), maxsplit=1)
        a, b = _num(a), _num(b)
        if b <= a:
            raise ValueError(f"rentang '{part}' tidak valid")
        out.append((a, b))
    return out


def section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", text or "", re.S | re.M)
    return m.group(1) if m else ""


def parse_edit(text):
    """Return (edit, layers, errors). edit: list of dict shot/video/audio/transition."""
    edit, layers, errors = [], [], []
    for cells in table_rows(section(text, "Urutan edit")):
        if len(cells) < 4:
            errors.append((cells[0], "baris urutan edit kurang dari 4 kolom"))
            continue
        sid, vid, aud, trans = cells[:4]
        try:
            video = parse_ranges(vid)
            a = aud.strip().lower()
            audio = a if a in ("klip", "mute", "", "-") else parse_ranges(aud)
            if isinstance(audio, list):
                audio = audio[0]
            elif audio in ("", "-"):
                audio = "klip"
            t = trans.strip().lower()
            if t in ("", "-", "cut"):
                xfade = 0.0
            elif t.startswith("dissolve"):
                xfade = _num(t.split()[1]) if len(t.split()) > 1 else 1.0
            else:
                raise ValueError(f"transisi '{trans}' tidak dikenal (cut / dissolve <dtk>)")
        except (ValueError, IndexError) as e:
            errors.append((sid, str(e)))
            continue
        edit.append({"shot": sid, "video": video, "audio": audio, "xfade": xfade})
    for cells in table_rows(section(text, "Lapisan audio"), first_cell=r"[^|\-\s][^|]*"):
        if cells[0].lower() == "file" or len(cells) < 3:
            continue
        try:
            layers.append({"file": cells[0].strip("` "), "start": _num(cells[1]), "volume": _num(cells[2])})
        except ValueError:
            errors.append((cells[0], "Mulai/Volume lapisan audio bukan angka"))
    return edit, layers, errors


TAKE_COLS = ["Shot", "Take", "Jenis", "File", "Generator", "Model", "Kredit", "Status", "Catatan"]


def parse_takes(text):
    rows = []
    for cells in table_rows(section(text, "Log take"), first_cell=r"(?:S\d+|(?:CHAR|LOC|PROP)-[^|]*)"):
        cells += [""] * (len(TAKE_COLS) - len(cells))
        rows.append(dict(zip(TAKE_COLS, cells)))
    return rows
