"""Generate 04-keyframes.md for dua-gelas-kopi, pulling LOCK text verbatim from the bible."""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
bible = (root / "01-bible.md").read_text()
L = {k.strip(): re.sub(r"\s+", " ", v).strip()
     for k, v in re.findall(r"<!--\s*LOCK:([^>]+?)\s*-->\s*```text\s*\n(.*?)\n\s*```", bible, re.S)}

STYLE, RAKA, IBU = L["STYLE"], L["CHAR:Raka"], L["CHAR:Ibu"]
JALAN, WARUNG, DALAM, KOPI = L["LOC:Jalan"], L["LOC:Warung"], L["LOC:Warung-Dalam"], L["PROP:Kopi"]
END_IMG = "Aspect ratio 9:16. No text, no captions, no logos, no watermark."
SAME = "Same face, hair and clothing as the reference image."


def cap(s):
    return s[0].upper() + s[1:]


ingredients = [
    ("CHAR-Raka", "16:9, landscape, supaya muat beberapa pose",
     f"Character reference sheet of {RAKA} He carries a worn brown canvas backpack on his left shoulder. Full body front view and three-quarter view side by side, plus a head-and-shoulders close-up, neutral expression, standing on a plain light grey seamless background, even soft studio lighting. {STYLE} Aspect ratio 16:9. No text, no labels, no watermark."),
    ("CHAR-Ibu", "16:9, landscape",
     f"Character reference sheet of {IBU} Full body front view and three-quarter view side by side, plus a head-and-shoulders close-up, neutral gentle expression, standing on a plain light grey seamless background, even soft studio lighting. {STYLE} Aspect ratio 16:9. No text, no labels, no watermark."),
    ("LOC-Jalan", "16:9 (referensi, boleh landscape)",
     f"Empty establishing view of {JALAN} No people. {STYLE} No text, no signage lettering, no watermark."),
    ("LOC-Warung", "16:9 (referensi, boleh landscape)",
     f"Empty establishing view of {WARUNG} Seen from across the road, no people. {STYLE} No text, no signage lettering, no watermark."),
    ("LOC-Warung-Dalam", "16:9 (referensi, boleh landscape)",
     f"Empty establishing view of {DALAM} No people. The jars have no labels; no packaging, no hanging sachets, no signs. Any window shows only night darkness. {STYLE} No text, no signage lettering, no watermark."),
    ("PROP-Kopi", "1:1 atau 9:16",
     f"Product-style close-up of {KOPI}, side by side on a worn wooden table, warm yellow tungsten light, dark background. {STYLE} No text, no logos, no watermark."),
]

# (id, title, references, prompt body)
shots = [
    ("S01", "Raka sendirian di jalan senja", "CHAR-Raka, LOC-Jalan",
     f"{STYLE} Extreme wide shot, 35mm, high angle from slightly above. {RAKA} A worn brown canvas backpack hangs on his left shoulder. He stands small and alone at the left edge of the road in the lower third of the frame, seen in profile facing right, looking down the road. Setting: {JALAN} The red taillights of a small blue public minibus angkot glow far away on the road to the right. Last pale light on the horizon, wet road reflecting the sky. Road leading from lower left to upper right, lots of sky and negative space above him. {SAME} {END_IMG}"),
    ("S02", "Raka membetulkan ransel", "CHAR-Raka, LOC-Jalan",
     f"{STYLE} Medium shot framed from the waist up, 50mm, eye level, closer than the previous wide shot: his head and shoulders fill the upper half of the frame and his legs are out of frame. {RAKA} A worn brown canvas backpack hangs on his left shoulder. He stands on the left third of the frame, three-quarter profile facing right, looking along the empty road ahead with a heavy, hesitant expression, his right hand gripping the backpack strap on his shoulder, damp hair after the rain. Setting: {JALAN} Soft blue dusk light, faint rim light from the sky behind him. Open space on the right side of the frame in the direction he will walk. {SAME} {END_IMG}"),
    ("S03", "Sepatu melewati genangan", "CHAR-Raka (acuan celana & sepatu), LOC-Jalan",
     f"{STYLE} Extreme close-up at ground level, low angle, 35mm. Only a man's lower legs are visible: dark grey jeans and worn white canvas sneakers, no face or upper body in frame, his left foot planted and his right foot lifted mid-stride just before stepping into a puddle, walking from left to right. Setting: {JALAN} The still puddle in the lower third mirrors the deep blue dusk sky and a coconut tree silhouette. Shallow focus on the sneakers. {END_IMG}"),
    ("S05", "Raka menatap warung dari gelap", "CHAR-Raka, LOC-Warung",
     f"{STYLE} Medium close-up, 50mm, eye level. {RAKA} A worn brown canvas backpack hangs on his left shoulder. He stands in the dark on the left third of the frame, three-quarter profile facing right, his face half-lit by a distant warm yellow light and half in cool blue shadow, eyes fixed on something far away, lips closed, damp hair. Far behind on the right and deeply out of focus: {WARUNG} It appears only as a soft warm glow and bokeh. Night after rain. Empty dark space on the right in his eyeline. {SAME} {END_IMG}"),
    ("S06", "Ibu menuang air ke dua gelas", "CHAR-Ibu, LOC-Warung-Dalam, PROP-Kopi-crop",
     f"{STYLE} Medium shot, 50mm, eye level, side profile. {IBU} She stands at the table in side profile facing left, on the right half of the frame, holding a dented aluminium kettle with both hands, tilted just above the first of two glasses, calm and focused expression. On the table in the lower left: two identical empty clear glass mugs on small glass saucers, each with a spoonful of dry ground black coffee at the bottom, no liquid and no steam yet. Setting: {DALAM} The kettle is now in her hands, so the small kerosene stove behind her shows only a low blue flame. The bulb hangs above at the upper right, casting warm light and deep shadows. {SAME} {END_IMG}"),
    ("S07", "Gelas di depan bangku kosong", "CHAR-Ibu, LOC-Warung-Dalam, PROP-Kopi-crop",
     f"{STYLE} Close-up, 85mm, slightly high angle over the table. {IBU} She stands at the right side of the table, leaning slightly forward; her weathered hands, entering from the right, hold a single clear glass mug of black kopi tubruk on a small glass saucer, lowering it just above the table surface in front of an empty wooden bench on the left side of the frame; her face is softly visible and out of focus in the upper right. Setting: {DALAM} Warm yellow bulb light, dark background. {SAME} {END_IMG}"),
    ("S08", "Mata Raka berkaca-kaca", "CHAR-Raka, LOC-Warung",
     f"{STYLE} Close-up, 85mm, eye level. {RAKA} The strap of his backpack is on his left shoulder. Tight on his face in three-quarter profile facing right, standing in darkness, eyes glistening with held-back tears, a tiny warm yellow reflection of a distant light in his eyes, jaw tight, damp hair. Setting: {WARUNG} The warung is in front of him, out of frame on the right; only its warm light touches his face, while cool blue darkness and faint mist fill the background behind him. {SAME} {END_IMG}"),
    ("S09", "Raka menunduk sebelum berbalik", "CHAR-Raka, LOC-Warung",
     f"{STYLE} Medium shot framed from the waist up, 50mm, eye level: his head and shoulders fill the upper half of the frame and his legs are out of frame. {RAKA} A worn brown canvas backpack hangs on his left shoulder. He stands on the left third of the frame, still facing right toward the distant warung light, head bowed, eyes closed, shoulders lifted mid-breath as if about to sigh. Setting: {WARUNG} It glows warm and out of focus in the far background on the right; he stands on the dark wet road in cool blue night shadow. {SAME} {END_IMG}"),
    ("S10", "Ibu menatap bangku kosong", "CHAR-Ibu, LOC-Warung-Dalam, PROP-Kopi-crop",
     f"{STYLE} Medium shot, 50mm, eye level. {IBU} She sits alone on the bench on the right side of the table, facing left, both hands around her own glass mug, gazing at a second full glass mug set in front of the empty bench on the left, a faint sad smile. On the table: {KOPI}, but the steam is only a thin fading wisp. Setting: {DALAM} The empty bench on the left third of the frame is lit, emphasizing absence. {SAME} {END_IMG}"),
    ("S11", "Raka pergi, lalu berhenti", "CHAR-Raka, LOC-Warung",
     f"{STYLE} Wide shot, 35mm, eye level, camera facing toward the warung. {RAKA} A worn brown canvas backpack hangs on his left shoulder. He is in the dark midground on the left, walking toward the camera and away from the warung, mid-step, head lowered, face mostly in shadow, rim-lit from behind by warm light. Setting: {WARUNG} It sits small and glowing in the background on the right, about thirty meters behind him. Wet ground reflecting the bulb. {SAME} {END_IMG}"),
    ("S12", "Raka melangkah ke cahaya", "CHAR-Raka, LOC-Warung",
     f"{STYLE} Medium shot, 50mm, eye level, camera placed at the front of the warung looking out into the night. {RAKA} A worn brown canvas backpack hangs on his left shoulder. He stands at the edge of the darkness, slightly left of center, facing the camera with his eyeline just off-camera to the right, one foot about to step forward into the circle of warm light on the wet ground, face just lifting, eyes wet, lips about to speak. Setting: {WARUNG} The bulb light falls on the ground in front of him and the edge of the long wooden bench is visible in the foreground on the right. {SAME} {END_IMG}"),
    ("S13", "Ibu terpaku", "CHAR-Ibu, LOC-Warung-Dalam, PROP-Kopi-crop",
     f"{STYLE} Medium close-up, 50mm, eye level. {IBU} She sits at the table facing left, her head just beginning to turn toward the open doorway on the left, holding a clear glass mug of black kopi tubruk in her right hand just above its small glass saucer, eyes widening, frozen in disbelief. Setting: {DALAM} Warm bulb light on her face, darkness beyond the doorway on the left. {SAME} {END_IMG}"),
    ("S14", "Ibu mempersilakan duduk", "CHAR-Ibu, LOC-Warung-Dalam, PROP-Kopi-crop",
     f"{STYLE} Medium shot, 50mm, eye level. {IBU} She sits on the right side of the table facing left, her own glass mug still held in her right hand just above its small glass saucer, about to set it down, her left hand resting on the table, looking up to the left at someone standing off-screen with a tender, tearful gaze. A second clear glass mug of black kopi tubruk with only a faint wisp of steam stands in front of the empty bench. Setting: {DALAM} {SAME} {END_IMG}"),
    ("S15", "Raka menangis memegang kopi", "CHAR-Raka, LOC-Warung-Dalam, PROP-Kopi-crop",
     f"{STYLE} Medium close-up, 50mm, slightly high angle. {RAKA} He is now seated on the bench on the left side of the table facing right, no backpack on his shoulders; his worn brown canvas backpack lies on the floor beside the bench. Both hands wrapped around a clear glass mug of black kopi tubruk with a faint wisp of steam, head bowed low over it, face partially hidden, shoulders tense. Setting: {DALAM} Warm bulb light from above, deep shadows. {SAME} {END_IMG}"),
    ("S16", "Ibu menggenggam tangan Raka", "CHAR-Raka, CHAR-Ibu, LOC-Warung-Dalam, PROP-Kopi-crop",
     f"{STYLE} Medium two-shot, 50mm, eye level, side view across the table. {RAKA} He sits on the left side of the table facing right, no backpack on his shoulders; his worn brown canvas backpack lies on the floor beside the bench. Head bowed, both hands around his glass mug. {IBU} She sits on the right side facing left, leaning slightly forward, her right hand reaching across the table and just about to rest on Raka's hands, looking at him with gentle tearful eyes. One clear glass mug of black kopi tubruk on a small glass saucer stands in front of each of them, with only a faint wisp of steam. Setting: {DALAM} {SAME} {END_IMG}"),
    ("S17", "Dua gelas kopi berdampingan", "PROP-Kopi-crop, LOC-Warung-Dalam",
     f"{STYLE} Extreme close-up, 85mm, table level. Two identical clear glass mugs of black Javanese kopi tubruk on small glass saucers, on opposite sides of the worn wooden table, seen from the side at table level so they appear side by side in the center of the frame, thick fresh steam rising and curling together, the warm yellow bulb blurred into soft bokeh above. Background: {DALAM} Deeply out of focus. No people, no hands. Space in the upper third for a title to be added later. {END_IMG}"),
]

out = [
    "# Keyframes — Dua Gelas Kopi",
    "Status: draft",
    "",
    "## Cara pakai di Google Flow",
    "1. **Generate semua ingredients dulu** (6 gambar di bawah). Buat 2–4 variasi dan pilih yang terbaik. Simpan ke `assets/ingredients/` dengan nama file yang tertera. Character sheet adalah acuan wajah untuk seluruh film, jadi pilih dengan teliti.",
    "2. **Keyframe per shot**: upload ingredient yang tertulis di baris `Referensi`, tempel prompt, lalu generate 2–4 variasi. Pastikan rasio **9:16**.",
    "3. Simpan yang terpilih sebagai `assets/keyframes/Sxx.jpg` (S01, S02, …). S04 tidak butuh keyframe (mode Text).",
    "4. Setelah semua tersimpan, minta Claude untuk **\"cek keyframe\"**. Claude akan membandingkan setiap gambar dengan character sheet.",
    "",
    "Tips: kalau wajah meleset, tambahkan `Same face as the reference image, identical person.` di awal prompt. Kalau muncul tulisan di papan warung, regenerate. Jangan dipakai.",
    "",
    "## Ingredients",
    "",
]
for name, ratio, prompt in ingredients:
    out += [f"### {name}", f"File: assets/ingredients/{name}.jpg · Rasio: {ratio}", "```prompt", prompt, "```", ""]

out += ["## Keyframes", ""]
titles = {s[0]: s for s in shots}
for n in range(1, 18):
    sid = f"S{n:02d}"
    if sid == "S04":
        out += ["## S04 — Warung di kejauhan", "Tidak perlu keyframe (mode Text). Prompt lengkap ada di 05-motion.md.", ""]
        continue
    _, title, refs, prompt = titles[sid]
    out += [f"## {sid} — {title}", f"File: assets/keyframes/{sid}.jpg · Referensi: {refs}", "```prompt", prompt, "```", ""]

(root / "04-keyframes.md").write_text("\n".join(out))
print("ok", len(shots), "keyframes")
