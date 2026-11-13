"""Compare complete-user ranking outputs written by main.py."""
import argparse
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np


def compare(released, direct):
    a = json.loads((released / "summary.json").read_text(encoding="utf-8"))
    d = json.loads((direct / "summary.json").read_text(encoding="utf-8"))
    if a["route"] != "author_snapshot" or d["route"] != "streaming_direct":
        raise ValueError("Provide the released directory first and direct directory second")
    for key in ("config", "shape", "users"):
        if a[key] != d[key]:
            raise ValueError(f"Mismatched {key}")
    for split in ("train", "test"):
        if a["inputs"][split]["sha256"] != d["inputs"][split]["sha256"]:
            raise ValueError(f"Mismatched {split} input")
    n = a["users"]
    if n < 2:
        raise ValueError("At least two complete user outputs are required")
    with np.load(released / "per_user.npz") as ap, np.load(direct / "per_user.npz") as dp:
        if not all(np.array_equal(p["users"], np.arange(n)) and p["top20"].shape == (n, 20)
                   for p in (ap, dp)):
            raise ValueError("Expected full user order and one Top20 list per user")
        result = {}
        normal = NormalDist()
        for key in ("recall10", "recall20", "ndcg10", "ndcg20"):
            delta = (dp[key] - ap[key]) * 100
            mean = float(delta.mean())
            se = float(delta.std(ddof=1) / np.sqrt(n))
            intervals = [[mean - z * se, mean + z * se]
                         for z in (normal.inv_cdf(.975), normal.inv_cdf(1 - .05 / 16))]
            result[key] = {"direct_minus_released_pp": mean, "iid_normal_95_ci_pp": intervals[0],
                           "bonferroni_8_ci_pp": intervals[1]}
        overlap = sum(len(set(x) & set(y)) for x, y in zip(ap["top20"], dp["top20"]))
    return {"config": a["config"], "users": n, "metrics": result,
            "mean_top20_overlap_percent": 100 * overlap / (20 * n)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("released", type=Path)
    parser.add_argument("direct", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.released, args.direct), indent=2))
