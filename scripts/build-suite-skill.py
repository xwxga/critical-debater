#!/usr/bin/env python3
"""Build single-suite skill bundles for ClawHub/OpenClaw, Claude, and OpenAI."""

from __future__ import annotations

import argparse
import json
import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "skills-src" / "critical-debater-suite"

TARGETS = {
    "clawhub": ROOT / "skills" / "critical-debater-suite",
    "claude": ROOT / ".claude" / "skills" / "critical-debater-suite",
    "openai": ROOT / "openai" / "skills" / "critical-debater-suite",
}

RESOURCE_DIRS = ["capabilities", "references", "scripts", "examples"]


def load_config(path: Path) -> dict:
    # Keep parser dependency-free: skill.yaml is valid JSON (also valid YAML).
    return json.loads(path.read_text(encoding="utf-8"))


def folded_yaml_text(key: str, value: str) -> str:
    wrapped = textwrap.wrap(value, width=88, break_long_words=False, break_on_hyphens=False)
    if not wrapped:
        wrapped = [""]
    return "\n".join([f"{key}: >"] + [f"  {line}" for line in wrapped])


def render_frontmatter(cfg: dict, target: str) -> str:
    lines = ["---", f"name: {cfg['name']}", folded_yaml_text("description", cfg["description"])]

    if target == "clawhub":
        lines.append(f"version: {cfg['version']}")
        lines.append(f"license: {cfg['license']}")
        metadata = {
            "openclaw": {
                "requires": {"bins": cfg["requires_bins"]},
                "homepage": cfg["platform_overrides"]["clawhub"]["homepage"],
                "emoji": cfg["platform_overrides"]["clawhub"]["emoji"],
            }
        }
        lines.append("metadata: " + json.dumps(metadata, ensure_ascii=False, separators=(",", ":")))

    lines.append("---")
    return "\n".join(lines)


def clean_target(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_resources(src_root: Path, dst_root: Path) -> None:
    for directory in RESOURCE_DIRS:
        shutil.copytree(
            src_root / directory,
            dst_root / directory,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )


def build_target(cfg: dict, body: str, target: str, out_dir: Path) -> None:
    clean_target(out_dir)
    copy_resources(SRC, out_dir)
    for cache_dir in out_dir.rglob("__pycache__"):
        shutil.rmtree(cache_dir, ignore_errors=True)
    for pyc in out_dir.rglob("*.pyc"):
        pyc.unlink(missing_ok=True)
    skill_md = render_frontmatter(cfg, target) + "\n\n" + body.strip() + "\n"
    (out_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build critical-debater-suite skill bundles")
    parser.add_argument(
        "--targets",
        default="clawhub,claude,openai",
        help="Comma-separated targets: clawhub,claude,openai",
    )
    return parser.parse_args()


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing source directory: {SRC}")

    cfg = load_config(SRC / "skill.yaml")
    body = (SRC / "SKILL.body.md").read_text(encoding="utf-8")

    requested = [x.strip() for x in parse_args().targets.split(",") if x.strip()]
    unknown = sorted(set(requested) - set(TARGETS))
    if unknown:
        raise SystemExit(f"unknown targets: {unknown}")

    for target in requested:
        build_target(cfg, body, target, TARGETS[target])
        print(f"built {target}: {TARGETS[target]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
