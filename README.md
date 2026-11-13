# The Cost of Keeping a Basis: Quality–Resource Tradeoffs in Graph-Filter Recommendation

This artifact studies the cost of evaluating one fixed low-degree polynomial filter per recommendation request. It contains the two scoring routes, frozen experimental configurations, aggregate records for 44 complete-user runs, and scripts for rebuilding Tables 1–6 and Figures 1–3.

The streaming route evaluates the implicit graph action Pz = Bᵀ(Bz) and immediately accumulates each polynomial term. The released baseline evaluates its pinned Mem-GF projection and maps the scores back to the item catalog. Both routes use the same graph, filter coefficients and evaluation criteria. The released projection and direct polynomial yield different predictions, so the manuscript evaluates both resource costs and ranking quality.

## Environment

Use Python 3.12 and CPU PyTorch. The reported runs used Windows 11, an Intel CPU with four assigned logical CPUs spanning two physical cores, four PyTorch compute threads and one inter-op thread. See [configs/formal_environment.json](configs/formal_environment.json) for the frozen protocol details.

```text
python -m venv .venv
```

Activate the environment, then run these commands from the repository root.

```text
python -m pip install -r requirements.txt
python scripts/download_reference.py
python main.py --author-source external/memgf --self-check --threads 1
python benchmark.py --author-source external/memgf --self-check --threads 1 --output runs/smoke
```

The source fetch is hash-checked against a fixed Mem-GF commit. To use an independently obtained copy of that commit, pass `--source PATH` to the fetch script. The self-check uses synthetic matrices.

## Data preparation

Obtain the two processed splits as described in [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md). Keep the downloaded interaction files outside any shared repository. Under the local working tree, place the four `train.txt` and `test.txt` files in `data/lightgcn_text/{yelp2018,amazon-book}/`.

```text
python prepare_data.py --raw-root data/lightgcn_text --output data/processed
python scripts/verify_inputs.py --data-root data/processed --author-source external/memgf
```

Conversion preserves the original user and item IDs and the full training and test sets. The reconstruction report includes matrix shapes, interaction counts, and file and sparse-content hashes.

## Complete-user evaluation

Run these commands separately. Each output directory must be new.

```text
python main.py --author-source external/memgf --train data/processed/yelp2018/R_train_full_official.npz --test data/processed/yelp2018/R_test.npz --config yelp_f5 --route streaming_direct --batch-size 64 --threads 4 --output runs/yelp_direct
python main.py --author-source external/memgf --train data/processed/amazon-book/R_train_full_official.npz --test data/processed/amazon-book/R_test.npz --config amazon_f2 --route streaming_direct --batch-size 64 --threads 4 --output runs/amazon_direct
```

For each dataset, repeat with `--route author_snapshot` and a different output directory. The evaluator visits every user and scores the full item catalog. It masks training interactions, resolves score ties by ascending item ID and ranks up to 20 eligible items. It calculates Recall and NDCG at cutoffs 10 and 20 per user, assigns zero to empty test sets, and takes the all-user mean. The JSON summary contains these four aggregate metrics. Individual rankings and score hashes are written only to the local run directory.

## Performance replay

Replace `main.py` with `benchmark.py` in an evaluation command and use a new output directory. The benchmark measures elapsed time from child process launch through exit. It samples RSS across the child lifetime and uses the Windows process lifetime peak when available. The portable replay uses a different output/checkpoint procedure from the original Windows timing harness. Compare new timings within the portable protocol. Tables 1–2 and 5 use the archived original measurements.

```text
python experiments/run_schedule.py --data-root data/processed --author-source external/memgf --output runs/schedule --dry-run
```

Remove `--dry-run` to run the full schedule. The script validates hashes before running, uses fresh processes in the frozen order, and waits 15 seconds between processes. An optional `--affinity` argument accepts a comma-separated list of logical CPU IDs. Time and memory depend on the hardware and system load.

## Rebuild tables and figures

```text
python experiments/build_tables.py --output runs/tables
python experiments/plot_figures.py --output runs/figures
```

Table 1 reports medians and ranges, Table 2 paired ratios and percentile bootstrap intervals, Table 3 default-filter quality, Table 4 the operation structure, Table 5 the 14 exploratory measurements and Table 6 their alternate-filter quality rows. The CSV outputs already checked against the paper are in `results/tables/`. The script verifies all 44 run identities and recomputes paired statistics from the aggregate records. Figure 1 uses the saved diagram inventory. Figures 2–3 use frozen full-precision plotting data. Figure regeneration uses installed Arial and Cambria Math fonts. Windows uses its system font directory by default. On another platform pass `--font-dir` with a directory containing `arial.ttf`, `arialbd.ttf`, and `cambria.ttc`.

Figure 3 uses archived aggregate paired-user intervals and set overlap. To independently recalculate these quantities after running both routes, use python experiments/compare_quality.py runs/yelp_released runs/yelp_direct (or the corresponding Amazon-book directories). See [CODE_AVAILABILITY.md](CODE_AVAILABILITY.md) for the artifact scope.
