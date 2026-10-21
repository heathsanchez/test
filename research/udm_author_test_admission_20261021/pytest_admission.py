"""Narrow candidate admission; not a replacement for UDM's source/verifier authority."""
import shlex
from dataclasses import dataclass
@dataclass(frozen=True)
class Admission:
    status:str
    args:tuple[str,...]=()
    reason:str=""
ALLOWED={'-q','-v','-vv','-x','-s','-l','--tb=short','--tb=line','--import-mode=importlib','--import-mode=prepend','--import-mode=append'}
def admit(command,*,authorized_roots,authorized):
    if not authorized:return Admission('UNKNOWN_SOURCE_AUTHORITY',reason='Independent author authorization missing')
    try: words=shlex.split(command,posix=True)
    except ValueError:return Admission('REJECT',reason='Invalid quoting')
    if not words or (words[:3] not in (['python','-m','pytest'],['python3','-m','pytest']) and words[0]!='pytest'):
        return Admission('REJECT',reason='Unsupported entrypoint')
    args=words[3:] if words[0] in ('python','python3') else words[1:]
    roots=[]
    for a in args:
        if a.startswith('-'):
            if a not in ALLOWED:return Admission('REJECT',reason=f'Unknown option {a}')
        else:
            if a.startswith('/') or '\\' in a or ':' in a or a in ('.','..') or any(p in ('.','..') for p in a.split('/')):
                return Admission('REJECT',reason='Unsafe path')
            roots.append(a)
    if not roots or any(r not in authorized_roots for r in roots):
        return Admission('REJECT',reason='Non-authorized test root')
    return Admission('ADMIT_SCOPED',tuple(args))
