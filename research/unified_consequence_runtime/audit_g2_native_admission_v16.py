"""Independent structural audit of V16 admission packets, NOT proof of full Git/runtime replay.

Accepts a CI evidence directory or the downloaded Actions ZIP. Never re-executes
foreign code. An original trusted Git checkout is still needed to verify source
OIDs and original assertion semantics beyond the authenticated packet.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

SCHEMA='UDM_V16_INDEPENDENT_ADMISSION_PACKET_AUDIT'
HEX40=re.compile(r'[0-9a-f]{40}\Z')
HEX64=re.compile(r'[0-9a-f]{64}\Z')
REQUIRED=('admission.json','pin.json','events.json','native.xml','native.stdout','native.stderr')


def digest(value):
    return hashlib.sha256(value).hexdigest()


def audit(path):
    path=Path(path)
    if path.is_dir():
        if any((path/name).is_symlink() or not (path/name).is_file() for name in REQUIRED):
            raise ValueError('UNKNOWN_MISSING_OR_REDIRECTED_PACKET')
        packet={name:(path/name).read_bytes() for name in REQUIRED}
    else:
        with zipfile.ZipFile(path) as z:
            if len(z.namelist())!=len(set(z.namelist())) or any(name not in z.namelist() for name in REQUIRED):
                raise ValueError('UNKNOWN_ZIP_PACKET_MANIFEST')
            packet={name:z.read(name) for name in REQUIRED}
    get=lambda name: json.loads(packet[name])
    result,pin,events=get('admission.json'),get('pin.json'),get('events.json')
    if (result.get('schema')!='UDM_NATIVE_ADMISSION_V16' or result.get('scope')!='CALIBRATION_ONLY'
            or any(result.get(k)!='UNKNOWN' for k in ('G2','G3','G4'))):
        raise ValueError('UNKNOWN_SCIENTIFIC_SCOPE')
    if result.get('status') not in ('ADMITTED_NATIVE_PASS_CALIBRATION',
                                    'ADMITTED_NATIVE_FAIL_PROTECTED_CALIBRATION'):
        raise ValueError('UNKNOWN_NATIVE_ADMISSION_STATUS')
    if (pin.get('scope')!='CALIBRATION_ONLY' or result.get('source_sha')!=pin.get('sha')
            or not isinstance(pin.get('sha'),str) or not HEX40.fullmatch(pin['sha'])
            or not isinstance(pin.get('requirements_blob'),str)
            or not HEX40.fullmatch(pin['requirements_blob'])
            or result.get('pin_sha256')!=digest(packet['pin.json'])):
        raise ValueError('UNKNOWN_SOURCE_TEST_PIN')
    source=result.get('source_identity',{})
    entries=source.get('entries',[])
    if (not isinstance(entries,list) or not entries or source.get('files')!=len(entries)
            or len({row['path'] for row in entries})!=len(entries)
            or any(row.get('mode') not in ('100644','100755')
                   or not HEX40.fullmatch(row.get('oid','')) or not HEX64.fullmatch(row.get('sha256',''))
                   for row in entries)
            or source.get('manifest_sha256')!=digest(json.dumps(entries,sort_keys=True).encode())):
        raise ValueError('UNKNOWN_SOURCE_MANIFEST_INCONSISTENT')
    selected=events.get('collected',[]);calls=events.get('calls',[])
    observed=result.get('observed_call_nodes',[])
    if (not isinstance(selected,list) or not selected or events.get('calls')!=observed
            or [c.get('nodeid') for c in calls]!=selected
            or any(c.get('xfail') or c.get('outcome') not in ('passed','failed') for c in calls)
            or events.get('deselected') or events.get('collection_errors')
            or result.get('deselected') or result.get('collection_errors')
            or result.get('native_calls')!=1
            or result.get('returncode')!=events.get('returncode')):
        raise ValueError('UNKNOWN_NATIVE_CALL_PACKET')
    cases=list(ET.fromstring(packet['native.xml']).iter('testcase'))
    counts={'cases':len(cases),'failed':sum(bool(list(c.iter('failure'))) for c in cases),
            'errors':sum(bool(list(c.iter('error'))) for c in cases),
            'skipped':sum(bool(list(c.iter('skipped'))) for c in cases)}
    failed=[c['nodeid'] for c in calls if c['outcome']=='failed']
    required=pin.get('required_test_prefixes',[])
    matches=lambda node,prefix: node==prefix or node.startswith(prefix+'[')
    if (counts!=result.get('counts') or counts['cases']!=len(calls)
            or counts['errors'] or counts['skipped'] or counts['failed']!=len(failed)
            or not isinstance(required,list) or not required
            or any(not any(matches(node,p) for node in selected) for p in required)):
        raise ValueError('UNKNOWN_JUNIT_OR_PROTECTED_SCOPE')
    if result['status']=='ADMITTED_NATIVE_PASS_CALIBRATION':
        if failed or result.get('returncode')!=0:
            raise ValueError('UNKNOWN_FALSE_POSITIVE_NATIVE_STATUS')
    elif (not failed or result.get('returncode')!=1 or any(
          not any(matches(node,p) for p in required) for node in failed)):
        raise ValueError('UNKNOWN_FALSE_PROTECTED_FAILURE_STATUS')
    return {'schema':SCHEMA,'status':'PASS_PACKET_CONSISTENCY_CALIBRATION_ONLY',
            'G2':'UNKNOWN','source_sha':pin['sha'],'manifest_sha256':source['manifest_sha256'],
            'native_calls':1,'actual_collected':len(selected),'actual_call_reports':len(calls),
            'junit':counts,'required':required,
            'packet_sha256':{name:digest(packet[name]) for name in REQUIRED},
            'limitation':'Git blob bytes, original assertion truth and hostile-source containment NOT independently reconstructed from this packet'}


if __name__=='__main__':
    receipt=audit(sys.argv[1])
    print(json.dumps(receipt,sort_keys=True,indent=2))
    if len(sys.argv)>2:
        target=Path(sys.argv[2])
        if target.exists():raise SystemExit('Refuse overwrite prior independent audit receipt')
        target.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
