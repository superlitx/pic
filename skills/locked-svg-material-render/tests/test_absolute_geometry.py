"""A task cannot redefine the project's geometry baseline to pass validation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('absolute_workflow', SKILL / 'scripts/workflow.py')
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)


class AbsoluteGeometryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copyfile(SKILL.parents[1] / 'AppLogo_Blender/approved-delivery/assets/matters.svg', self.root / 'source.svg')
        self.policy = json.loads((SKILL / 'references/matters-absolute-geometry.json').read_text())
        (self.root / 'task.json').write_text('{}')
        self.run = workflow.Run(self.root / 'task.json')
        self.run.source = self.root / 'source.svg'
        self.run.contract = {
            'canvas': self.policy['canvas'].copy(),
            'required_regions': list(self.policy['regions']),
            'reference_masks': {n: r['coverage_mask_sha256'] for n, r in self.policy['regions'].items()}}
        self.bind_policy(self.policy)

    def bind_policy(self, rules):
        p = self.root / 'rules.json'
        p.write_text(json.dumps(rules))
        self.run.contract['absolute_geometry_rules'] = {
            'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

    def test_original_baseline_accepted(self):
        self.run.check_absolute_geometry()
        self.assertEqual(self.run.report['checks']['absolute_geometry']['allowed_differing_coverage_pixels'], 0)
        self.assertFalse(self.run.report['delivery_ready'])

    def test_omitting_policy_is_rejected(self):
        del self.run.contract['absolute_geometry_rules']
        with self.assertRaisesRegex(ValueError, 'requires its absolute'):
            self.run.check_absolute_geometry()

    def test_rehashed_relaxed_policy_is_rejected(self):
        self.policy['regions']['left_eye']['allowed_differing_coverage_pixels'] = 1
        self.bind_policy(self.policy)
        with self.assertRaisesRegex(ValueError, 'cannot redefine'):
            self.run.check_absolute_geometry()

    def test_rebinding_reference_mask_is_rejected(self):
        self.run.contract['reference_masks']['smile'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'smile: absolute reference mask changed'):
            self.run.check_absolute_geometry()

    def test_missing_eye_is_rejected(self):
        self.run.contract['required_regions'].remove('left_eye')
        with self.assertRaisesRegex(ValueError, 'all five'):
            self.run.check_absolute_geometry()

    def test_canvas_change_is_rejected(self):
        self.run.contract['canvas'] = [1254, 1254]
        with self.assertRaisesRegex(ValueError, 'canvas coordinates changed'):
            self.run.check_absolute_geometry()


if __name__ == '__main__':
    unittest.main()
