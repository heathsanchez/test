"""Exact generic byte/JSON helpers reused from prior V41 read-only audit."""
import hashlib,json,math
from pathlib import PurePosixPath

def _sha(raw):
    return hashlib.sha256(raw).hexdigest()

def _fp(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())

def _json(raw, label):
    def pairs(rows):
        out = {}
        for key, value in rows:
            if key in out:
                raise ValueError('duplicate JSON key in ' + label + ': ' + key)
            out[key] = value
        return out
    def invalid(value):
        raise ValueError('nonfinite JSON number in ' + label + ': ' + value)
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('malformed JSON: ' + label) from error

def _raw(mapping, name):
    path = PurePosixPath(name)
    if (path.is_absolute() or '..' in path.parts or str(path) != name or '\\' in name
            or name not in mapping or not isinstance(mapping[name], bytes)):
        raise ValueError('missing/invalid retained byte member: ' + name)
    return mapping[name]

def _read(mapping, name):
    return _json(_raw(mapping, name), name)

def _finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0
