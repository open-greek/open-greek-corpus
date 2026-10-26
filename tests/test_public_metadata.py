import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / "scripts/validate_public_export.py"
spec = importlib.util.spec_from_file_location("published_metadata_tests", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicMetadataTests(unittest.TestCase):
    def fixture(self, root):
        registry = root / "data/source_registry.json"
        registry.parent.mkdir(parents=True)
        registry.write_text('{"works":{}}\n')
        reference = {"identity_inputs": {"data/source_registry.json": hashlib.sha256(registry.read_bytes()).hexdigest()}}
        manifest = root / "data/reference/bilby-oga-glaux-2024/manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(reference))
        report = root / "data/oga_glaux_date_comparison.json"
        report.write_text(json.dumps({"provenance": reference}))
        return registry, report

    def test_a_reference_cannot_pin_an_unpublished_registry_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registry, _ = self.fixture(root)
            module.validate_reference_pins(root)
            registry.write_text('{"works":{"changed":{}}}\n')
            with self.assertRaisesRegex(ValueError, "identity input hash differs"):
                module.validate_reference_pins(root)

    def test_date_comparison_must_retain_the_same_reference_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, report = self.fixture(root)
            report.write_text('{"provenance":{}}\n')
            with self.assertRaisesRegex(ValueError, "provenance differs"):
                module.validate_reference_pins(root)
