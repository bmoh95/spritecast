---
name: spritecast
description: Build camera-locked isometric game sprites, pixel props, 4/8-direction character animations, and seated character/chair composites for Godot using SpriteCast's 3D guides, Codex native image generation, depth masks, and export scripts.
---

# SpriteCast for Codex CLI

Use this skill when creating isometric or top-down props, furniture, characters, walk/action sprite sheets, pixel art, or a character seated on a chair. This skill is bundled in the SpriteCast Codex Plugin together with its scripts and references. Resolve `scripts/...` and `reference/...` relative to this skill directory. Before shell commands, set `SPRITECAST_SKILL` to the absolute directory containing this `SKILL.md`; do not assume the game project's current directory is the skill directory. Install the plugin through the SpriteCast marketplace documented in the repository README.

## Image generation in Codex

Use Codex's built-in `image_gen` tool for every SpriteCast drawing step. Do not call the OpenAI Images API, `openai images`, or ask for `OPENAI_API_KEY` in Codex mode. The Python scripts cannot call the built-in tool directly: they stage a request file, Codex generates the image, and the import helper returns it to the pipeline.

Before running any SpriteCast step that draws, set the backend for that command:

```bash
export SPRITECAST_SKILL=/absolute/path/to/the/spritecast-skill-directory
export SPRITECAST_IMAGE_BACKEND=codex
python3 "$SPRITECAST_SKILL/scripts/doctor.py" --fix
python3 "$SPRITECAST_SKILL/scripts/isoprop.py" draw path/to/PROP.json
```

On PowerShell:

```powershell
$env:SPRITECAST_SKILL = "C:\path\to\the\spritecast-skill-directory"
$env:SPRITECAST_IMAGE_BACKEND = "codex"
python "$env:SPRITECAST_SKILL/scripts/doctor.py" --fix
python "$env:SPRITECAST_SKILL/scripts/isoprop.py" draw path/to/PROP.json
```

When a command stages a `*.codex-request.json`:

1. Read the JSON. Use its `prompt` verbatim, pass every `input_images` path to the built-in `image_gen` tool as reference images, and preserve their listed roles/order from the prompt. `target_size` is the requested canvas size. Keep the flat white or magenta background requested in the prompt; SpriteCast removes it in its own finishing step. Do not request transparency for color-keyed renders.
2. Use the generated image file path returned by Codex's image tool and import it:

   ```bash
   python3 "$SPRITECAST_SKILL/scripts/codex_image.py" import /absolute/path/to/output.png.codex-request.json /absolute/path/to/generated-image.png
   ```

3. Rerun the same SpriteCast command with `SPRITECAST_IMAGE_BACKEND=codex` so its existing finishing and packing steps run. For batch commands, process each staged request and import each result before rerunning.

A native image-generation request uses Codex's image tool, not per-call Images API billing. Do not quote the API prices printed in the legacy Claude/API documentation as Codex charges. Tripo and Meshy model/rig operations remain separate services and still require their own API keys and explicit user approval before a chargeable request.

## Standard workflow

1. Run `python3 scripts/doctor.py --fix` for Python dependencies and local browser setup. In Codex set `SPRITECAST_IMAGE_BACKEND=codex` when checking drawing readiness. `TRIPO_API_KEY` is only needed for Tripo character modeling/rigging; Meshy is optional when its modeler is selected. A supplied rigged GLB can avoid a model-generation call.
2. For props, read `reference/spec.md` and `reference/tips.md`, create a JSON spec, then run `isoprop.py render`, inspect `render.png` and `render-shadow.png`, and adjust the guide before drawing. Draw through the image-generation relay above, then run `finish` and `preview`.
3. For a walking character, read `reference/character.md`. Use `charpipe.py` for turnaround, model/rig, render, draw, finish and preview. Confirm Tripo/Meshy costs before those external model calls; use native `image_gen` for turnaround and drawing sheets. Check every facing and animation preview before handing it over.
4. For pixel sprites, read `reference/pixel.md`. Use `pixelart.py` for a character or `proppixel.py` for a prop. These commands also stage one request per sheet in Codex mode; generate and import each staged image, then rerun the command.
5. Keep all generated assets in the user's project directory. Do not overwrite a prior drawing unless the user requests a redraw; `codex_image.py import` refuses to overwrite by default.

## Seated character and chair occlusion

For sitting, read `reference/sitting.md`. First create the seated pose with `charpipe.py sit`; draw it with `charpipe.py sit ... --draw` through the Codex image workflow. Then place it on a finished chair/bench with `scripts/seat.py PROP.json CHAR.json --height <meters> --facing <direction>`. Inspect its `preview.png` and `front.png`.

`front.png` is a depth-derived transparent mask containing only chair pixels that should cover the sitter. The full chair sprite remains underneath the character. This is what allows the rear armrest/backrest to stay behind the head while the front armrest/seat edge crosses in front of the torso or legs.

For Godot, create a layered scene from the computed seat metadata:

```bash
python3 "$SPRITECAST_SKILL/scripts/seat_export.py" /absolute/path/to/seat.json --out /absolute/path/to/game/assets/seats --project-root /absolute/path/to/game --name office_chair_se
```

The resulting `.tscn` draws shadow at z=-1, the complete chair at z=0, the seated character at z=1, and the masked chair foreground at z=2. Instance the scene at the chair's footprint anchor so the room's Y-sorting orders the composite as one object. Never put the entire chair above the character; that hides the sitter instead of making the armrest cross the body correctly.

If the armrest is still behind the character, inspect the seat preview and `front_px` in `seat.json`. Re-run `seat.py` after adjusting the depth comparison/mask, and re-export the scene. Do not try to repair the overlap by moving the whole chair layer or changing only its z-index.

## General rules

- Show the 3D render/guide before requesting image generation. User's request to create an asset authorizes its Codex image generation; do not ask again for the image step. Ask before chargeable Tripo/Meshy operations unless the user already authorized them.
- Keep camera angle, footprint, frame layout, scale and anchor tied to the 3D guide. Use only the requested reference's style when the prompt distinguishes style from content.
- If a prompt, guide or image result has a layout/pose error, fix the source guide or prompt first. Do not blindly upscale, stretch or flip asymmetrical designs.
- Preserve the original backend behavior for Claude Code: its skill under `skills/spritecast/` can still use the explicit API backend. Codex should set `SPRITECAST_IMAGE_BACKEND=codex`.
