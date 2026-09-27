import base64
import io
import json
import textwrap
from pathlib import Path

import pytest

from scene import spec as spec_mod
from scene.providers.minimax_video import MiniMaxVideo
from scene.stages import clips, keyframes
from scene.state import Ledger, State
from scene.timing import plan, resolve_at
from scene.util import SceneError

# 1x1 PNG
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def make_project(tmp_path: Path, budget=1.0, video=None) -> Path:
    video = video or {"name": "minimax", "model": "MiniMax-H3", "resolution": "768P"}
    (tmp_path / "scene.yaml").write_text(textwrap.dedent(f"""
        project: t
        brief: {{duration: 11}}
        providers: {{image: {{name: manual}}, video: {json.dumps(video)}}}
        budget: {{video_usd: {budget}}}
        shots:
          - {{id: a, duration: 5, keyframe_prompt: kf a, motion_prompt: move a}}
          - {{id: b, duration: 6, keyframe_prompt: kf b, motion_prompt: move b}}
    """))
    src = tmp_path / "incoming"
    src.mkdir()
    for n in ("a", "b"):
        (src / f"{n}.png").write_bytes(PNG)
    s = spec_mod.load(tmp_path)
    keyframes.adopt(s, State(tmp_path), src)
    return tmp_path


# ------------------------------------------------------------------ timing
def test_resolve_at_forms():
    p = {"id": "x", "dur": 5, "vo_end": 3.2,
         "words": [{"text": "langkah", "s": 1.0, "e": 1.3}, {"text": "demi", "s": 1.3, "e": 1.5}, {"text": "langkah,", "s": 1.6, "e": 2.0}]}
    assert resolve_at(None, p, 0.4) == 0.4
    assert resolve_at(1.5, p) == 1.5
    assert resolve_at("2.25", p) == 2.25
    assert resolve_at("w:langkah", p) == 1.0
    assert resolve_at("w:langkah#2", p) == 1.6
    assert resolve_at("w:demi+0.2", p) == 1.5
    assert resolve_at("end-0.3", p) == 4.7
    assert resolve_at("vo_end+0.1", p) == pytest.approx(3.3)
    with pytest.raises(SceneError):
        resolve_at("w:nothere", p)


def test_plan_rounds_up_from_measured_voice(tmp_path):
    (tmp_path / "scene.yaml").write_text("shots:\n  - {id: a, vo: satu dua tiga, keyframe_prompt: k, motion_prompt: m}\n")
    s = spec_mod.load(tmp_path)
    st = State(tmp_path)
    st.put("voice", "a", {"key": "k", "speech": 2.31, "words": [{"text": "satu", "s": 0.05, "e": 0.4}]})
    p = plan(s, st)[0]
    assert p["dur"] == 4  # ceil(0.3 offset + 2.31 speech + 0.5 tail)
    assert p["words"][0]["s"] == pytest.approx(0.35)


# ------------------------------------------------------------------ minimax provider
class FakeHTTP:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, req, timeout=None):
        self.requests.append((req.get_method(), req.full_url, json.loads(req.data) if req.data else None, dict(req.headers)))
        body = self.responses.pop(0)
        return io.BytesIO(json.dumps(body).encode())


def test_minimax_submit_and_poll(tmp_path, monkeypatch):
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    img = tmp_path / "k.png"
    img.write_bytes(PNG)
    http = FakeHTTP([{"task_id": "T1"}, {"status": "Processing"}, {"status": "succeeded", "content": {"url": "https://x/v.mp4"}}])
    monkeypatch.setattr("urllib.request.urlopen", http)
    mm = MiniMaxVideo({"model": "MiniMax-H3", "resolution": "768P", "poll_seconds": 0})
    assert mm.submit("move", img, 20) == "T1"
    method, url, body, headers = http.requests[0]
    assert (method, url) == ("POST", "https://api.minimax.io/v2/video_generation")
    assert headers["Authorization"] == "Bearer test-key"
    assert body["model"] == "MiniMax-H3" and body["resolution"] == "768P"
    assert body["duration"] == 15  # clamped to H3 max
    assert body["content"][0] == {"type": "text", "text": "move"}
    assert body["content"][1]["role"] == "first_frame"
    assert body["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert body["extra"] == {"prompt_expansion_mode": "disabled"}
    assert mm.wait("T1") == "https://x/v.mp4"
    assert http.requests[-1][1] == "https://api.minimax.io/v2/query/video_generation/T1"


def test_minimax_pricing():
    assert MiniMaxVideo({"model": "MiniMax-H3", "resolution": "768P"}).estimate(5) == pytest.approx(0.40)
    assert MiniMaxVideo({"model": "MiniMax-H3", "resolution": "2K"}).estimate(6) == pytest.approx(0.78)
    assert MiniMaxVideo({"model": "MiniMax-H3-Max", "resolution": "480P"}).fit_duration(4) == 5
    with pytest.raises(SceneError):
        MiniMaxVideo({"model": "MiniMax-H3", "resolution": "1080P"})


# ------------------------------------------------------------------ clips stage: money safety
class FakeProvider:
    """Counts submissions; can simulate a crash while waiting."""
    submits = 0

    def __init__(self, crash_on_wait=False):
        self.crash_on_wait = crash_on_wait

    def install(self, monkeypatch):
        prov = self

        def submit(self_, prompt, image, seconds, last_frame=None, references=None):
            FakeProvider.submits += 1
            FakeProvider.last_refs = references
            return f"task-{FakeProvider.submits}"

        def wait(self_, task_id, on_tick=None):
            if prov.crash_on_wait:
                raise SceneError(f"minimax: task {task_id} still running after 0s — rerun to resume")
            return "fake://" + task_id

        monkeypatch.setattr(MiniMaxVideo, "submit", submit)
        monkeypatch.setattr(MiniMaxVideo, "wait", wait)
        monkeypatch.setattr(MiniMaxVideo, "download", staticmethod(lambda url, dest: (dest.parent.mkdir(parents=True, exist_ok=True), dest.write_bytes(b"mp4"))))


def ctx(root):
    s = spec_mod.load(root)
    return s, State(root), Ledger(root)


def test_budget_blocks_before_submitting(tmp_path, monkeypatch):
    FakeProvider.submits = 0
    FakeProvider().install(monkeypatch)
    root = make_project(tmp_path, budget=0.5)  # 11s * $0.08 = $0.88 > $0.50
    s, st, lg = ctx(root)
    with pytest.raises(SceneError, match="budget exceeded"):
        clips.run(s, st, lg, yes=True)
    assert FakeProvider.submits == 0


def test_requires_confirmation(tmp_path, monkeypatch):
    FakeProvider.submits = 0
    FakeProvider().install(monkeypatch)
    root = make_project(tmp_path)
    s, st, lg = ctx(root)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))  # not a tty
    with pytest.raises(SceneError, match="--yes"):
        clips.run(s, st, lg)
    assert FakeProvider.submits == 0


def test_resume_never_resubmits(tmp_path, monkeypatch):
    FakeProvider.submits = 0
    FakeProvider(crash_on_wait=True).install(monkeypatch)
    root = make_project(tmp_path)
    s, st, lg = ctx(root)
    clips.run(s, st, lg, yes=True)
    assert FakeProvider.submits == 2
    assert all(t["status"] == "pending" and t["task_id"] for sid in ("a", "b") for t in st.get("clips", sid)["takes"])
    assert lg.spent("video") == pytest.approx(0.88)

    FakeProvider(crash_on_wait=False).install(monkeypatch)  # provider finishes the same tasks
    s, st, lg = ctx(root)
    clips.run(s, st, lg, yes=True)
    assert FakeProvider.submits == 2  # resumed, not resubmitted
    assert clips.selected_clip(s, st, s.shot("a")).name == "take-1.mp4"
    assert lg.spent("video") == pytest.approx(0.88)

    clips.run(s, st, lg, yes=True)  # everything current → no-op
    assert FakeProvider.submits == 2


def test_prompt_edit_invalidates_only_that_shot(tmp_path, monkeypatch):
    FakeProvider.submits = 0
    FakeProvider().install(monkeypatch)
    root = make_project(tmp_path, budget=5.0)  # budget is cumulative across runs
    s, st, lg = ctx(root)
    clips.run(s, st, lg, yes=True)
    assert FakeProvider.submits == 2
    y = (root / "scene.yaml").read_text().replace("motion_prompt: move b", "motion_prompt: move b faster")
    (root / "scene.yaml").write_text(y)
    s, st, lg = ctx(root)
    assert clips.selected_clip(s, st, s.shot("b")) is None  # stale clip never used
    clips.run(s, st, lg, yes=True)
    assert FakeProvider.submits == 3


# ------------------------------------------------------------------ persona
def add_persona(root: Path, sheet_bytes: bytes = PNG) -> None:
    pdir = root / "personas" / "kai"
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "sheet.png").write_bytes(sheet_bytes)
    (pdir / "persona.yaml").write_text(
        "name: Kai\nlook: Original anime coder, dark-teal spiky hair.\nsheet: sheet.png\n"
        "voice: {voice: id-ID-ArdiNeural, pitch: '+12Hz'}\n")
    y = (root / "scene.yaml").read_text()
    if "persona:" not in y:
        (root / "scene.yaml").write_text("persona: personas/kai\n" + y)


def test_persona_loads_and_sets_voice(tmp_path):
    root = make_project(tmp_path)
    add_persona(root)
    s = spec_mod.load(root)
    assert s.persona["name"] == "Kai"
    assert s.persona_images() == [(root / "personas/kai/sheet.png").resolve()]
    assert s.providers["voice"]["pitch"] == "+12Hz"  # persona voice merged into the voice provider
    assert "must match the attached character sheet" in keyframes.shot_prompt(s, s.shot("a"))


def test_persona_refs_sent_and_sheet_change_invalidates(tmp_path, monkeypatch):
    FakeProvider.submits = 0
    FakeProvider().install(monkeypatch)
    root = make_project(tmp_path, budget=10.0)
    add_persona(root)
    s, st, lg = ctx(root)
    # keyframes adopted before the persona existed are stale now → re-adopt against the persona
    assert keyframes.current(s, st, s.shot("a")) is None
    keyframes.adopt(s, st, root / "incoming")
    clips.run(s, st, lg, yes=True)
    assert FakeProvider.submits == 2
    assert FakeProvider.last_refs == s.persona_images()
    # a new character sheet invalidates keyframes and clips
    (root / "personas/kai/sheet.png").write_bytes(PNG + b"v2")
    s, st, lg = ctx(root)
    assert keyframes.current(s, st, s.shot("a")) is None
    assert clips.selected_clip(s, st, s.shot("a")) is None


def test_minimax_body_includes_reference_images(tmp_path):
    img = tmp_path / "k.png"
    img.write_bytes(PNG)
    body = MiniMaxVideo({"model": "MiniMax-H3", "resolution": "768P"}).build_body("m", img, 5, references=[img] * 12)
    roles = [c.get("role") for c in body["content"]]
    assert roles.count("first_frame") == 1 and roles.count("reference_image") == 9


# ------------------------------------------------------------------ elevenlabs
def test_elevenlabs_words_and_trim(tmp_path, monkeypatch):
    from scene.providers import elevenlabs_voice as el
    monkeypatch.setenv("ELEVENLABS_API_KEY", "k")
    text = "Halo, spec dulu!"
    chars = list(text)
    starts = [0.4 + 0.05 * i for i in range(len(chars))]
    ends = [s + 0.05 for s in starts]
    silent_mp3 = tmp_path / "s.mp3"
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", "2", str(silent_mp3)], check=True)
    audio_b64 = base64.b64encode(silent_mp3.read_bytes()).decode()
    http = FakeHTTP([{"audio_base64": audio_b64, "alignment": {"characters": chars, "character_start_times_seconds": starts,
                                                              "character_end_times_seconds": ends}}])
    monkeypatch.setattr("urllib.request.urlopen", http)
    v = el.ElevenLabsVoice({"voice_id": "V1", "language_code": "id", "stability": 0.4})
    info = v.synthesize(text, tmp_path / "out.wav")
    method, url, body, headers = http.requests[0]
    assert url.startswith("https://api.elevenlabs.io/v1/text-to-speech/V1/with-timestamps")
    assert headers["Xi-api-key"] == "k"
    assert body == {"text": text, "model_id": "eleven_multilingual_v2", "language_code": "id", "voice_settings": {"stability": 0.4}}
    assert [w["text"] for w in info["words"]] == ["Halo,", "spec", "dulu!"]
    assert info["words"][0]["s"] == pytest.approx(0.05)  # trimmed to 50ms before the first word
    assert (tmp_path / "out.wav").exists()
