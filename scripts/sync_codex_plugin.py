#!/usr/bin/env python3
"""Sync SpriteCast resources into the plugin's bundled Codex skill, preserving its Codex-specific SKILL.md."""
import shutil
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "skills" / "spritecast"
DEST = REPO / "plugins" / "spritecast" / "skills" / "spritecast"


def main():
    skill_md = DEST / "SKILL.md"
    if not skill_md.is_file():
        raise SystemExit(f"Codex SKILL.md is missing: {skill_md}")
    for child in list(DEST.iterdir()):
        if child.name == "SKILL.md":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in SOURCE.iterdir():
        if child.name == "SKILL.md" or child.name == "__pycache__":
            continue
        target = DEST / child.name
        if child.is_dir():
            shutil.copytree(child, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(child, target)
    print(f"Synced Codex plugin skill resources from {SOURCE} to {DEST}; preserved Codex SKILL.md")


if __name__ == "__main__":
    main()
