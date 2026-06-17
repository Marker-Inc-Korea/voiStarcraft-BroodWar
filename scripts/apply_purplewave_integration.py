#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "integrations" / "purplewave"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Voi commander integration templates to a PurpleWave checkout.")
    parser.add_argument("purplewave_root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = args.purplewave_root
    lifecycle = root / "src" / "Lifecycle" / "PurpleWave.scala"
    target_dir = root / "src" / "Commander"

    if not lifecycle.exists():
        raise SystemExit(f"missing PurpleWave lifecycle file: {lifecycle}")

    print(f"target={root}")
    print(f"copy Commander templates -> {target_dir}")
    print(f"patch lifecycle -> {lifecycle}")
    if args.dry_run:
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    for name in ["CommanderIntent.scala", "CommanderQueueConsumer.scala", "CommanderTelemetry.scala"]:
        shutil.copy2(TEMPLATE_DIR / name, target_dir / name)

    text = lifecycle.read_text(encoding="utf-8")
    marker = 'tryCatch(() => Commander.CommanderQueueConsumer.poll("runtime/commands.jsonl"))'
    if marker not in text:
        needle = "With.performance.startFrame()\n"
        replacement = f'With.performance.startFrame()\n        {marker}\n'
        if needle not in text:
            raise SystemExit("could not locate With.performance.startFrame() insertion point")
        text = text.replace(needle, replacement, 1)
        lifecycle.write_text(text, encoding="utf-8")
    print("applied=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
