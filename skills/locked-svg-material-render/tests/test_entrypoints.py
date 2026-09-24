"""Test historical entrypoints cannot silently bypass the release gate."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageCms

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parents[1]
SCRIPTS = SKILL / 'scripts'
spec = importlib.util.spec_from_file_location('colors', SCRIPTS/'color_management.py')
colors = importlib.util.module_from_spec(spec); spec.loader.exec_module(colors)


class Entrypoints(unittest.TestCase):
    def test_old_registration_invocation_does_not_create_a_final(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'must-not-exist'
            run = subprocess.run([sys.executable,str(ROOT/'AppLogo_Blender/approved-delivery/scripts/register_reference.py'),
                                  '--source',str(Path(d)/'source.png'),'--slug','test','--output-dir',str(out)],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('BLOCKED',run.stderr)
            self.assertFalse(out.exists())

    def test_untagged_requires_explicit_color_assumption(self):
        with self.assertRaisesRegex(ValueError,'Untagged'):
            colors.convert_srgb(Image.new('RGBA',(2,2),(200,100,40,77)))
        result,icc,record = colors.convert_srgb(Image.new('RGBA',(2,2),(200,100,40,77)),True)
        self.assertEqual(result.getpixel((0,0)),(200,100,40,77))
        self.assertEqual(record['operation'],'explicit_srgb_assumption')
        self.assertIn('sRGB',ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))))

    def test_p3_conversion_changes_color_values_preserves_alpha(self):
        path = Path('/System/Library/ColorSync/Profiles/Display P3.icc')
        if not path.is_file(): self.skipTest('System Display P3 profile unavailable')
        source = Image.new('RGBA',(3,3),(200,100,40,77)); source.info['icc_profile'] = path.read_bytes()
        result,icc,record = colors.convert_srgb(source)
        self.assertNotEqual(result.getpixel((0,0))[:3],(200,100,40))
        self.assertEqual(result.getpixel((0,0))[3],77)
        self.assertEqual(record['operation'],'icc_conversion')
        self.assertIn('sRGB',ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))))

    def test_generated_logo_plate_is_rejected_before_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'origin.json').write_text(json.dumps({'kind':'full_logo_generation'}))
            run=subprocess.run([sys.executable,str(SCRIPTS/'lock_svg_alpha.py'),'--material',str(p/'rgb.png'),
                                '--mask',str(p/'mask.png'),'--source-svg',str(p/'source.svg'),
                                '--provenance',str(p/'origin.json'),'--report',str(p/'report.json'),
                                '--output-transparent',str(p/'result.png')],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0); self.assertIn('BLOCKED',run.stderr)
            self.assertFalse((p/'result.png').exists())

    def test_eligible_swatch_records_coverage_icc_and_actual_file_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'source.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4"/></svg>')
            Image.new('RGB',(4,4),(200,100,40)).save(p/'rgb.png')
            Image.new('L',(4,4),173).save(p/'mask.png')
            sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
            (p/'origin.json').write_text(json.dumps({'kind':'boundary_free_material','material_sha256':sha(p/'rgb.png'),
                                                     'source_svg_sha256':sha(p/'source.svg'),'notes':'Uniform color fixture, no boundaries.'}))
            run=subprocess.run([sys.executable,str(SCRIPTS/'lock_svg_alpha.py'),'--material',str(p/'rgb.png'),'--mask',str(p/'mask.png'),
                                '--source-svg',str(p/'source.svg'),'--provenance',str(p/'origin.json'),'--assume-srgb',
                                '--report',str(p/'report.json'),'--output-transparent',str(p/'face.png'),
                                '--output-background',str(p/'composite.png')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            report=json.loads((p/'report.json').read_text())
            self.assertFalse(report['delivery_ready'])
            self.assertEqual(report['final_sha256'],sha(p/'composite.png'))
            with Image.open(p/'face.png') as face,Image.open(p/'mask.png') as mask,Image.open(p/'composite.png') as final:
                self.assertEqual(face.getchannel('A').tobytes(),mask.tobytes())
                self.assertTrue(face.info.get('icc_profile')); self.assertTrue(final.info.get('icc_profile'))


if __name__=='__main__': unittest.main()
