"""Replay authenticated qualified V54 state; no acquisition or discovery reruns.

The caller authenticates the upstream workflow/artifact digest. Retained native
interpreter paths remain exact bindings; external relocation is UNKNOWN.
Run with the UDM interpreter containing the native E/D evaluator; the separate
--native-python interpreter runs the V54 native tests.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .consequence_selection import _state_digest
from .developmental_machine import Machine, digest
from .qualify_v54_machine import _subprocess_mode
from .v54_source import SOURCE_COMMIT, SOURCE_SHA256


def qualify(args):
    root, out = args.qualified_root.resolve(), args.out.resolve()
    qualified = root/'qualification/v54'
    original_state = (qualified/'state').resolve()
    if any(out == source or source in out.parents or out in source.parents for source in (root, qualified.resolve(), original_state)):
        raise ValueError('replay output must be separate and outside archived input state')
    worlds = args.worlds.resolve()
    if any(worlds == source or source in worlds.parents or worlds in source.parents for source in (root, qualified.resolve())):
        raise ValueError('native worlds must be separate from archived evidence')
    out.mkdir(parents=True, exist_ok=False)
    report = {'schema': 'udm.v54.qualified-state-replay.v1', 'status': 'FAILED_OR_UNKNOWN',
        'qualified_root': str(root), 'acquisition_rerun': False, 'fresh_discovery_claim': False,
        'external_relocation': 'UNKNOWN', 'upstream_artifact_authentication': 'CALLER_RESPONSIBILITY',
        'source_commit': SOURCE_COMMIT, 'source_sha256': SOURCE_SHA256,
        'runtime_sha256': digest(Path(__file__).with_name('v54_runtime.py').read_bytes())}
    try:
        raw = (qualified/'RESULT.json').read_bytes()
        prior = json.loads(raw)
        report['original_result_sha256'] = digest(raw)
        if (prior.get('schema') != 'udm.v54.native-developmental-qualification.v1' or
                prior.get('status') != 'WARRANTED_BOUNDED_V54_TWO_GENERATION_EXTENSION'):
            raise ValueError('original V54 result is not qualified')
        required = set(('restore_qualified_base original_O1_acquisition native_target_and_O1_admission '
            'protected_original_ED_before original_complete_cold_search UDM_O1_reuse_and_original_O2_construction '
            'fresh_equal_information_executable_ledger_baseline selective_exact_O1_ancestor_withdrawal '
            'independent_native_restoration_new_lineage separate_process_cold_restart_native_and_ED').split())
        stages = prior.get('stages', {})
        if not required <= stages.keys() or any(stage.get('status') != 'PASS' for stage in stages.values()):
            raise ValueError('original qualification stages are incomplete or failed')
        baseline = prior.get('baseline', {})
        if baseline.get('status') != 'PASS' or baseline.get('equal_information') is not True or baseline.get('comparison') != 'TIE_ON_NATIVE_CAPABILITY_AND_SEARCH_HORIZON':
            raise ValueError('original equal-information baseline is not a verified tie')
        archived_restart = prior.get('restart', {})
        if archived_restart.get('status') != 'PASS' or archived_restart != json.loads((qualified/'cold-replay.json').read_text()):
            raise ValueError('original restart is not a matching PASS')
        report['unchanged_sources'] = {}
        for filename in ('v54_source.py', 'v54_verify.py', 'qualify_v54_machine.py'):
            current = Path(__file__).with_name(filename).read_bytes()
            if current != (root/'research/unified_consequence_runtime'/filename).read_bytes():
                raise ValueError('archived/current source bytes differ: '+filename)
            report['unchanged_sources'][filename] = digest(current)
        if prior['restoration']['independent_receipt']['native_python'] != str(args.native_python.absolute()):
            raise ValueError('retained native interpreter path differs; external relocation UNKNOWN')
        if digest((original_state/'metatron-ledger.jsonl').read_bytes()) != prior['retention']['final_ledger_sha256']:
            raise ValueError('archived final ledger differs from qualified result')
        report['input_state_before'] = _state_digest(original_state)
        shutil.copytree(original_state, out/'state')
        machine = Machine(args.components, out/'state', args.evaluator, args.config)
        spec = json.loads((qualified/'replay-spec.json').read_text())
        if (prior['restoration']['status'] != 'PASS' or spec['operators'] != prior['restoration']['operators'] or
                len(spec['operators']) != 2 or set(spec['protected_capabilities']) != {'grouping', 'stars'} or
                spec['protected_capabilities'] != prior['base']['protected_capabilities'] or
                spec['withdrawn'] != [prior['withdrawal']['exact_ancestor'], prior['O1_capability'], prior['warm']['O2_capability']]):
            raise ValueError('archived executable replay bindings differ from restoration')
        original_ids = set(machine.mt.ids(machine.log))
        if not set(spec['historical_ids']) <= original_ids:
            raise ValueError('archived historical records are missing')
        protected = set(spec['operators']) | set(spec['protected_capabilities'].values())
        if not protected <= set(machine.mt.live_ids(machine.log)):
            raise ValueError('qualified V54 or E/D routes are inactive')
        parent = machine.append('independent_replay_control', {'scope': 'unrelated control withdrawal'})
        child = machine.append('independent_replay_child', {}, (parent,))
        machine.flush()
        before = set(machine.mt.live_ids(machine.log))
        machine.append('revoke', {'target': parent, 'reason': 'independent replay control withdrawal'})
        machine.flush()
        removed = before - set(machine.mt.live_ids(machine.log))
        if removed != {parent, child} or not protected <= machine.flash_live_ids():
            raise ValueError('independent control withdrawal changed qualified routes')
        report['independent_control'] = {'parent': parent, 'child': child, 'removed_count': len(removed)}
        spec.update({name: str(getattr(args, name).resolve()) for name in ('source', 'worlds', 'components', 'evaluator', 'config')})
        spec.update(state=str(out/'state'), assets=str(args.config.resolve().parent),
            native_python=str(args.native_python.absolute()), historical_ids=sorted(original_ids))
        (out/'replay-spec.json').write_text(json.dumps(spec, indent=2)+'\n')
        replay = _subprocess_mode(Path(sys.executable), '--replay', out/'replay-spec.json', out/'cold-replay.json', timeout=1200)
        receipt = replay.get('independent_receipt', {})
        if (replay.get('status') != 'PASS' or replay.get('native', {}).get('passed') is not True or
                replay.get('history_retained') is not True or replay.get('withdrawn_generations_inactive') is not True or
                replay.get('acquisition_rerun') is not False or receipt.get('status') != 'accepted' or
                receipt.get('evaluated') is not True or not receipt.get('gates') or not all(receipt['gates'].values())):
            raise ValueError('fresh native replay, independent proof or history checks failed')
        hashes = lambda result: {task: value['response_sha256'] for task, value in result['protected'].items()}
        if set(hashes(replay)) != {'62', '64', '65', '168', '169', '172'} or hashes(replay) != hashes(archived_restart):
            raise ValueError('fresh native E/D response hashes differ from original restart')
        if replay['native']['source_sha256'] != archived_restart['native']['source_sha256']:
            raise ValueError('fresh native final source differs from original restart')
        final = Machine(args.components, out/'state', args.evaluator, args.config)
        if (not original_ids <= set(final.mt.ids(final.log)) or not protected <= final.flash_live_ids() or
                set(spec['withdrawn']) & (set(final.mt.live_ids(final.log)) | final.flash_live_ids())):
            raise ValueError('fresh replay lost original history or qualified routes')
        report.update(replay=replay, historical_records_retained=len(original_ids),
            final_ledger_sha256=digest((out/'state/metatron-ledger.jsonl').read_bytes()))
        report['input_state_after'] = _state_digest(original_state)
        if report['input_state_after'] != report['input_state_before']:
            raise ValueError('archived input state bytes changed')
        report['status'] = 'REPLAY_VERIFIED_QUALIFIED_V54_STATE'
        return report
    except BaseException as error:
        report.update(reason=str(error), error_type=type(error).__name__)
        if 'input_state_before' in report:
            report['input_state_after'] = _state_digest(original_state)
        if isinstance(error, subprocess.TimeoutExpired):
            output = ''.join(part.decode(errors='replace') if isinstance(part, bytes) else part or ''
                for part in (error.stdout, error.stderr))
            (out/'process-replay.log').write_text(output)
        raise
    finally:
        (out/'RESULT.json').write_text(json.dumps(report, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('qualified-root', 'out', 'source', 'worlds', 'components', 'evaluator', 'config', 'native-python'):
        parser.add_argument('--'+name, type=Path, required=True)
    result = qualify(parser.parse_args())
    print(json.dumps({'status': result['status'], 'acquisition_rerun': False}))


if __name__ == '__main__':
    main()
