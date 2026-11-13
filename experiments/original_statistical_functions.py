"""Verbatim selected definitions from frozen update_study.py; no harness import."""
import math
import random
import statistics

SEED, RESAMPLES, EXPECTED_PAIRS = 20261021, 10000, 5

MAIN = ('amazon_f2', 'yelp_f5')

def quantile(values, probability):
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

def describe(values):
    values = [float(value) for value in values if value is not None]
    if not values:
        return {'n': 0, 'raw': []}
    q1, q3 = quantile(values, .25), quantile(values, .75)
    return {'n': len(values), 'median': statistics.median(values), 'q25': q1, 'q75': q3,
            'iqr': q3 - q1, 'min': min(values), 'max': max(values), 'raw': values}

def paired_ratio(values, complete_five):
    result = describe(values)
    result.update(bootstrap_seed=SEED, bootstrap_resamples=RESAMPLES,
        estimand='Geometric mean of within-repeat author/candidate ratios',
        status='complete_five_pairs' if complete_five else 'partial_no_stable_conclusion')
    if not values:
        return result
    logs = [math.log(value) for value in values]
    result['geometric_mean'] = math.exp(statistics.mean(logs))
    if complete_five:
        assert len(values) == EXPECTED_PAIRS
        rng = random.Random(SEED)
        bootstrap = sorted(math.exp(sum(rng.choice(logs) for _ in logs) / len(logs)) for _ in range(RESAMPLES))
        result['conditional_percentile_95_ci'] = [quantile(bootstrap, .025), quantile(bootstrap, .975)]
        result['ci_limit'] = 'n=5 only; descriptive paired bootstrap, conditional on these runs; no simultaneous or universal claim'
    return result

def memory_match(gaps, complete_five):
    return bool(complete_five and len(gaps) == EXPECTED_PAIRS and all(gap <= .05 for gap in gaps))

FIELDS = ('parent_wall_seconds', 'parent_unbiased_active_seconds', 'worker_cpu_seconds_at_complete',
    'imports_seconds', 'data_to_last_metric_seconds', 'data_to_final_commit_seconds',
    'rss_full_lifecycle_sampled_peak_bytes', 'windows_lifetime_peak_bytes', 'observed_process_peak_bytes',
    'rss_formal_peak_bytes', 'rss_formal_baseline_bytes', 'rss_formal_growth_bytes',
    'rss_graph_ready_bytes', 'rss_post_graph_peak_bytes', 'rss_post_graph_growth_bytes', 'actual_SpMM')

def grouped(rows):
    groups = {}
    for row in rows:
        key = f"{row['config']}/{row['method']}/b{row['batch']}"
        groups.setdefault(key, []).append(row)
    result = {}
    for key, values in groups.items():
        phases = sorted({field for row in values for field in row['phases']})
        result[key] = {'n': len(values), 'stage': values[0]['stage'],
            'interpretation': 'exploratory_n1' if values[0]['stage'] != 'controlled_main_and_budget' else ('five_repeats_complete' if len(values) == 5 else 'partial_no_stable_conclusion'),
            'statistics': {field: describe([row.get(field) for row in values]) for field in FIELDS},
            'phases_seconds': {field: describe([row['phases'].get(field, 0) for row in values]) for field in phases},
            'repeats': [row['repeat'] for row in values]}
    return result

def pair_comparisons(rows):
    chosen = {(row['config'], row['method'], row['batch'], row['repeat']): row for row in rows}
    comparisons = {}
    for config in MAIN:
        for label, author_batch in (('same_batch64', 64), ('author32_vs_direct64_budget', 32)):
            pairs = []
            for repeat in range(EXPECTED_PAIRS):
                author = chosen.get((config, 'author_snapshot', author_batch, repeat))
                direct = chosen.get((config, 'streaming_direct', 64, repeat))
                if author is None or direct is None:
                    continue
                a, d = author['observed_process_peak_bytes'], direct['observed_process_peak_bytes']
                pairs.append({'repeat': repeat, 'author_directory': author['directory'], 'direct_directory': direct['directory'],
                    'author_parent_seconds': author['parent_wall_seconds'], 'direct_parent_seconds': direct['parent_wall_seconds'],
                    'author_observed_peak_bytes': a, 'direct_observed_peak_bytes': d,
                    'time_ratio_author_over_direct': author['parent_wall_seconds'] / direct['parent_wall_seconds'],
                    'memory_ratio_author_over_direct': a / d, 'relative_peak_gap': abs(a - d) / max(a, d),
                    'direct_peak_relation_to_author': 'higher' if d > a else ('lower' if d < a else 'equal'),
                    'within_5_percent_peak': abs(a - d) / max(a, d) <= .05})
            complete = len(pairs) == EXPECTED_PAIRS
            matched = memory_match([pair['relative_peak_gap'] for pair in pairs], complete)
            comparisons[f'{config}/{label}'] = {'n_complete_pairs': len(pairs), 'expected_pairs': EXPECTED_PAIRS,
                'complete_five_pairs': complete, 'pairs': pairs,
                'direct_peak_direction_counts': {label: sum(pair['direct_peak_relation_to_author'] == label for pair in pairs) for label in ('higher', 'lower', 'equal')},
                'time_ratio': paired_ratio([pair['time_ratio_author_over_direct'] for pair in pairs], complete),
                'memory_ratio': paired_ratio([pair['memory_ratio_author_over_direct'] for pair in pairs], complete),
                'approximately_equal_peak_all_five_pairs': matched,
                'memory_match_rule': 'Every one of five paired gaps abs(author-direct)/max(author,direct) <=5%; peak=max(full-lifecycle sampled RSS, Windows lifetime peak).',
                'memory_interpretation': ('approximately_equal_observed_peak' if matched else
                    ('partial_no_memory_match_claim' if not complete else 'measured_resource_budgets_differ_report_each_pair'))}
    return comparisons

def observed_pareto(groups):
    result = {}
    for config in sorted({key.split('/')[0] for key in groups}):
        points = {key: {'time_median_seconds': group['statistics']['parent_wall_seconds']['median'],
            'peak_median_bytes': group['statistics']['observed_process_peak_bytes']['median'], 'n': group['n']}
            for key, group in groups.items() if key.split('/')[0] == config}
        for key, point in points.items():
            point['dominated_by_observed_medians'] = [other for other, candidate in points.items()
                if other != key and candidate['time_median_seconds'] <= point['time_median_seconds']
                and candidate['peak_median_bytes'] <= point['peak_median_bytes']
                and (candidate['time_median_seconds'] < point['time_median_seconds'] or candidate['peak_median_bytes'] < point['peak_median_bytes'])]
        result[config] = {'points': points, 'observed_front': [key for key, point in points.items() if not point['dominated_by_observed_medians']],
            'limit': 'Descriptive resource medians only; mixed repeat counts/partial observations and different predictor semantics; not a quality-equivalent or global optimum.'}
    return result
