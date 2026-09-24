"""Material overhang cannot conceal core drift; old exact tasks remain exact."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image, ImageDraw

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('series_workflow', SKILL/'scripts/workflow.py')
workflow = importlib.util.module_from_spec(spec); spec.loader.exec_module(workflow)
POLICY = json.loads((SKILL/'references/matters-series-consistency.json').read_text())


class SeriesConsistencyTests(unittest.TestCase):
    def mask(self, bounds=(35,30,64,83)):
        im = Image.new('L',(128,128)); ImageDraw.Draw(im).ellipse(bounds,fill=255)
        return np.array(im)

    def metrics(self, obs, effects=None):
        return workflow.Run.series_region_metrics(self.mask(),obs,POLICY['regions']['left_eye'],effects)

    def test_small_translation_is_allowed(self):
        r=self.metrics(self.mask((37,30,66,83)))
        self.assertTrue(r['passed']); self.assertAlmostEqual(r['center_shift_px'],2)

    def test_ten_pixel_shift_is_rejected_despite_allowed_edges(self):
        r=self.metrics(self.mask((35,20,64,73)))
        self.assertFalse(r['passed']); self.assertIn('core center shifted',r['failures'])

    def test_eye_growth_is_not_reclassified_as_center_preserving_bevel(self):
        r=self.metrics(self.mask((35,15,64,83)))
        self.assertFalse(r['passed']); self.assertIn('core size changed',r['failures'])

    def test_symmetric_material_extension_preserves_core(self):
        core=self.mask(); effects=np.zeros_like(core)
        effects[56,27]=255;effects[56,72]=255
        r=self.metrics(core,effects)
        self.assertTrue(r['passed']);self.assertEqual(r['center_shift_px'],0)

    def test_excess_material_extension_is_rejected(self):
        core=self.mask(); effects=np.zeros_like(core);effects[56,20]=255
        r=self.metrics(core,effects)
        self.assertFalse(r['passed']);self.assertIn('material extension exceeded',r['failures'])

    def test_extension_radius_is_euclidean_not_square(self):
        core=np.zeros((64,64),np.uint8);core[30:34,30:34]=255
        effects=np.zeros_like(core);effects[38,38]=255 # 7.07 px from the corner
        limits=dict(max_center_shift_px=5,max_size_change_fraction=.12,min_core_iou=.82,max_material_extension_px=5)
        r=workflow.Run.series_region_metrics(core,core,limits,effects)
        self.assertEqual(r['material_effect_pixels_beyond_band'],1)

    def test_empty_core_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Empty series'):
            self.metrics(np.zeros((128,128),np.uint8))

    def profile_run(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        (root/'task.json').write_text('{}')
        (root/'policy.json').write_text(json.dumps(POLICY))
        run=workflow.Run(root/'task.json')
        run.contract={'acceptance_mode':'series_consistency','canvas':[1024,1024],
                      'required_regions':list(POLICY['regions']),'absolute_geometry_rules':{},
                      'series_policy':{'path':'policy.json','sha256':hashlib.sha256((root/'policy.json').read_bytes()).hexdigest()},
                      'acceptance_authorization':{'user_statement':'允许材质边缘适当超出，保持系列位置稳定'}}
        run.report['checks']['absolute_geometry']={}
        return run

    def test_explicit_series_mode_uses_new_policy(self):
        run=self.profile_run();run.check_acceptance_profile()
        self.assertEqual(run.report['acceptance_mode'],'series_consistency')

    def test_absent_mode_keeps_exact_acceptance(self):
        run=self.profile_run();del run.contract['acceptance_mode'];run.check_acceptance_profile()
        self.assertEqual(run.acceptance_mode,'exact_geometry')

    def test_series_mode_requires_recorded_scope_change(self):
        run=self.profile_run();del run.contract['acceptance_authorization']
        with self.assertRaisesRegex(ValueError,'user-authorized'):
            run.check_acceptance_profile()

    def test_rehashed_looser_task_policy_is_rejected(self):
        run=self.profile_run(); changed=copy.deepcopy(POLICY);changed['regions']['left_eye']['max_center_shift_px']=50
        path=run.root/'policy.json';path.write_text(json.dumps(changed))
        run.contract['series_policy']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'policy changed'):
            run.check_acceptance_profile()

if __name__=='__main__':unittest.main()
