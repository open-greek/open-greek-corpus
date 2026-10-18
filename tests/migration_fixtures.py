"""Copy audit state and reverse newer migrations before testing an older one."""
import json
import shutil


def copy_repair_state(root, destination, repair, later_repairs=()):
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
