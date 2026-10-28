"""Versioned closure of the original independent V44 screening finalizer."""
from pathlib import Path
import hashlib
import importlib.util
from types import CodeType,FunctionType

HERE=Path(__file__).resolve().parent
_path=Path('/workspace/qualification/native-bootstrap-v44-screening-audit-preparation/finalize_audit_v44.py')
_sha='73a2e3e82e792ac7786fe31b69b9e68d08075160191b7ea66d905ae162fded99'
if hashlib.sha256(_path.read_bytes()).hexdigest()!=_sha:
    raise ValueError('original screening finalizer source differs')
_spec=importlib.util.spec_from_file_location('_v45_original_screening_finalizer',_path)
_original=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_original)
_replacements={'audit_retained_v44.py':'audit_retained_v45.py',
 'UDM_V44_INDEPENDENT_ADMISSION_ONLY_SCREENING_AUDIT_V1':'UDM_V45_INDEPENDENT_ADMISSION_ONLY_SCREENING_AUDIT_V1',
 '/root/integrate_bootstrap_runtime':'/root/v45_science_readiness'}


def _code(code):
    return code.replace(co_consts=tuple(_code(v) if isinstance(v,CodeType) else
      _replacements.get(v,v) if isinstance(v,str) else v for v in code.co_consts))


_namespace=dict(vars(_original),HERE=HERE)
main=FunctionType(_code(_original.main.__code__),_namespace,'main',_original.main.__defaults__,_original.main.__closure__)
if __name__=='__main__':main()
