from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs" / "qwen3-devlog"


def load_statuses(root: Path) -> dict[str, dict]:
    items: dict[str, dict] = {}
    for seg_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for status_path in sorted(seg_dir.glob("take-*-clean.status.json")):
            try:
                items[str(status_path)] = json.loads(status_path.read_text(encoding="utf-8"))
            except Exception:
                items[str(status_path)] = {"status": "unreadable"}
    return items


def summarize_change(path: str, data: dict) -> str:
    seg = Path(path).parent.name
    take = Path(path).name.replace("-clean.status.json", "")
    status = data.get("status", "unknown")
    dur = data.get("duration_sec", "")
    return f"{seg} {take} -> {status} ({dur}s)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--interval-sec", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    root = Path(args.output_dir)
    seen = load_statuses(root) if root.exists() else {}

    if args.once:
        for path, data in seen.items():
            print(summarize_change(path, data))
        return 0

    print(f"watching {root}")
    try:
        while True:
            time.sleep(args.interval_sec)
            current = load_statuses(root) if root.exists() else {}
            for path, data in current.items():
                old = seen.get(path)
                if old != data:
                    print(summarize_change(path, data), flush=True)
            seen = current
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
