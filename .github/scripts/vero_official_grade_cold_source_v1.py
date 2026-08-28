from pathlib import Path
import json
from vero.generation.benchmark import Benchmark
from vero.generation.extractor import extract, write_artifact
from vero.evaluation.runner import run_evaluation

SOURCE = Path('vero/benchmarks/galoistools').resolve()
# Locate the certified cold source tree inside the uploaded evidence artifact.
candidates = [p for p in Path('coldcert').rglob('Galoistools') if p.is_dir()]
roots = []
for g in candidates:
    root = g.parent
    if (root/'lakefile.toml').exists() or (root/'lakefile.lean').exists():
        roots.append(root)
if not roots:
    raise SystemExit('No certified Galoistools source root found in coldcert artifact')
PROMOTED = sorted(set(roots), key=lambda p: len(str(p)))[0].resolve()
OUT = Path('official_grade_cold_source_v1').resolve()
OUT.mkdir(parents=True, exist_ok=True)

bench = Benchmark(SOURCE)
artifact = extract(PROMOTED, bench, mode='codeproof')
write_artifact(artifact, OUT/'artifact.json')
run_evaluation(
    benchmark_dir=SOURCE,
    artifact=artifact,
    mode='codeproof',
    eval_sandbox_dir=OUT/'sandbox',
    report_dir=OUT/'report',
    lake_timeout=1200,
)
report = json.loads((OUT/'report'/'report.json').read_text())
summary = report['summary']
build = report.get('build', {})
marker = {
  'source_root': str(PROMOTED),
  'build_ok': build.get('ok', report.get('build_ok', False)),
  'impl_broken': report.get('impl_broken', build.get('impl_broken', False)),
  'total_specs': summary['total_specs'],
  'passed_specs': summary['passed_specs'],
  'failed_specs': summary['failed_specs'],
  'unfilled_specs': summary['unfilled_specs'],
  'overfilled_specs': summary['overfilled_specs'],
  'unpaired_sat_specs': summary['unpaired_sat_specs'],
}
print('VERO_OFFICIAL_GRADE_COLD_SOURCE_V1', json.dumps(marker, sort_keys=True))
statuses = {}
for module in report.get('modules', []):
    for spec in module.get('specs', []):
        st = spec.get('status','unknown')
        statuses[st] = statuses.get(st,0)+1
        if st != 'passed':
            print('VERO_COLD_RESIDUAL', module.get('module'), spec.get('spec'), st, spec.get('message',''))
print('VERO_COLD_STATUS_CENSUS', json.dumps(statuses, sort_keys=True))
raise SystemExit(0 if marker['passed_specs']==48 and marker['failed_specs']==0 else 1)
