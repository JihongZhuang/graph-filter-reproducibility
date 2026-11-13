"""Run the frozen 44-cell schedule with the portable benchmark entry point."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--author-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--affinity", help="optional comma-separated logical CPU IDs")
    parser.add_argument("--dry-run", action="store_true", help="show the schedule without running it")
    args = parser.parse_args()
    schedule = json.loads((ROOT / "configs/schedule.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "configs/reference.json").read_text(encoding="utf-8"))["configs"]
    assert len(schedule) == 44
    if not args.dry_run:
        subprocess.run([sys.executable, str(ROOT / "scripts/verify_inputs.py"),
                        "--data-root", str(args.data_root), "--author-source", str(args.author_source)], check=True)
        args.output.mkdir(parents=True, exist_ok=False)
    for index, cell in enumerate(schedule):
        data = args.data_root / config[cell["config"]]["dataset"]
        run = f"{cell['config']}_{cell['method']}_b{cell['batch']}_r{cell['repeat']}"
        command = [sys.executable, str(ROOT / "benchmark.py")]
        command += ["--author-source", str(args.author_source), "--train", str(data / "R_train_full_official.npz"),
                    "--test", str(data / "R_test.npz"), "--config", cell["config"], "--route", cell["method"],
                    "--batch-size", str(cell["batch"]), "--threads", "4", "--output", str(args.output / run)]
        if args.affinity:
            command.extend(["--affinity", args.affinity])
        if args.dry_run:
            print(run)
        else:
            subprocess.run(command, check=True)
            if index + 1 < len(schedule):
                time.sleep(15)

