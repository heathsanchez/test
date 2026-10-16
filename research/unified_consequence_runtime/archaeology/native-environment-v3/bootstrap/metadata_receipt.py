"""Check the frozen package closure without importing project or runtime code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import packaging
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version


def validate(catalog_path):
    catalog_path = Path(catalog_path)
    raw = catalog_path.read_bytes()
    catalog = json.loads(raw)
    if catalog['schema'] != 'UDM_NATIVE_ENVIRONMENT_CATALOG_V3':
        raise ValueError('unexpected catalog schema')
    metadata_path = catalog_path.parent / catalog['package_metadata_file']
    metadata_raw = metadata_path.read_bytes()
    if hashlib.sha256(metadata_raw).hexdigest() != catalog['package_metadata_sha256']:
        raise ValueError('package metadata digest differs from catalog')
    metadata = json.loads(metadata_raw)
    results = []
    for profile in catalog['profiles']:
        pins = {}
        for pin in profile['packages']:
            req = Requirement(pin)
            specs = list(req.specifier)
            if (req.extras or req.marker or req.url or len(specs) != 1
                    or specs[0].operator != '=='):
                raise ValueError('exact ordinary package pin required')
            name = canonicalize_name(req.name)
            if name in pins:
                raise ValueError('duplicate package pin')
            pins[name] = Version(specs[0].version)
        target = Version(profile['python_version'])
        edges = []
        for pin in profile['packages']:
            req = Requirement(pin)
            name = canonicalize_name(req.name)
            evidence = metadata['packages'][pin]
            artifact = profile['package_artifacts'][name]
            wheel = evidence['wheel']
            for key in ('filename', 'url', 'sha256', 'size', 'metadata_sha256'):
                if artifact[key] != wheel[key]:
                    raise ValueError('catalog artifact differs from metadata: ' + pin)
            if evidence['requires_dist'] != profile['package_requirements'][name]:
                raise ValueError('catalog requirements differ from metadata: ' + pin)
            for spec in (evidence.get('requires_python'), wheel.get('requires_python'),
                         wheel.get('metadata_requires_python')):
                if target not in SpecifierSet(spec or ''):
                    raise ValueError('Requires-Python excludes profile: ' + pin)
            if wheel['yanked']:
                raise ValueError('yanked wheel is not bootstrap authority')
            for text in profile['package_requirements'][name]:
                dep = Requirement(text)
                env = {**profile['marker_environment'], 'extra': ''}
                if dep.marker is not None and not dep.marker.evaluate(environment=env):
                    continue
                selected = pins.get(canonicalize_name(dep.name))
                if dep.url or dep.extras or selected is None or selected not in dep.specifier:
                    raise ValueError('active dependency is outside exact closure: ' + text)
                edges.append({'parent': pin, 'requirement': text,
                              'selected_version': str(selected)})
        results.append({'id': profile['id'], 'python_version': str(target),
                        'pins': profile['packages'], 'active_dependencies': edges,
                        'status': 'PASS_METADATA_CLOSURE'})
    return {'schema': 'UDM_BOOTSTRAP_METADATA_RECEIPT_V3',
            'status': 'PASS_METADATA_CLOSURE',
            'catalog_sha256': hashlib.sha256(raw).hexdigest(),
            'package_metadata_sha256': hashlib.sha256(metadata_raw).hexdigest(),
            'packaging_version': packaging.__version__, 'profiles': results,
            'target_source_accessed': False, 'native_tests_executed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = validate(args.catalog)
    text = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
