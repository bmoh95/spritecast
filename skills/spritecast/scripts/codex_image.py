"""Bridge SpriteCast's image pipeline to Codex's built-in image_gen tool.

Python cannot call Codex's native image tool directly. The SpriteCast scripts
write a request JSON; the Codex agent invokes image_gen and imports its saved
result with this helper.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageOps


def write_request(prompt, images, output, target_size, background=(255, 255, 255, 255)):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    request = output.with_name(output.name + ".codex-request.json")
    refs = [Path(p).resolve() for p in images]
    missing = [str(p) for p in refs if not p.is_file()]
    if missing:
        sys.exit("Codex image request has missing reference images: " + ", ".join(missing))
    payload = {
        "provider": "codex_builtin_image_gen",
        "action": "edit" if refs else "generate",
        "prompt": prompt,
        "input_images": [str(p) for p in refs],
        "output": str(output),
        "target_size": [int(target_size[0]), int(target_size[1])],
        "canvas_rgba": [int(c) for c in background],
    }
    request.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Codex image request: {request}")
    print(f"After image_gen, import its saved image to: {output}")
    return request


def import_result(request_path, source_path, overwrite=False):
    request_path = Path(request_path).resolve()
    source_path = Path(source_path).resolve()
    if not request_path.is_file():
        sys.exit(f"No Codex request file: {request_path}")
    if not source_path.is_file():
        sys.exit(f"No generated image file: {source_path}")
    task = json.loads(request_path.read_text(encoding="utf-8"))
    if task.get("provider") != "codex_builtin_image_gen":
        sys.exit(f"Not a Codex image request: {request_path}")
    output = Path(task["output"]).resolve()
    if output.exists() and not overwrite:
        sys.exit(f"Output already exists (use --overwrite only for an intentional redraw): {output}")
    width, height = map(int, task["target_size"])
    background = tuple(task.get("canvas_rgba", [255, 255, 255, 255]))
    with Image.open(source_path) as opened:
        image = opened.convert("RGBA")
    original_size = image.size
    fitted = ImageOps.contain(image, (width, height), method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (width, height), background)
    canvas.alpha_composite(fitted, ((width - fitted.width) // 2, (height - fitted.height) // 2))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
    if original_size != (width, height):
        print(f"Imported {original_size[0]}x{original_size[1]} into {width}x{height} without stretching.")
    print(f"Imported Codex image: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import", help="fit a generated Codex image into a SpriteCast request's canvas")
    imp.add_argument("request")
    imp.add_argument("generated_image")
    imp.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    import_result(args.request, args.generated_image, args.overwrite)


if __name__ == "__main__":
    main()
