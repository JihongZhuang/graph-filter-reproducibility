"""Rebuild Tables 1--6 from the frozen aggregate evidence."""
import argparse
import csv
import json
from pathlib import Path

from original_statistical_functions import grouped, pair_comparisons

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
METRICS = ("recall10", "recall20", "ndcg10", "ndcg20")
DEFAULT = ("yelp_f5", "amazon_f2")
ALTERNATE = ("amazon_f5", "yelp_f2")
METHODS = ("author_snapshot", "streaming_direct")


def load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def describe(stats, unit):
    return [f"{stats[k] / unit:.2f}" for k in ("median", "min", "max")]


def tables():
    rows = load("observations.json")
    schedule = json.loads((ROOT / "configs/schedule.json").read_text(encoding="utf-8"))
    identity = ("config", "Q", "method", "batch", "repeat", "stage")
    assert len(rows) == len(schedule) == 44
    assert all(all(row[k] == cell[k] for k in identity) for row, cell in zip(rows, schedule))
    assert all(r["quality_audit_passed"] for r in rows)
    assert sum(r["stage"] == "controlled_main_and_budget" for r in rows) == 30
    groups = grouped(rows)
    pairs = pair_comparisons(rows)
    assert pairs == load("paired_statistics.json")
    t1, t2, t3, t5, t6 = [], [], [], [], []
    for cfg in DEFAULT:
        for method, batch in ((*[(method, 64) for method in METHODS], (METHODS[0], 32))):
            g = groups[f"{cfg}/{method}/b{batch}"]
            t1.append([cfg, method, batch, g["n"],
                       *describe(g["statistics"]["parent_wall_seconds"], 60),
                       *describe(g["statistics"]["observed_process_peak_bytes"], 2**20)])
    for cfg in DEFAULT:
        for key in ("same_batch64", "author32_vs_direct64_budget"):
            pair = pairs[f"{cfg}/{key}"]
            ratios = []
            for label in ("time_ratio", "memory_ratio"):
                data = pair[label]
                ratios += [f"{x:.2f}" for x in (data["geometric_mean"], *data["conditional_percentile_95_ci"])]
            t2.append([cfg, key, pair["n_complete_pairs"], *ratios, pair["approximately_equal_peak_all_five_pairs"]])
    for configs, output in ((DEFAULT, t3), (ALTERNATE, t6)):
        for cfg in configs:
            for method in METHODS:
                row = min((r for r in rows if (r["config"], r["method"], r["batch"]) ==
                           (cfg, method, 64)), key=lambda r: r["repeat"])
                output.append([cfg, method, *[f"{100*row['quality'][0][k]:.2f}" for k in METRICS]])
    for r in rows:
        if r["stage"] != "controlled_main_and_budget":
            t5.append([r["config"], r["method"], r["batch"],
                       f"{r['parent_wall_seconds']/60:.2f}", f"{r['observed_process_peak_bytes']/2**20:.2f}"])
    t4 = [
        ["Graph operator", "Implicit P action", "Same implicit P action"],
        ["Propagation", "K Lanczos iterations", "d power actions"],
        ["Sparse multiplications per batch", "2K", "2d"],
        ["Additional response workspace", "Degree-dependent basis", "Constant number of response and accumulation blocks"],
        ["Projection and back-projection", "Required", "Direct item-score accumulation"],
    ]
    return [
        (["configuration", "route", "batch", "runs", "median_min", "min_min", "max_min",
          "median_MiB", "min_MiB", "max_MiB"], t1),
        (["configuration", "comparison", "pairs", "time_ratio", "time_ci_low", "time_ci_high",
          "peak_ratio", "peak_ci_low", "peak_ci_high", "all_pairs_near_peak"], t2),
        (["configuration", "route", *METRICS], t3),
        (["component", "released", "direct"], t4),
        (["configuration", "route", "batch", "minutes", "peak_MiB"], t5),
        (["configuration", "route", *METRICS], t6),
    ]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    content = tables()
    args.output.mkdir(parents=True, exist_ok=False)
    for number, (header, data) in enumerate(content, 1):
        with (args.output / f"table{number}.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(data)
    print("Tables 1--6 rebuilt; 44 aggregate records and paired statistics verified.")
