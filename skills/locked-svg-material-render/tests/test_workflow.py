import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageCms, ImageDraw

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/workflow.py'
spec = importlib.util.spec_from_file_location('workflow', SCRIPT)
workflow = importlib.util.module_from_spec(spec); spec.loader.exec_module(workflow)


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.p = Path(self.temp.name)
        self.icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        (self.p/'source.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><rect x="4" y="4" width="24" height="24"/></svg>')
        im = Image.new('RGB', (32,32), '#aa7755'); im.save(self.p/'final.png', icc_profile=self.icc)
        im.save(self.p/'reference.png'); im.save(self.p/'comparison.png'); im.save(self.p/'overlay.png')
        self.regions = ['outer', 'inner', 'left_eye', 'right_eye', 'smile']
        self.evidence = {}
        regions = {}
        for name in self.regions:
            mask=Image.new('L',(32,32)); draw=ImageDraw.Draw(mask)
            if name == 'outer': draw.rectangle((4,4,27,27),fill=255)
            elif name == 'inner': draw.rectangle((8,8,23,23),fill=255)
            elif name == 'left_eye': draw.ellipse((10,11,12,16),fill=255)
            elif name == 'right_eye': draw.ellipse((19,11,21,16),fill=255)
            else: draw.arc((11,17,22,24),0,160,fill=255,width=2)
            mask.save(self.p/f'{name}-ref.png');mask.save(self.p/f'{name}-obs.png')
            ev={'final_sha256':self.hash('final.png'),'source_svg_sha256':self.hash('source.svg'),
                'reference_mask_sha256':self.hash(f'{name}-ref.png'),'observed_mask_sha256':self.hash(f'{name}-obs.png'),
                'method':'rendered_geometry_id','reviewer':'synthetic-test-fixture','notes':'Synthetic coverage fixture, not artwork approval'}
            self.evidence[name]=ev;self.write(f'{name}-evidence.json',ev)
            regions[name]={'reference_mask':self.art(f'{name}-ref.png'),'observed_mask':self.art(f'{name}-obs.png'),'evidence':self.art(f'{name}-evidence.json')}
        contract={'source_svg_sha256':self.hash('source.svg'),'canvas':[32,32],'viewBox':[0,0,32,32],
                  'mask_origin':'source_svg_render','renderer':'synthetic-test-fixture','required_regions':self.regions,
                  'construction':{n:'raised' for n in self.regions},'background_policy':'opaque',
                  'reference_masks':{n:self.hash(f'{n}-ref.png') for n in self.regions}}
        self.write('contract.json',contract)
        self.review={'final_sha256':self.hash('final.png'),'contract_sha256':self.hash('contract.json'),
                     'reviewer':'synthetic-test-fixture','reviewed_at':'2026-09-22','scale_checks':['native','fit'],
                     'region_notes':{n:'Synthetic fixture matches' for n in self.regions},
                     'comparison':self.art('comparison.png'),'overlay':self.art('overlay.png')}
        for k in ['visible_edges','material','depth_construction','effects']:
            self.review[k]={'status':'PASS','notes':'Synthetic fixture only'}
        self.write('review.json',self.review)
        self.write('color.json',{'final_sha256':self.hash('final.png'),'input_sha256':self.hash('reference.png'),
                                'operation':'explicit_srgb_assumption','notes':'Synthetic pixels defined in sRGB'})
        self.task={'schema_version':'2.0','mode':'new_material','source_svg':self.art('source.svg'),'contract':self.art('contract.json'),
                   'references':[self.art('reference.png')],'required_modules':['PIL','numpy'],
                   'smoke_tests':[{'name':'synthetic runtime','argv':[sys.executable,'-c','print("fixture-ready")'],'expect':'fixture-ready'}],
                   'final':self.art('final.png'),'color_record':self.art('color.json'),'regions':regions,'review':self.art('review.json')}
        self.save()

    def hash(self,name): return hashlib.sha256((self.p/name).read_bytes()).hexdigest()
    def art(self,name): return {'path':name,'sha256':self.hash(name)}
    def write(self,name,data): (self.p/name).write_text(json.dumps(data))
    def save(self): self.write('task.json',self.task)
    def run_gate(self): self.save();r=workflow.Run(self.p/'task.json');r.validate();return r
    def refresh_review(self): self.write('review.json',self.review);self.task['review']=self.art('review.json')

    def test_complete_evidence_releases(self):
        r=self.run_gate();self.assertTrue(r.report['delivery_ready']);r.package(self.p/'delivery.zip');self.assertTrue((self.p/'delivery.zip').exists())
    def test_equal_outer_bbox_shifted_smile_rejected(self):
        im=Image.open(self.p/'smile-obs.png');shifted=Image.new('L',im.size);shifted.paste(im,(0,-2));shifted.save(self.p/'smile-obs.png')
        self.task['regions']['smile']['observed_mask']=self.art('smile-obs.png')
        ev=self.evidence['smile'];ev['observed_mask_sha256']=self.hash('smile-obs.png');self.write('smile-evidence.json',ev)
        self.task['regions']['smile']['evidence']=self.art('smile-evidence.json')
        with self.assertRaisesRegex(ValueError,'smile: region geometry differs'): self.run_gate()
    def test_alpha_proxy_cannot_certify_rgb(self):
        ev=self.evidence['inner'];ev['method']='copied_svg_alpha';self.write('inner-evidence.json',ev)
        self.task['regions']['inner']['evidence']=self.art('inner-evidence.json')
        with self.assertRaisesRegex(ValueError,'proxy'):self.run_gate()
    def test_missing_eye_blocks(self):
        del self.task['regions']['left_eye']
        with self.assertRaisesRegex(ValueError,'semantic region'):self.run_gate()
    def test_material_failure_blocks(self):
        self.review['material']['status']='FAIL';self.refresh_review()
        with self.assertRaisesRegex(ValueError,'material'):self.run_gate()
    def test_wrong_depth_blocks(self):
        self.review['depth_construction']={'status':'FAIL','notes':'Panel raised but contract requires inset'};self.refresh_review()
        with self.assertRaisesRegex(ValueError,'depth_construction'):self.run_gate()
    def test_runtime_crash_blocks(self):
        self.task['smoke_tests'][0]['argv']=[sys.executable,'-c','raise SystemExit(139)']
        with self.assertRaisesRegex(ValueError,'Runtime unavailable'):self.run_gate()
    def test_missing_module_blocks(self):
        self.task['required_modules']=['nonexistent_render_runtime_test']
        with self.assertRaises(ImportError):self.run_gate()
    def test_missing_asset_blocks(self):
        (self.p/'source.svg').unlink()
        with self.assertRaisesRegex(ValueError,'Missing artifact'):self.run_gate()
    def test_changed_final_blocks(self):
        Image.new('RGB',(32,32),'blue').save(self.p/'final.png',icc_profile=self.icc)
        with self.assertRaisesRegex(ValueError,'Stale or changed'):self.run_gate()
    def test_refreshing_final_hash_does_not_refresh_review(self):
        Image.new('RGB',(32,32),'blue').save(self.p/'final.png',icc_profile=self.icc);self.task['final']=self.art('final.png')
        with self.assertRaisesRegex(ValueError,'stale final'):self.run_gate()
    def test_icc_missing_blocks(self):
        Image.new('RGB',(32,32),'blue').save(self.p/'final.png');self.task['final']=self.art('final.png')
        with self.assertRaisesRegex(ValueError,'lacks embedded ICC'):self.run_gate()
    def test_reference_reused_as_observation_blocks(self):
        self.task['regions']['inner']['observed_mask']=self.task['regions']['inner']['reference_mask']
        with self.assertRaisesRegex(ValueError,'reused'):self.run_gate()
    def test_path_escape_blocks(self):
        self.task['source_svg']['path']='../source.svg'
        with self.assertRaisesRegex(ValueError,'relative'):self.run_gate()
    def test_invented_replacement_source_rejected(self):
        (self.p/'source.svg').write_text('<svg/>');self.task['source_svg']=self.art('source.svg')
        with self.assertRaisesRegex(ValueError,'another SVG'):self.run_gate()
    def test_false_composition_blocks(self):
        Image.new('RGBA',(32,32),'blue').save(self.p/'background.png')
        self.task['composition']={'background':self.art('background.png'),'layers':[]}
        with self.assertRaisesRegex(ValueError,'not the recorded composition'):self.run_gate()
    def test_failed_package_creates_no_zip(self):
        self.review['material']['status']='PENDING';self.refresh_review();self.save()
        with self.assertRaises(ValueError):workflow.Run(self.p/'task.json').package(self.p/'bad.zip')
        self.assertFalse((self.p/'bad.zip').exists())
    def test_cli_failure_writes_blocked_report(self):
        self.task['regions']={};self.save()
        r=subprocess.run([sys.executable,str(SCRIPT),'validate','--task',str(self.p/'task.json'),'--report',str(self.p/'report.json')],capture_output=True)
        self.assertEqual(r.returncode,2);self.assertFalse(json.loads((self.p/'report.json').read_text())['delivery_ready'])
    def test_legacy_alpha_pass_not_delivery(self):
        mask=Image.open(self.p/'outer-ref.png');im=Image.new('RGBA',(32,32),'red');im.putalpha(mask);im.save(self.p/'face.png')
        r=subprocess.run([sys.executable,str(SCRIPT.parent/'verify_locked_render.py'),'--mask',str(self.p/'outer-ref.png'),'--candidate',str(self.p/'face.png'),'--report',str(self.p/'alpha.json')],capture_output=True)
        self.assertEqual(r.returncode,0);report=json.loads((self.p/'alpha.json').read_text());self.assertEqual(report['status'],'PASS');self.assertFalse(report['delivery_ready'])

if __name__=='__main__':unittest.main(verbosity=2)
