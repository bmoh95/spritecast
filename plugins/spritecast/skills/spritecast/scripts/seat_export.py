"""Export a SpriteCast chair + seated character as a layered Godot 4 scene.

    python seat_export.py PATH/TO/seat.json --out godot-assets [--name desk_seat]

The chair is drawn first, the sitter next, and the depth-masked chair front last.
The scene root sits at the chair's footprint anchor for Y-sorting with the room.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path


def export(seat_path, out_dir, name=None, project_root=None):
    seat_path = Path(seat_path).resolve()
    if not seat_path.is_file():
        sys.exit(f"seat.json not found: {seat_path}")
    seat = json.loads(seat_path.read_text(encoding="utf-8"))
    made_by = seat.get("made_by") or {}
    prop_spec_path = Path(made_by.get("prop", "")).resolve()
    char_spec_path = Path(made_by.get("char", "")).resolve()
    if not prop_spec_path.is_file() or not char_spec_path.is_file():
        sys.exit("seat.json does not point to readable prop and character specs")

    prop_spec = json.loads(prop_spec_path.read_text(encoding="utf-8"))
    char_spec = json.loads(char_spec_path.read_text(encoding="utf-8"))
    prop_dir = prop_spec_path.parent / prop_spec["name"]
    if made_by.get("view"):
        prop_dir /= made_by["view"]
    chair_sprite = prop_dir / "sprite.png"
    chair_meta_path = prop_dir / "sprite.json"
    front_sprite = seat_path.parent / seat.get("front", "front.png")
    sitter_sprite = char_spec_path.parent / seat["frame"]
    shadow_sprite = prop_dir / "shadow.png"
    for p in (chair_sprite, chair_meta_path, front_sprite, sitter_sprite):
        if not p.is_file():
            sys.exit(f"required seating asset is missing: {p}")
    chair_meta = json.loads(chair_meta_path.read_text(encoding="utf-8"))
    anchor = chair_meta.get("anchor_px")
    if not anchor or len(anchor) != 2:
        sys.exit(f"{chair_meta_path} has no two-dimensional anchor_px")

    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if project_root:
        project_root = Path(project_root).resolve()
    else:
        project_root = next((p for p in (out_dir, *out_dir.parents) if (p / "project.godot").is_file()), None)
    if project_root is None:
        sys.exit("Godot project.godot not found above --out; pass --project-root <Godot project directory>")
    try:
        out_rel = out_dir.relative_to(project_root).as_posix()
    except ValueError:
        sys.exit(f"--out must be inside the Godot project: {out_dir} is outside {project_root}")
    name = name or f"{prop_spec['name']}_{seat.get('facing', 'seated')}_seat"
    name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
    files = {
        "chair": out_dir / f"{name}_chair.png",
        "sitter": out_dir / f"{name}_sitter.png",
        "front": out_dir / f"{name}_front.png",
    }
    shutil.copyfile(chair_sprite, files["chair"])
    shutil.copyfile(sitter_sprite, files["sitter"])
    shutil.copyfile(front_sprite, files["front"])
    has_shadow = shadow_sprite.is_file()
    if has_shadow:
        files["shadow"] = out_dir / f"{name}_shadow.png"
        shutil.copyfile(shadow_sprite, files["shadow"])

    ext = []
    def texture_resource(key, path):
        rid = str(len(ext) + 1)
        ext.append((rid, f"res://{out_rel}/{path.name}" if out_rel != "." else f"res://{path.name}"))
        return rid

    chair_id = texture_resource("chair", files["chair"])
    sitter_id = texture_resource("sitter", files["sitter"])
    front_id = texture_resource("front", files["front"])
    shadow_id = texture_resource("shadow", files["shadow"]) if has_shadow else None
    resources = "\n".join(
        f'[ext_resource type="Texture2D" path="{file_name}" id="{rid}"]'
        for rid, file_name in ext
    )
    ax, ay = map(float, anchor)
    chair_pos = f"Vector2({-ax:.3f}, {-ay:.3f})"
    sitter_tl = seat["top_left_in_sprite"]
    sitter_pos = f"Vector2({float(sitter_tl[0]) - ax:.3f}, {float(sitter_tl[1]) - ay:.3f})"
    sitter_scale = float(seat["scale"])
    children = []
    if shadow_id:
        shadow_offset = chair_meta.get("shadow", {}).get("offset_px", [0, 0])
        sx, sy = float(shadow_offset[0]) - ax, float(shadow_offset[1]) - ay
        children.append(f'''[node name="Shadow" type="Sprite2D" parent="."]
modulate = Color(1, 1, 1, 0.3)
position = Vector2({sx:.3f}, {sy:.3f})
texture = ExtResource("{shadow_id}")
centered = false
z_index = -1''')
    children.append(f'''[node name="Chair" type="Sprite2D" parent="."]
position = {chair_pos}
texture = ExtResource("{chair_id}")
centered = false
z_index = 0''')
    children.append(f'''[node name="SeatedCharacter" type="Sprite2D" parent="."]
position = {sitter_pos}
scale = Vector2({sitter_scale:.6f}, {sitter_scale:.6f})
texture = ExtResource("{sitter_id}")
centered = false
z_index = 1''')
    children.append(f'''[node name="ChairFront" type="Sprite2D" parent="."]
position = {chair_pos}
texture = ExtResource("{front_id}")
centered = false
z_index = 2''')
    scene = (f"[gd_scene load_steps={len(ext) + 1} format=3]\n\n{resources}\n\n"
             f'[node name="{name}" type="Node2D"]\n\n' + "\n\n".join(children) + "\n")
    scene_path = out_dir / f"{name}.tscn"
    scene_path.write_text(scene, encoding="utf-8")
    report = {
        "scene": scene_path.name,
        "facing": seat.get("facing"),
        "anchor_px": anchor,
        "draw_order": ["Shadow", "Chair", "SeatedCharacter", "ChairFront"],
        "front_mask": str(front_sprite),
        "front_mask_pixels": seat.get("front_px"),
        "note": "Instance this scene at the chair footprint anchor; ChairFront is the only chair piece drawn over the sitter.",
    }
    (out_dir / f"{name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Godot seated composite: {scene_path}")
    print("Draw order: chair base -> seated character -> depth-masked front armrest/seat edge")
    return scene_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seat_json")
    parser.add_argument("--out", required=True, help="output asset directory inside the Godot project")
    parser.add_argument("--project-root", help="Godot project root (auto-detected from project.godot when omitted)")
    parser.add_argument("--name", help="scene and asset basename")
    args = parser.parse_args()
    export(args.seat_json, args.out, args.name, args.project_root)


if __name__ == "__main__":
    main()
