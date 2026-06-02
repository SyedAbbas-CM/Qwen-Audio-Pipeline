from __future__ import annotations

import argparse
import csv
from pathlib import Path

from voice_direction import build_variants


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "transcripts" / "devlog-final-manifest.tsv"
DEFAULT_OUTPUT = ROOT / "transcripts" / "devlog-final-takes.tsv"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--takes", type=int, default=2)
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    with open(args.manifest, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            seg_id = row["id"].strip()
            marker = row["marker"].strip()
            title = row["title"].strip()
            style = row["style"].strip()
            intent = row.get("intent", "").strip() or "explaining"
            text = row["text"].strip()
            for take_idx, variant in enumerate(build_variants(text, style, args.takes, intent=intent), start=1):
                rows.append(
                    {
                        "job_id": f"{seg_id}-take-{take_idx:02d}",
                        "segment_id": seg_id,
                        "marker": marker,
                        "title": title,
                        "take": f"{take_idx:02d}",
                        "style": style,
                        "intent": variant.get("intent", intent),
                        "energy": variant["energy"],
                        "temperature": variant["temperature"],
                        "text": variant["text"],
                    }
                )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["job_id", "segment_id", "marker", "title", "take", "style", "intent", "energy", "temperature", "text"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
