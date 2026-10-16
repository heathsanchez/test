"""Pre-target contracts for the generic prospective experiment's data boundary."""
import unittest
import base64
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from . import decisive_native as native
from . import generic_native_verify as verifier


def native_fixture():
    """Explicit numerical/raw fixture; never independent scientific evidence."""
    manifest=[{'path':'pkg.py','sha256':verifier.sha256(b'x=1\n'),'mode':'100644','blob':'a'*40}]
    environment={'pytest_import':{'path':'fixture/pytest.py','sha256':'b'*64}}
    contract={'repository':'fixture/source','commit':'a'*40,'git_tree':'c'*40,
        'tracked_tree_sha256':verifier.fingerprint(manifest),'file_count':1,
        'protocol_binding':'d'*64,'environment_sha256':verifier.fingerprint(environment)}
    candidate={'replacements':[]};xml=b'<testsuite><testcase name="fixture"/></testsuite>'
    receipt={'status':'PASS_NATIVE','exit_code':0,'repository':contract['repository'],'commit':contract['commit'],
        'source':{k:contract[k] for k in ('git_tree','tracked_tree_sha256','file_count')},
        'runner_sha256':verifier.sha256(Path(verifier.__file__).read_bytes()),
        'contract_sha256':verifier.fingerprint(contract),'candidate_sha256':verifier.fingerprint(candidate),
        'protocol_binding':contract['protocol_binding'],'environment_sha256':contract['environment_sha256'],
        'environment':environment,'pytest_import':environment['pytest_import'],
        'import_manifest':[{'path':'pkg.py','sha256':manifest[0]['sha256']}],
        'junit':dict(tests=1,passed=1,failures=0,errors=0,skipped=0),
        'junit_sha256':verifier.sha256(xml),'stdout_sha256':verifier.sha256(b''),'stderr_sha256':verifier.sha256(b''),
        'costs':{'native_calls':1}}
    files={'receipt.json':json.dumps(receipt).encode(),'tracked-source-manifest.json':json.dumps(manifest).encode(),
        'native.xml':xml,'stdout.log':b'','stderr.log':b''}
    packet={'schema':'UDM_DECISIVE_NATIVE_PACKET_V1','files':{k:base64.b64encode(v).decode() for k,v in files.items()}}
    record={'receipt':receipt,'contract':contract,'candidate':candidate,'packet':'packet','evidence_dir':'NOT_AUTHORITY'}
    return record,packet


class DecisiveNativeContracts(unittest.TestCase):
    def test_native_suite_authority_and_required_execution_are_not_replayable(self):
        record,packet=native_fixture()
        authority={'required_test_nodes':['tests/test_native.py::test_new'],'baseline_commit':'0'*40,
            'test_source_sha256':{'tests/test_native.py':'f'*64}}
        record['native_suite_authority']=authority
        receipt=record['receipt'];receipt.update(native_suite_authority_sha256=verifier.fingerprint(authority),
            required_test_nodes=authority['required_test_nodes'],executed_test_nodes=authority['required_test_nodes'],
            deselected_test_nodes=[],executed_test_reports=[{'nodeid':authority['required_test_nodes'][0],'outcome':'passed'}])
        def seal():packet['files']['receipt.json']=base64.b64encode(json.dumps(receipt).encode()).decode()
        seal();machine=SimpleNamespace(get=lambda key:packet)
        with patch.object(verifier,'validate_native_suite_authority',side_effect=lambda contract,auth:verifier.fingerprint(auth)):
            self.assertEqual(native.checked_native_receipt(record,machine),receipt)
            for field,value in (('native_suite_authority_sha256','f'*64),
                                ('required_test_nodes',['tests/test_native.py::test_old']),
                                ('deselected_test_nodes',authority['required_test_nodes'])):
                before=copy.deepcopy(receipt);receipt[field]=value;seal()
                with self.assertRaises(ValueError):native.checked_native_receipt(record,machine)
                receipt.clear();receipt.update(before);seal()
            receipt.update(status='FAIL_NATIVE',exit_code=1,junit=dict(tests=1,passed=0,failures=1,errors=0,skipped=0),
                executed_test_reports=[{'nodeid':authority['required_test_nodes'][0],'outcome':'failed'}])
            xml=b'<testsuite><testcase name="fixture"><failure/></testcase></testsuite>'
            packet['files']['native.xml']=base64.b64encode(xml).decode();receipt['junit_sha256']=verifier.sha256(xml);seal()
            self.assertEqual(native.checked_native_receipt(record,machine)['status'],'FAIL_NATIVE')

    def test_native_authority_uses_cas_packet_not_mutable_evidence_path(self):
        record,packet=native_fixture();machine=SimpleNamespace(get=lambda key:packet)
        self.assertEqual(native.checked_native_receipt(record,machine),record['receipt'])
        for name in ('native.xml','stdout.log','stderr.log','tracked-source-manifest.json','receipt.json'):
            forged=copy.deepcopy(packet);del forged['files'][name]
            with self.assertRaises((ValueError,KeyError)):
                native.checked_native_receipt(record,SimpleNamespace(get=lambda key:forged))

    def test_mutated_receipt_environment_import_or_native_xml_is_refused(self):
        record,packet=native_fixture()
        for field,value in (('repository','fixture/another'),('environment',{}),
                            ('import_manifest',[{'path':'pkg.py','sha256':'f'*64}])):
            forged=copy.deepcopy(record);forged['receipt'][field]=value
            altered=copy.deepcopy(packet);altered['files']['receipt.json']=base64.b64encode(json.dumps(forged['receipt']).encode()).decode()
            with self.assertRaises(ValueError):
                native.checked_native_receipt(forged,SimpleNamespace(get=lambda key:altered))
        forged=copy.deepcopy(packet);forged['files']['native.xml']=base64.b64encode(b'<testsuite/>').decode()
        with self.assertRaises(ValueError):native.checked_native_receipt(record,SimpleNamespace(get=lambda key:forged))

    def test_fail_label_cannot_license_development_without_verified_failure(self):
        record,packet=native_fixture();record['receipt']['status']='FAIL_NATIVE'
        packet['files']['receipt.json']=base64.b64encode(json.dumps(record['receipt']).encode()).decode()
        with self.assertRaises(ValueError):native.checked_native_receipt(record,SimpleNamespace(get=lambda key:packet))

    def test_profiles_refuse_wrong_task_wrong_policy_order_and_unretained_packet(self):
        record,packet=native_fixture();ident=verifier.fingerprint(record['candidate'])
        metadata={'selected':[{'repo':'fixture/source'}]}
        scope={'protocol_binding':'d'*64,'candidate_catalog_sha256':'e'*64,
            'source_binding':native.digest(native.canonical(native.task_roles(metadata['selected'])).encode()),
            'budget':1,'contexts':{'fixture/source':'context'},'receipt_objects':['context','baseline','packet','record']}
        context={'contract':record['contract'],'orders':{'POLICY':[ident]},'baseline_record':'baseline','catalog_spec':{'cap':64}}
        report={'candidate':'POLICY','future':'fixture/source','scope':scope,'order':[ident],'attempts':['record']}
        values={'packet':packet,'record':record,'baseline':record,'report':report,'context':context}
        machine=SimpleNamespace(log=[SimpleNamespace(id='evidence',kind='native_acquisition_profile',payload={'report':'report'})],
            get=lambda key:values[key],costs=[])
        with tempfile.TemporaryDirectory(prefix='decisive-fixture-metadata-') as folder:
            metadata_path=Path(folder)/'metadata.json';metadata_path.write_text(json.dumps(metadata))
            protocol_path=Path(folder)/'protocol.json';protocol_path.write_text(json.dumps({'search_budget':1,'candidate_cap_per_file':64}))
            scope['protocol_sha256']=native.digest(protocol_path.read_bytes())
            with patch.object(native,'METADATA_PATH',metadata_path),patch.object(native,'PROTOCOL_PATH',protocol_path),patch.object(native,'_checked_context',return_value=context):
                self.assertEqual(native.reconstruct_profiles(machine,('POLICY',),('fixture/source',),('evidence',))['profiles']['POLICY']['fixture/source'],[0,1])
                for mutate in ('task','order','packet','horizon'):
                    old=copy.deepcopy(values)
                    if mutate=='task':record['contract']={**record['contract'],'repository':'fixture/other'}
                    if mutate=='order':report['order']=['not-the-program']
                    if mutate=='packet':scope['receipt_objects'].remove('packet')
                    if mutate=='horizon':report['attempts']=[]
                    with self.assertRaises(ValueError):native.reconstruct_profiles(machine,('POLICY',),('fixture/source',),('evidence',))
                    record.clear();record.update(old['record']);report.clear();report.update(old['report']);scope.clear();scope.update(old['report']['scope']);report['scope']=scope

    def test_only_original_author_test_files_can_be_transported(self):
        from .decisive_native import overlay_author_tests
        base = {'pkg/code.py': b'answer=1\n', 'tests/test_code.py': b'assert False\n'}
        files = overlay_author_tests(base, {'tests/test_code.py': b'assert True\n'})
        self.assertEqual(files['pkg/code.py'], base['pkg/code.py'])
        self.assertEqual(files['tests/test_code.py'], b'assert True\n')
        with self.assertRaises(ValueError):
            overlay_author_tests(base, {'pkg/code.py': b'answer=2\n'})

    def test_changed_line_measure_ignores_unparse_formatting(self):
        from .decisive_native import changed_lines
        old = 'def f(x):\n    # source provenance retained\n    return x + 1\n'
        self.assertEqual(changed_lines(old, 'def f(x):\n    return x + 1'), ())
        self.assertEqual(changed_lines(old, 'def f(x):\n    return x'), (3,))

    def test_native_unknown_cannot_be_scored_as_a_success(self):
        from .decisive_native import passed
        good = {'status':'PASS_NATIVE','exit_code':0,'junit':
                {'tests':2,'passed':2,'failures':0,'errors':0,'skipped':0}}
        self.assertTrue(passed(good))
        for key, value in [('status','UNKNOWN_NATIVE_ERROR'), ('exit_code',1)]:
            self.assertFalse(passed(dict(good, **{key:value})))
        self.assertFalse(passed(dict(good, junit=dict(good['junit'], skipped=1))))
        self.assertFalse(passed(dict(good, junit=dict(good['junit'], tests=0, passed=0))))

    def test_metadata_shortfall_is_not_filled_after_outcomes(self):
        from .decisive_native import task_roles
        rows = [{'repo':str(i), 'role':'TRAINING'} for i in range(3)]
        self.assertEqual([x['role'] for x in task_roles(rows)],
                         ['TRAINING','PROTECTED_FUTURE_1','PROTECTED_FUTURE_2'])
        self.assertTrue(all(x['role']=='TRAINING' for x in rows))

    def test_original_policy_grammar_is_source_authenticated(self):
        from .decisive_native import policy_language
        policies, key, pin = policy_language(Path(os.environ.get('UDM_SOURCE_REPOS','/workspace/repos'))/'msi')
        self.assertEqual(len(policies), 36)
        self.assertEqual(key(((1,'K'),(-1,'c')), {'K':4,'c':2,'v':1}), (4,-2))
        self.assertEqual(pin['commit'], '56cfd7b523e3592cae4eafa5468f437ccb94dbe9')


if __name__ == '__main__':
    unittest.main()
