"""Prepare the six original native TOML source revisions; no science rerun."""
import argparse
from pathlib import Path
import subprocess

from .native_observation import NATIVE_PINS, checked_world


def prepare(worlds, repository=None):
    worlds = Path(worlds).absolute()
    if worlds.exists() and worlds.resolve() != worlds:
        raise ValueError('native world root redirected')
    worlds.mkdir(parents=True, exist_ok=True)
    repository = Path(repository).resolve() if repository else worlds.parent/'tomlkit-source.git'
    if not repository.exists():
        subprocess.run(['git', 'clone', '--bare', 'https://github.com/python-poetry/tomlkit.git', str(repository)], check=True)
    for family, versions in NATIVE_PINS.items():
        for version, sha in versions.items():
            if subprocess.run(['git', '-C', str(repository), 'cat-file', '-e', sha+'^{commit}'],
                    capture_output=True).returncode:
                subprocess.run(['git', '-C', str(repository), 'fetch', '--no-tags', 'origin', sha], check=True)
            target = worlds/(family+version)
            if not target.exists():
                subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(repository), str(target)], check=True)
            if set(p.name for p in target.iterdir()) == {'.git'}:
                subprocess.run(['git', '-C', str(target), 'checkout', '--quiet', '--detach', sha], check=True)
            checked_world(target, sha)
    return worlds


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worlds', type=Path, required=True)
    parser.add_argument('--repository', type=Path)
    args = parser.parse_args()
    print(prepare(args.worlds, args.repository))
