"""Close only the new independent amended admission dossier; no native runs."""
from pathlib import Path
import hashlib
import importlib.util
import inspect
from types import CodeType,FunctionType

HERE=Path(__file__).resolve().parent
_path=Path('/workspace/qualification/native-namespace-v45-screening-audit-preparation/finalize_audit_v45.py')
_sha='83f6f3fe10e9824825412aff43c798e68eade84f9d462e478468a0a80c81e294'
if _path.is_symlink() or hashlib.sha256(_path.read_bytes()).hexdigest()!=_sha:
    raise ValueError('original frozen V45 screening finalizer differs')
_spec=importlib.util.spec_from_file_location('_request_v1_original_finalizer',_path)
_original=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_original)


def prepare_finalizer():
    source=inspect.getsource(_original._original.main)
    before="'costs':value['costs'],'dossier':"
    after="'costs':value['costs'],\n        'external_screening_budget':value['external_screening_budget'],\n        'original_metadata_origin':{k:value['original_metadata_reconstruction'][k] for k in ('original_prequery_commit','original_screening_commit','metadata_summary','exposure_reconstruction','original_metadata_costs')},\n        'lifecycle_cost_boundary':'Original metadata outer and prior screening costs plus all newly measured intervals are common inputs to every arm; overlapping inner intervals are not added twice. Unknown engineering/model/final-receipt costs remain UNKNOWN, so this audit grants no comparative advantage.',\n        'dossier':"
    if source.count(before)!=1:raise ValueError('original finalizer cost/source binding site differs')
    source=source.replace(before,after)
    namespace=dict(vars(_original._original),HERE=HERE)
    exec(compile(source,str(HERE/'finalize_audit_request_v1.py')+':original-finalizer','exec'),namespace)
    replacements={'audit_retained_v44.py':'audit_retained_request_v1.py',
      'UDM_V44_INDEPENDENT_ADMISSION_ONLY_SCREENING_AUDIT_V1':'UDM_REQUEST_ACTIVATION_V1_INDEPENDENT_ADMISSION_ONLY_SCREENING_AUDIT',
      '/root/integrate_bootstrap_runtime':'/root/v45_science_readiness'}
    def transport(code):
        return code.replace(co_consts=tuple(transport(v) if isinstance(v,CodeType) else
            replacements.get(v,v) if isinstance(v,str) else v for v in code.co_consts))
    f=namespace['main']
    return FunctionType(transport(f.__code__),namespace,'main',f.__defaults__,f.__closure__)


if __name__=='__main__':prepare_finalizer()()
