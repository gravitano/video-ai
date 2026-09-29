---
name: create-video
description: Plan and produce a short-form AI video or Reels/Shorts/TikTok using the S.C.E.N.E. framework. Use when asked for a video concept, script, storyboard, keyframes, image-to-video prompts, shot-by-shot production, or an editing handoff. Can start from a brief or continue an existing production.
---

# S.C.E.N.E. video producer

Produce a coherent short video through five stages. Match the language of the user's brief. Honor any existing approved brief, script, assets, and decisions; do not restart approved stages.

## 1. Strategy

Capture topic, audience, platform, runtime, objective, single key message, CTA, language, and tone. Infer routine details from context and label assumptions. Ask only for a missing decision that prevents meaningful work. Output a concise creative brief.

## 2. Creative

Write a voice-over script with a hook, problem, escalation, solution, explanation, payoff, and CTA as appropriate. Make its speaking length plausible for the target runtime. Break it into a shot sheet with shot number, start/end times, narrative purpose, visual, VO line, overlay, and sound cue. Sum all shot durations and make them equal the target runtime. Treat the sheet as the source of truth; revise it when the script changes.

## 3. Establish visuals

Define a style bible covering character identity, outfit, setting, palette, light, camera language, aspect ratio, and overlay safe space. Make a character/reference frame first when continuity matters. Create one keyframe per shot using that reference and inspect each for narrative clarity and identity continuity. Use original characters when the user seeks an original concept. Keep exact typography out of generated footage; design overlay text for the editor. If image tools are unavailable, provide image prompts and mark image production pending.

## 4. Narrative motion

For each approved keyframe, write an image-to-video prompt focused on subject action, camera, environmental movement, timing, and invariants. Animate one shot at a time when video tools are available. Inspect takes for continuity, unnatural motion, distorted hands, unwanted writing, and accidental cuts. Select a take or record what must be regenerated. When video tools are unavailable, provide ready-to-paste prompts without claiming video clips were made.

## 5. Edit and export

Place VO first on the timeline, cut visuals to its beats, then add selective typography, SFX, low-level music, and consistent color. State export dimensions, frame rate, codec, and platform safe-area checks. Preview the whole result and report what is complete and what still needs an external editor or generator.

## Output contracts

- If the user asks to **plan**: brief, full VO, shot sheet, style bible, prompts, and editing plan.
- If the user asks for **images**: create or revise the keyframes, show them in numbered shot order, and report consistency issues.
- If the user asks for **video**: use available video creation tools if present, then assemble and verify when editing tools are available; otherwise deliver the approved keyframes and shot-specific motion prompts with a clear status.
- If the user asks to **continue**: inspect the existing stage and advance the next unfinished stage, preserving prior approved artifacts.

## Production pipeline (scene CLI)

When the user wants the video actually produced (not only planned), use the bundled pipeline in `../../pipeline` (see its README):

1. Express the approved plan as `scene.yaml` in the video's folder — start from `pipeline/scene/templates/scene.yaml`; `pipeline/examples/sdd-reels-45s/scene.yaml` is a complete reference. The spec is the source of truth: revise it, never the generated `video/` files.
2. Run the stages with `uv run --project <pipeline> scene …` (or `<pipeline>/.venv/bin/scene` after `uv sync`): `voice` → `keyframes` → `review` → `estimate` → `clips` → `review` → `build` → `check` → `render`.
3. Gates: show `review/keyframes.jpg` before paid video; show `scene estimate` and get the user's explicit OK before `scene clips --yes` (MiniMax H3 is billed per second); inspect `review/clips.jpg` and use `--retake` / `scene select` for weak takes; render only after `scene check` passes.
4. Without a MiniMax key or budget, `scene run --no-clips` produces the keyframe + virtual-camera version, and `providers.video.name: mock` tests the flow for $0. Clips made elsewhere enter with `scene adopt clips DIR`.
5. Report from `scene status`: which shots are real clips vs stills, total spend from the ledger, and the output path.

Read [prompt-templates.md](references/prompt-templates.md) when writing image or motion prompts. Read [handoff.md](references/handoff.md) when assembling the production sheet or editing handoff. Do not add tools, services, or paid steps the user did not request unless necessary to finish the task.
