#!/usr/bin/env python3
"""Frozen operational-distinction assay against Costanzo 2016 NxN yeast SGA.

Do not tune thresholds, seeds, baselines, or witness rule after seeing target outcomes.
Primary: KNN lower-confidence-bound selector versus same-KNN point ranking.
NOTE: selection uses query mutants' observed 8-background panel, and training
mutants' candidate-background readouts. Withheld target readouts are never used
until the preoutcome prediction artifact is written and SHA256-committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.neighbors import NearestNeighbors

SEED = 20261019
KNOWN = 8
CANDIDATES = 128
MAX_PAIRS = 100
GAP_EQUIVALENT = 0.08
GAP_DISTINCT = 0.16
K_NEIGHBORS = 31
CAL_VALIDATION = 0.20
MIN_TRAIN_NONMISSING = 0.85
EXPECTED_MATRIX_SHA256 = '10e82acc42fe66416111cfecd7b62040c284664741df15bd2c3d95f7f410bd9c'
SOURCE_URLS = [
  'https://thecellmap.org/costanzo2016/data_files/Raw%20genetic%20interaction%20datasets%3A%20Matrix%20format.zip',
  'https://thecellmap.org/costanzo2016/data_files/Raw%20genetic%20interaction%20datasets:%20Matrix%20format.zip',
]
METHODS = ('warrant_lcb', 'knn_point', 'ridge_point', 'global_variance', 'random')


def dump_atomic(p: Path, data: object) -> str:
    p.parent.mkdir(parents=True, exist_ok=True)
    b = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
    p.write_bytes(b)
    return hashlib.sha256(b).hexdigest()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def acquire(cache: Path) -> tuple[Path, dict]:
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / 'SGA_NxN_clustered.cdt'
    provenance = {'source_page': 'https://thecellmap.org/yeast/costanzo2016/',
                  'dataset': 'Costanzo 2016 NxN SGA interaction-score matrix',
                  'expected_cdt_sha256': EXPECTED_MATRIX_SHA256,
                  'original_paper': 'https://doi.org/10.1126/science.aaf1420'}
    if target.exists():
        provenance['acquisition'] = 'cached_source_file'
    else:
        archive = cache / 'official_matrix.zip'
        errors = []
        for url in SOURCE_URLS:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'research-reproducer/1.0'})
                with urllib.request.urlopen(req, timeout=150) as stream, open(archive, 'wb') as out:
                    import shutil
                    shutil.copyfileobj(stream, out)
                with zipfile.ZipFile(archive) as z:
                    names = [n for n in z.namelist() if n.endswith('/SGA_NxN_clustered.cdt') or n == 'SGA_NxN_clustered.cdt']
                    if len(names) != 1:
                        raise RuntimeError(f'NxN member count is {len(names)}')
                    with z.open(names[0]) as src, open(target, 'wb') as out:
                        shutil.copyfileobj(src, out)
                    provenance.update({'archive_url': url, 'archive_sha256': sha(archive),
                                       'archive_member': names[0], 'archive_bytes': archive.stat().st_size})
                archive.unlink()
                break
            except Exception as exc:
                errors.append(f'{url}: {type(exc).__name__}: {exc}')
                if target.exists(): target.unlink()
                if archive.exists(): archive.unlink()
        else:
            raise RuntimeError('DATA_ACQUISITION_BLOCKED\n' + '\n'.join(errors))
    digest = sha(target)
    provenance.update({'cdt_sha256': digest, 'cdt_bytes': target.stat().st_size})
    if digest != EXPECTED_MATRIX_SHA256:
        raise RuntimeError(f'SOURCE_IDENTITY_MISMATCH expected {EXPECTED_MATRIX_SHA256} observed {digest}; no data evaluated')
    return target, provenance


def parse_cdt(path: Path) -> tuple[np.ndarray, list[str], list[str]]:
    # The first line is the real column header; the next five lines are metadata.
    # Columns beginning "dma" are nonessential deletion arrays (verified by
    # TheCellMap source documentation and published teaching material).
    cols = list(pd.read_csv(path, sep='\t', nrows=0).columns)
    score_cols = [c for c in cols if str(c).lower().startswith('dma')]
    assert len(score_cols) > 1000, f'Not a full NxN DMA matrix: {len(score_cols)} columns'
    assert 'ORF' in cols, f'Missing source row identifier ORF: {cols[:12]}'
    df = pd.read_csv(path, sep='\t', skiprows=range(1, 6), usecols=['ORF'] + score_cols,
                     low_memory=False)
    query_ids = df['ORF'].astype(str).tolist()
    assert len(query_ids) > 2500, f'Unexpectedly few query rows: {len(query_ids)}'
    score = df[score_cols].apply(pd.to_numeric, errors='coerce').to_numpy(dtype=np.float32)
    if not np.isfinite(score).any(): raise RuntimeError('No finite interaction scores parsed')
    return score, query_ids, score_cols


def knn_predictions(Xtrain: np.ndarray, Ytrain: np.ndarray, Xnew: np.ndarray, k: int = K_NEIGHBORS) -> np.ndarray:
    """Equal 1/(distance+0.05) neighbor weighting; same model for both arms."""
    assert np.isfinite(Xtrain).all() and np.isfinite(Xnew).all()
    assert len(Xtrain) > k
    nbrs = NearestNeighbors(n_neighbors=k, algorithm='auto', metric='euclidean').fit(Xtrain)
    distances, indexes = nbrs.kneighbors(Xnew)
    ws = 1.0 / (distances + 0.05)
    Ys = Ytrain[indexes]
    ok = np.isfinite(Ys)
    nums = np.where(ok, Ys * ws[:, :, None], 0.0).sum(axis=1)
    dens = np.where(ok, ws[:, :, None], 0.0).sum(axis=1)
    return np.divide(nums, dens, out=np.full_like(nums, np.nan), where=dens > 0)


def ridge_predictions(Xtrain: np.ndarray, Ytrain: np.ndarray, Xnew: np.ndarray) -> np.ndarray:
    output = np.full((len(Xnew), Ytrain.shape[1]), np.nan, dtype=float)
    for c in range(Ytrain.shape[1]):
        good = np.isfinite(Ytrain[:, c])
        if good.sum() >= 100:
            fit = Ridge(alpha=5.0).fit(Xtrain[good], Ytrain[good, c])
            output[:, c] = fit.predict(Xnew)
    return output


def split_and_predict(mat: np.ndarray, queries: list[str], arrays: list[str], output: Path) -> tuple[dict, np.ndarray]:
    rng = np.random.default_rng(SEED)
    nrows, ncols = mat.shape
    shuffled_rows = rng.permutation(nrows)
    cut = int(nrows * 0.75)
    cal_all, target_all = shuffled_rows[:cut], shuffled_rows[cut:]
    # Column eligibility uses only non-target mutant readouts. No target
    # candidate-background value or missingness is inspected until evaluation.
    frac = np.isfinite(mat[cal_all]).mean(axis=0)
    eligible = np.flatnonzero(frac >= MIN_TRAIN_NONMISSING)
    assert len(eligible) >= KNOWN + CANDIDATES, f'Insufficient eligible columns {len(eligible)}'
    cols = rng.permutation(eligible)[:KNOWN + CANDIDATES]
    known_cols, candidate_cols = cols[:KNOWN], cols[KNOWN:]
    good_cal = cal_all[np.isfinite(mat[np.ix_(cal_all, known_cols)]).all(axis=1)]
    good_target = target_all[np.isfinite(mat[np.ix_(target_all, known_cols)]).all(axis=1)]
    assert len(good_cal) >= 500 and len(good_target) >= 100
    # Primary train/validation split for independent calibration of the
    # uncertainty penalty. Cal-valid records are not used to fit its residuals.
    nvalid = int(len(good_cal) * CAL_VALIDATION)
    cv = good_cal[:nvalid]
    ct = good_cal[nvalid:]
    Xct, Yct = mat[np.ix_(ct, known_cols)].astype(float), mat[np.ix_(ct, candidate_cols)].astype(float)
    Xcv, Ycv = mat[np.ix_(cv, known_cols)].astype(float), mat[np.ix_(cv, candidate_cols)].astype(float)
    Pcv = knn_predictions(Xct, Yct, Xcv)
    err = Ycv - Pcv
    n = np.isfinite(err).sum(axis=0)
    rmse = np.sqrt(np.divide(np.nansum(err ** 2, axis=0), np.maximum(n, 1)))
    rmse[n < 30] = np.nan
    Xcal = mat[np.ix_(good_cal, known_cols)].astype(float)
    Ycal = mat[np.ix_(good_cal, candidate_cols)].astype(float)
    Xt = mat[np.ix_(good_target, known_cols)].astype(float)
    knn = knn_predictions(Xcal, Ycal, Xt)
    ridge = ridge_predictions(Xcal, Ycal, Xt)
    var = np.nanstd(Ycal, axis=0)
    # Greedy independent (disjoint) pairing using only first-stage measurements.
    # Each target mutant may appear at most once; no selection from withheld values.
    order = rng.permutation(len(good_target))
    unused = set(int(i) for i in order)
    pairs: list[tuple[int, int]] = []
    for a in order:
        a = int(a)
        if a not in unused: continue
        unused.remove(a)
        options = [b for b in sorted(unused) if queries[good_target[a]] != queries[good_target[b]]
                   and np.max(np.abs(Xt[a] - Xt[b])) <= GAP_EQUIVALENT]
        if not options: continue
        b = min(options, key=lambda z: (float(np.max(np.abs(Xt[a] - Xt[z]))), z))
        unused.remove(b)
        pairs.append((a, b))
        if len(pairs) >= MAX_PAIRS: break
    assert len(pairs) >= 20, f'Only {len(pairs)} operationally equivalent pairs: predeclared insufficient-data gate'
    attempts = []
    for index, (a, b) in enumerate(pairs):
        pknn = np.abs(knn[a] - knn[b])
        pridge = np.abs(ridge[a] - ridge[b])
        # 1.96 * sqrt(2) assumes exchangeable independent row errors; this is
        # an explicitly imperfect uncertainty model, calibrated out-of-sample.
        lcb = pknn - 1.96 * np.sqrt(2.0) * rmse
        choices = {
            'warrant_lcb': int(np.nanargmax(lcb)),
            'knn_point': int(np.nanargmax(pknn)),
            'ridge_point': int(np.nanargmax(pridge)),
            'global_variance': int(np.nanargmax(var)),
            'random': int(rng.integers(0, CANDIDATES)),
        }
        attempts.append({
            'pair_index': index,
            'query_a': queries[good_target[a]], 'query_b': queries[good_target[b]],
            'target_row_a': int(good_target[a]), 'target_row_b': int(good_target[b]),
            'observed_panel_max_gap': float(np.max(np.abs(Xt[a] - Xt[b]))),
            'choices': {name: {'candidate_array_index': int(candidate_cols[ci]),
                               'candidate_array': arrays[int(candidate_cols[ci])],
                               'predicted_gap': float(pknn[ci]) if name == 'warrant_lcb' else
                                   (float(pknn[ci]) if name == 'knn_point' else
                                    float(pridge[ci]) if name == 'ridge_point' else None),
                               'lcb': float(lcb[ci]) if name == 'warrant_lcb' else None,
                               'warranted_prediction': bool(lcb[ci] >= GAP_DISTINCT) if name == 'warrant_lcb' else None}
                        for name, ci in choices.items()},
        })
    seal = {
        'protocol': 'biology-operational-distinction-v1',
        'model': 'KNN31 inverse-distance + 1.96 sqrt(2) held-calibration residual penalty',
        'seed': SEED,
        'measurement': 'NxN genetic interaction score epsilon, not growth or p-value',
        'eq': GAP_EQUIVALENT, 'distinction': GAP_DISTINCT,
        'selection': '8 measured contexts; 128 candidate contexts; 100 max disjoint pairs',
        'n_all_rows': nrows, 'n_all_array_cols': ncols,
        'n_eligible_contexts': len(eligible), 'n_calibrating_rows': len(good_cal),
        'n_target_rows': len(good_target), 'n_pairs': len(pairs),
        'known_array_indices': [int(x) for x in known_cols],
        'candidate_array_indices': [int(x) for x in candidate_cols],
        'attempts': attempts,
    }
    digest = dump_atomic(output / 'sealed_predictions.json', seal)
    print(f'SEALED_PREOUTCOME_PREDICTIONS_SHA256={digest}', flush=True)
    return seal, candidate_cols


def audit_predictions(seal: dict, mat: np.ndarray, candidate_cols: np.ndarray, out: Path) -> dict:
    # This function is the FIRST place that target/candidate interaction values
    # can be read (after writing + hashing all selectors' choices).
    metrics = {m: {'attempted': 0, 'observed': 0, 'detected': 0, 'sum_observed_gap': 0.0,
                   'gaps': [], 'pass': []} for m in METHODS}
    any_separator = 0
    actual = []
    for attempt in seal['attempts']:
        a,b = attempt['target_row_a'],attempt['target_row_b']
        truth = np.abs(mat[a, candidate_cols] - mat[b, candidate_cols])
        # Unknown measurements are never treated as negative biological evidence.
        finite = np.isfinite(truth)
        can_separate = bool(np.any(truth[finite] >= GAP_DISTINCT))
        any_separator += int(can_separate)
        entry = {'pair_index': attempt['pair_index'], 'potentially_distinguishable': can_separate,
                 'eligible_measured_candidates': int(finite.sum()), 'observations': {}}
        for method in METHODS:
            ix = attempt['choices'][method]['candidate_array_index']
            loc = int(np.flatnonzero(candidate_cols == ix)[0]); gap = float(truth[loc])
            observed = bool(np.isfinite(gap))
            detected = bool(observed and gap >= GAP_DISTINCT)
            m = metrics[method]
            m['attempted'] += 1
            m['observed'] += int(observed)
            m['detected'] += int(detected)
            m['sum_observed_gap'] += gap if observed else 0.0
            m['gaps'].append(gap if observed else None)
            m['pass'].append(detected)
            entry['observations'][method] = {'measured': observed, 'actual_abs_epsilon_gap': gap if observed else None,
                                              'distinction_detected': detected}
        actual.append(entry)
    summary = {}
    for method, m in metrics.items():
        summary[method] = {'attempts': m['attempted'], 'observed': m['observed'],
                           'detected': m['detected'], 'detection_rate_all_attempts': m['detected']/m['attempted'],
                           'mean_gap_observed_only': m['sum_observed_gap']/max(1,m['observed']),
                           'missing_outcome_count': m['attempted']-m['observed']}
    primary = np.array(metrics['warrant_lcb']['pass'],dtype=int) - np.array(metrics['knn_point']['pass'],dtype=int)
    rng = np.random.default_rng(2026101901)
    boot = np.array([primary[rng.integers(0,len(primary),size=len(primary))].mean() for _ in range(2000)])
    certified = [r for r in actual if seal['attempts'][r['pair_index']]['choices']['warrant_lcb']['warranted_prediction']]
    certified_yes = sum(1 for r in certified if r['observations']['warrant_lcb']['distinction_detected'])
    summary['warrant_lcb']['emitted_warrants'] = len(certified)
    summary['warrant_lcb']['correct_emitted_warrants'] = certified_yes
    report = {
        'status': 'EVALUATED_REAL_OBSERVATIONS',
        'holdout_type': 'retrospective, concealed target×candidate matrix cells; not new experiments',
        'threshold_note': 'difference in epsilon >= 0.16 is operational threshold; no per-cell p-values in matrix',
        'predictions_sha256': sha(out/'sealed_predictions.json'),
        'pairs_with_any_measured_separator_in_128_candidates': any_separator,
        'all_pairs': len(seal['attempts']),
        'metrics': summary,
        'primary_lcb_minus_same_knn_point_precision': float(primary.mean()),
        'paired_pair_bootstrap_95_interval': [float(x) for x in np.quantile(boot,[0.025,0.975])],
        'not_claimed': ['novel biology', 'single-mutant fitness equivalence', 'source-independent method invention',
                        'true physical biological prospectivity', 'per-cell statistical significance',
                        'advantage if confidence interval includes zero or baseline wins'],
        'each_pair': actual,
    }
    print('EXPERIMENT_PRIMARY_RESULT='+json.dumps({k:v for k,v in report.items() if k!='each_pair'},sort_keys=True), flush=True)
    dump_atomic(out/'outcome_report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('out/biology_operational_distinction_v1'))
    parser.add_argument('--cache', type=Path, default=Path('data/biology_operational_distinction_v1'))
    parser.add_argument('--cdt-fixture', type=Path, help='Local fixture for parser testing ONLY; no scientific evaluation')
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    if args.cdt_fixture:
        mat, queries, cols = parse_cdt(args.cdt_fixture)
        print('PARSER_FIXTURE_ONLY',mat.shape,queries[:2],cols[:2])
        return
    path, prov = acquire(args.cache)
    mat, queries, cols = parse_cdt(path)
    prov.update({'matrix_shape': list(mat.shape), 'finite_cells': int(np.isfinite(mat).sum()),
                 'matrix_parser': 'CDT header line 1, metadata 5 lines, all dma column names'})
    dump_atomic(args.output/'provenance.json',prov)
    seal, candidates = split_and_predict(mat,queries,cols,args.output)
    report = audit_predictions(seal,mat,candidates,args.output)
    assert report['predictions_sha256']==sha(args.output/'sealed_predictions.json')
    print('BIOLOGY_OPERATIONAL_DISTINCTION_V1_EXECUTED')

if __name__ == '__main__':
    main()