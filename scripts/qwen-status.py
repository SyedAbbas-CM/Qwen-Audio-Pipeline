from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "outputs" / "qwen3-reftext-full-v2"


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--fail-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.output_dir)
    print("segment\ttake\tstatus\tgen_sec\tclean\traw\tnotes")
    for seg_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for status_path in sorted(seg_dir.glob("take-*-clean.status.json")):
            data = json.loads(status_path.read_text(encoding="utf-8"))
            take = status_path.name.replace("-clean.status.json", "")
            clean_exists = "yes" if Path(data["output_clean"]).exists() else "no"
            raw_exists = "yes" if Path(data["output_raw"]).exists() else "no"
            duration = data.get("duration_sec", "")
            status = data.get("status", "unknown")
            supervisor_pid = data.get("supervisor_pid")
            child_pid = data.get("child_pid")
            notes: list[str] = []
            if status == "timeout":
                notes.append("retry")
            if status == "qwen_failed":
                notes.append("check-log")
            if status == "postprocess_failed":
                notes.append("cleanup-failed")
            if status == "ready" and clean_exists == "no":
                notes.append("missing-clean")
            if status == "running":
                if pid_alive(int(child_pid) if child_pid else None) or pid_alive(int(supervisor_pid) if supervisor_pid else None):
                    notes.append("running-active")
                else:
                    notes.append("running-stale")
            if args.fail_only and status not in {"timeout", "qwen_failed", "postprocess_failed"}:
                continue
            print(
                f"{seg_dir.name}\t{take}\t{status}\t{duration}\t{clean_exists}\t{raw_exists}\t{','.join(notes)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
