"""An unchanged original entrypoint must defeat a forged derived license.

--source replays the exact initially executed validator bytes for the retained
RED evidence. Default execution checks the current fixed validator.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = HERE/'prepare_profile.py'


class RawEntrypointAuthority(unittest.TestCase):
    def test_derived_license_cannot_override_original_entrypoint_bytes(self):
        module = types.ModuleType('profile_raw_evidence_candidate')
        module.__file__ = str(HERE/'prepare_profile.py')
        exec(compile(SOURCE.read_bytes(), module.__file__, 'exec'), module.__dict__)
        catalog = json.loads((HERE.parent/'ENVIRONMENT_CATALOG.json').read_bytes())
        metadata = json.loads((HERE.parent/'PACKAGE_METADATA.json').read_bytes())
        # Keep raw original entry_points.txt and its SHA unchanged, but forge
        # both derived metadata and the catalog policy so copied fields agree.
        metadata['packages']['pytest-cov==6.3.0']['entry_points']['groups']['pytest11']['pytest_cov'] = 'pytest_cov'
        catalog['profiles'][1]['plugins'][-1]['module'] = 'pytest_cov'
        with tempfile.TemporaryDirectory(prefix='v41-raw-entrypoint-') as temporary:
            root = Path(temporary); (root/'bootstrap').mkdir()
            shutil.copytree(HERE/'metadata-evidence', root/'bootstrap/metadata-evidence')
            raw = (json.dumps(metadata, indent=2, sort_keys=True)+'\n').encode()
            (root/'PACKAGE_METADATA.json').write_bytes(raw)
            catalog['package_metadata_sha256'] = hashlib.sha256(raw).hexdigest()
            candidate = root/'ENVIRONMENT_CATALOG.json'
            candidate.write_text(json.dumps(catalog, indent=2, sort_keys=True)+'\n')
            with self.assertRaisesRegex(ValueError, 'UNKNOWN_RAW_ENTRYPOINT_BINDING: pytest-cov==6.3.0'):
                module.validate(candidate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    args = parser.parse_args(); SOURCE = args.source
    unittest.main(argv=['test_profile_raw_evidence'], verbosity=2)
