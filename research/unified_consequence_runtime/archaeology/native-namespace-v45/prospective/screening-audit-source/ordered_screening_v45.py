"""Pinned original once-only ordered controller with V45 transport inputs.

Preparing/importing this module performs no query or screening execution.
Actual execution belongs to the separately designated independent screener.
"""
import hashlib
import os
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
PIN='27a5d944c43e9c28836c53018ba11745b899871abbb14f674c89a8826de7cd3f'


def prepare_driver_source():
    path=HERE/'original_run_ordered_screening.py';raw=path.read_bytes()
    if path.is_symlink() or hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('original ordered process transport differs')
    text=raw.decode()
    substitutions=[
      ("source_commit = '77c2ef539aed252e037c5c0a67dd62816d5306b4'", "source_commit = os.environ['UDM_SCREENING_SOURCE_COMMIT']"),
      ("authority_pin = '8c1ae9852b4cc60fb8773863b790c18b0b9dc4c1733fddb96e4a577e5a0dc0b0'", "authority_pin = os.environ['UDM_SCREENING_AUTHORITY_SHA256']"),
      ("prequery_commit = 'b112b69dcda962c9323cbcd13aefdcd580a5449a'", "prequery_commit = os.environ['UDM_PREQUERY_COMMIT']"),
      ('if len(pool)!=2 or len(requests)!=len(pool):','if not 1<=len(pool)<=9 or len(requests)!=len(pool):'),
      ('externally frozen complete two-case pool required','externally frozen complete ordered bounded pool required'),
      ('research.unified_consequence_runtime.qualify_native_frontier_v44','research.unified_consequence_runtime.qualify_native_frontier_v45'),
      ("'actor_identity':'/root/qualify_native_bootstrap_v44 independent screening executor running the exact frozen q44 admission-only CLI'", "'actor_identity':os.environ['UDM_SCREENING_ACTOR_IDENTITY']"),
    ]
    for before,after in substitutions:
        if text.count(before)!=1:raise ValueError('original process transport binding site differs: '+before)
        text=text.replace(before,after)
    return text.replace('UDM_V44_SCREENING_','UDM_V45_SCREENING_')


def main():
    for key,length in (('UDM_SCREENING_SOURCE_COMMIT',40),('UDM_PREQUERY_COMMIT',40),('UDM_SCREENING_AUTHORITY_SHA256',64)):
        if not re.fullmatch('[0-9a-f]{'+str(length)+'}',os.environ.get(key,'')):
            raise ValueError('independently supplied exact screening input required: '+key)
    if not os.environ.get('UDM_SCREENING_ACTOR_IDENTITY','').strip():
        raise ValueError('actual independent screening actor identity required')
    source=prepare_driver_source()
    exec(compile(source,str(HERE/'ordered_screening_v45.py')+':original-transport','exec'),
         {'__name__':'__udm_v45_independent_screening_transport__','__file__':str(HERE/'original_run_ordered_screening.py')})


if __name__=='__main__':main()
