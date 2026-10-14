#!/usr/bin/env python3
"""Verify CUDA/Triton files against the installed distributions' RECORD hashes."""
import base64
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
checked = 0
size = 0
bad = []
packages = []
for dist in metadata.distributions():
    name = dist.metadata.get("Name", "")
    if not (name.startswith("nvidia-") or name == "triton"):
        continue
    packages.append({"name": name, "version": dist.version})
    for entry in dist.files or []:
        if entry.hash is None or entry.suffix == ".pyc":
            continue
        path = Path(dist.locate_file(entry))
        if not path.is_file():
            bad.append(str(path))
            continue
        digest = hashlib.new(entry.hash.mode)
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        encoded = base64.urlsafe_b64encode(digest.digest()).decode().rstrip("=")
        if encoded != entry.hash.value:
            bad.append(str(path))
        checked += 1
        size += path.stat().st_size
result = {"packages": packages, "record_hashes_checked": checked, "bytes_checked": size,
          "mismatches": bad, "passed": bool(checked) and not bad}
output = root / "outputs" / "runtime_integrity.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2) + "\n")
print(f"Checked {checked} files; {len(bad)} mismatches; report: {output}")
raise SystemExit(0 if result["passed"] else 1)
