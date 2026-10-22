"""Frozen source-native infrastructure fixture backend; no discovery algorithm."""
from pathlib import Path
import base64
import csv
import hashlib
import io
import json
import zipfile

NAME = "native_bootstrap_alpha"
VERSION = "1.0.0"
DIST = NAME + "-" + VERSION + ".dist-info"


def _metadata():
    source = json.loads(Path("source-metadata.json").read_text())
    lines = ["Metadata-Version: 2.1", "Name: native-bootstrap-alpha", "Version: " + VERSION]
    value = source.get("requires_python")
    if value is not None:
        lines.append("Requires-Python: " + value)
    for field, key in (("Requires-Dist", "requires_dist"), ("Classifier", "classifiers"), ("Provides-Extra", "provides_extra")):
        lines.extend(field + ": " + value for value in source.get(key, []))
    return ("\n".join(lines) + "\n\n").encode()


def get_requires_for_build_wheel(config_settings=None):
    return []


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    members = {NAME + "/__init__.py": Path("src/" + NAME + "/__init__.py").read_bytes(),
               DIST + "/METADATA": _metadata(),
               DIST + "/WHEEL": b"Wheel-Version: 1.0\nGenerator: frozen-original-fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n"}
    table = io.StringIO(newline="")
    writer = csv.writer(table, lineterminator="\n")
    for path, raw in sorted(members.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b"=").decode()
        writer.writerow((path, "sha256=" + digest, len(raw)))
    writer.writerow((DIST + "/RECORD", "", ""))
    members[DIST + "/RECORD"] = table.getvalue().encode()
    name = NAME + "-" + VERSION + "-py3-none-any.whl"
    with zipfile.ZipFile(Path(wheel_directory) / name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, raw in sorted(members.items()):
            info = zipfile.ZipInfo(path, date_time=(2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return name
