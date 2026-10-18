"""Copy audit state and reverse newer migrations before testing an older one."""
import json
import shutil
import gzip
import hashlib


def copy_repair_state(root, destination, repair, later_repairs=()):
    historical = root / repair.AUDIT / "after.json.gz"
    if historical.exists():
        # An exact, independently hash-checked historical postimage avoids
        # assuming that unrelated branches form one reversible linear chain.
        audit = json.loads((root / repair.AUDIT / "changes.json").read_text())
        snapshots = json.loads(gzip.decompress(historical.read_bytes()))["files"]
        assert set(snapshots) == set(audit["outputs"])
        shutil.copytree(root / repair.AUDIT, destination / repair.AUDIT)
        for path, raw in snapshots.items():
            assert (hashlib.sha256(raw.encode()).hexdigest() if raw is not None else None) == audit["outputs"][path]
            if raw is not None:
                target = destination / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(raw)
        return
    repairs = [module for module in later_repairs if (root / module.AUDIT / "changes.json").exists()]
    paths = set()
    for module in [repair, *repairs]:
        audit_dir = root / module.AUDIT
        paths.update(json.loads((audit_dir / "changes.json").read_text())["outputs"])
        shutil.copytree(audit_dir, destination / module.AUDIT)
    for path in paths:
        source, target = root / path, destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            shutil.copyfile(source, target)
    for module in repairs:
        module.run(destination, "undo")
