from pathlib import Path
import json

from vero.generation.benchmark import Benchmark
from vero.generation.extractor import extract, write_artifact
from vero.evaluation.runner import run_evaluation

SOURCE = Path('vero/benchmarks/galoistools').resolve()
PROMOTED = Path('decontaminated/full48_decontaminated_v1').resolve()
OUT = Path('official_grade_full48_v1').resolve()
OUT.mkdir(parents=True, exist_ok=True)

bench = Benchmark(SOURCE)
artifact = extract(PROMOTED, bench, mode='codeproof')
write_artifact(artifact, OUT / 'artifact.json')

result = run_evaluation(
    benchmark_dir=SOURCE,
    artifact=artifact,
    mode='codeproof',
    eval_sandbox_dir=OUT / 'sandbox',
    report_dir=OUT / 'report',
    lake_timeout=1200,
)

report = json.loads((OUT / 'report' / 'report.json').read_text())
summary = report['summary']
marker = {
    'build_ok': report['build_ok'],
    'impl_broken': report.get('impl_broken', False),
    'total_specs': summary['total_specs'],
    'passed_specs': summary['passed_specs'],
    'unfilled_specs': summary['unfilled_specs'],
    'overfilled_specs': summary['overfilled_specs'],
    'unpaired_sat_specs': summary['unpaired_sat_specs'],
    'failed_specs': summary['failed_specs'],
    'joint_status': summary.get('joint_status'),
}
print('VERO_OFFICIAL_GRADE_FULL48_V1', json.dumps(marker, sort_keys=True))

ok = (
    marker['build_ok']
    and not marker['impl_broken']
    and marker['total_specs'] == 48
    and marker['passed_specs'] == 48
    and marker['unfilled_specs'] == 0
    and marker['overfilled_specs'] == 0
    and marker['unpaired_sat_specs'] == 0
    and marker['failed_specs'] == 0
)
raise SystemExit(0 if ok else 1)
