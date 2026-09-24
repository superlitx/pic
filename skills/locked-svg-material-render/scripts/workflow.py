#!/usr/bin/env python3
"""Fail-closed evidence checks and packaging. Never infers RGB geometry from alpha."""
import argparse
import hashlib
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

VERSION = '2.0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


class Run:
    def __init__(self, task):
        self.task = Path(task).resolve()
        self.root = self.task.parent
        self.data = json.loads(self.task.read_text())
        self.files = {self.task}
        self.report = {'schema_version': VERSION, 'status': 'BLOCKED',
                       'delivery_ready': False, 'task_sha256': sha(self.task), 'checks': {}}

    def artifact(self, spec):
        need(isinstance(spec, dict), 'Artifact must include path and sha256')
        rel = Path(spec['path'])
        need(not rel.is_absolute() and '..' not in rel.parts, 'Artifact must be relative to task directory')
        p = (self.root / rel).resolve()
        need(p.is_relative_to(self.root), 'Artifact escapes task directory')
        need(p.is_file(), f'Missing artifact: {rel}')
        need(sha(p) == spec['sha256'], f'Stale or changed artifact: {rel}')
        self.files.add(p)
        return p

    def check_absolute_geometry(self):
        """Pin the Matters baseline independently of an editable task contract."""
        policy_path = Path(__file__).resolve().parents[1] / 'references/matters-absolute-geometry.json'
        policy = json.loads(policy_path.read_text())
        declared = self.contract.get('absolute_geometry_rules')
        if sha(self.source) != policy['source_svg_sha256'] and not declared:
            return
        need(bool(declared), 'Matters requires its absolute geometry policy')
        rules_path = self.artifact(declared)
        need(json.loads(rules_path.read_text()) == policy, 'Absolute geometry policy changed; task cannot redefine the baseline')
        need(sha(self.source) == policy['source_svg_sha256'], 'Absolute geometry policy refers to another SVG')
        need(self.contract['canvas'] == policy['canvas'], 'Absolute canvas coordinates changed')
        need(set(self.contract['required_regions']) == set(policy['regions']), 'Absolute geometry requires all five Matters regions')
        for name, rule in policy['regions'].items():
            need(self.contract['reference_masks'][name] == rule['coverage_mask_sha256'],
                 f'{name}: absolute reference mask changed')
        self.report['checks']['absolute_geometry'] = {
            'policy_sha256': sha(rules_path), 'source_svg_sha256': sha(self.source),
            'allowed_differing_coverage_pixels': 0,
            'generator_supports_hard_coordinate_input': False,
            'status': 'BASELINE_PINNED; final observations still required'}

    def check_acceptance_profile(self):
        self.acceptance_mode = self.contract.get('acceptance_mode', 'exact_geometry')
        need(self.acceptance_mode in ['exact_geometry', 'series_consistency'], 'Unknown acceptance mode')
        self.report['acceptance_mode'] = self.acceptance_mode
        if self.acceptance_mode == 'exact_geometry':
            return
        need(self.contract.get('acceptance_authorization', {}).get('user_statement'),
             'Series consistency requires the user-authorized scope change')
        path = self.artifact(self.contract['series_policy'])
        canonical = Path(__file__).resolve().parents[1] / 'references/matters-series-consistency.json'
        self.series_policy = json.loads(path.read_text())
        need(self.series_policy == json.loads(canonical.read_text()), 'Series policy changed after selection')
        need(self.contract['canvas'] == self.series_policy['canvas'], 'Series profile requires its 1024 canvas')
        need(set(self.contract['required_regions']) == set(self.series_policy['regions']), 'Series profile requires all five regions')
        need('absolute_geometry_rules' in self.contract, 'Series profile retains the original SVG baseline')
        self.report['checks']['series_policy'] = {'sha256': sha(path), 'tolerance_origin': self.series_policy['tolerance_origin']}
        self.report['checks']['absolute_geometry']['scope'] = 'Pinned SOURCE baseline; final observations use series tolerances'

    @staticmethod
    def series_region_metrics(a, b, limits, effects=None):
        """Observed core placement and material effects are measured separately."""
        import numpy as np
        aa, bb = a >= 128, b >= 128
        need(aa.any() and bb.any(), 'Empty series core observation')
        def stats(mask):
            ys, xs = np.nonzero(mask)
            return np.array([xs.mean(), ys.mean()]), np.array([xs.max()-xs.min()+1, ys.max()-ys.min()+1])
        ac, az = stats(aa); bc, bz = stats(bb)
        shift = bc-ac
        size_change = np.abs(bz/az-1)
        iou = float(np.count_nonzero(aa & bb)/np.count_nonzero(aa | bb))
        failures = []
        if np.linalg.norm(shift) > limits['max_center_shift_px']: failures.append('core center shifted')
        if size_change.max() > limits['max_size_change_fraction']+1e-9: failures.append('core size changed')
        if iou < limits['min_core_iou']: failures.append('core contour changed')
        result = {'center_delta_px': shift.tolist(), 'center_shift_px': float(np.linalg.norm(shift)),
                  'size_change_fraction': size_change.tolist(), 'core_iou': iou, 'failures': failures}
        if effects is not None:
            need(effects.shape == aa.shape, 'Effect mask canvas mismatch')
            # Elliptical morphology, not a square dilation that admits diagonal overshoot.
            radius = limits['max_material_extension_px']; allowed = np.zeros_like(bb)
            height, width = bb.shape
            horizontal = {}
            for dy in range(-radius, radius+1):
                dx = int((radius*radius-dy*dy)**.5)
                if dx not in horizontal:
                    padded = np.pad(bb, ((0, 0), (dx, dx)))
                    sums = np.pad(np.cumsum(padded, axis=1, dtype=np.int32), ((0, 0), (1, 0)))
                    span = 2*dx+1
                    horizontal[dx] = sums[:, span:]-sums[:, :-span] > 0
                row = horizontal[dx]
                if dy >= 0: allowed[dy:] |= row[:height-dy]
                else: allowed[:height+dy] |= row[-dy:]
            beyond = int(np.count_nonzero((effects > 0) & ~allowed))
            result['material_effect_pixels_beyond_band'] = beyond
            if beyond: failures.append('material extension exceeded')
        result['passed'] = not failures
        return result

    def preflight(self):
        d = self.data
        need(d['schema_version'] == VERSION, 'Unsupported schema')
        need(d['mode'] in ['new_material', 'registration', 'depth_revision'], 'Unknown mode')
        self.source = self.artifact(d['source_svg'])
        need(self.source.suffix.lower() == '.svg', 'Source authority must be SVG')
        self.contract_path = self.artifact(d['contract'])
        self.contract = json.loads(self.contract_path.read_text())
        need(self.contract['source_svg_sha256'] == sha(self.source), 'Contract refers to another SVG')
        need(len(self.contract['canvas']) == 2 and all(type(n) is int and n > 0 for n in self.contract['canvas']), 'Invalid canvas')
        need(self.contract['mask_origin'] == 'source_svg_render', 'Mask must originate from source SVG')
        need(self.contract.get('renderer'), 'Record authoritative mask renderer/version')
        names = self.contract['required_regions']
        need(isinstance(names, list) and names and len(set(names)) == len(names), 'Contract must enumerate semantic regions')
        need(set(self.contract['construction']) == set(names), 'Record depth/role for every region')
        need(set(self.contract['reference_masks']) == set(names), 'Contract must bind every authoritative region mask')
        self.check_absolute_geometry()
        self.check_acceptance_profile()
        need(self.contract.get('background_policy'), 'Freeze background policy')
        need(d.get('references'), 'Material/depth references required')
        for a in d['references'] + d.get('required_files', []):
            self.artifact(a)
        # Dependency presence is insufficient: execute the planned geometry runtime.
        need(d.get('smoke_tests'), 'Geometry/registration runtime smoke test required')
        smoke = []
        for test in d['smoke_tests']:
            need(isinstance(test['argv'], list) and test['argv'] and test.get('expect'), 'Smoke test needs argv and expected output')
            if 'script' in test:
                script = self.artifact(test['script'])
                need(any(str(script) == str((self.root / x).resolve()) for x in test['argv'][1:] if isinstance(x, str)), 'Smoke script not present in argv')
            # Only execute locally authored task manifests. Never execute reference-supplied commands.
            r = subprocess.run(test['argv'], cwd=self.root, capture_output=True, text=True, timeout=30)
            smoke.append({'name': test['name'], 'returncode': r.returncode,
                          'stdout_tail': r.stdout[-1000:], 'stderr_tail': r.stderr[-1000:]})
            self.report['checks']['runtime'] = smoke
            need(r.returncode == 0 and test['expect'] in r.stdout, f"Runtime unavailable: {test['name']}")
        for module in d.get('required_modules', []):
            importlib.import_module(module)
        self.report['checks']['preflight'] = 'PASS'
        self.report['status'] = 'PREFLIGHT_READY'

    def validate(self):
        from PIL import Image, ImageCms
        import numpy as np
        self.preflight()
        d = self.data
        final = self.artifact(d['final'])
        self.report['final_sha256'] = sha(final)
        with Image.open(final) as f:
            need(f.format == 'PNG' and f.size == tuple(self.contract['canvas']), 'Final must be PNG at contracted canvas size')
            need(f.mode in ['RGB', 'RGBA'], 'Final must be RGB/RGBA')
            icc = f.info.get('icc_profile')
            need(bool(icc), 'Final lacks embedded ICC')
            description = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).strip()
            need('srgb' in description.lower(), 'Expected embedded sRGB profile')
            self.report['checks']['color_profile'] = {'description': description, 'sha256': hashlib.sha256(icc).hexdigest()}
        color = json.loads(self.artifact(d['color_record']).read_text())
        need(color['final_sha256'] == sha(final), 'Color record refers to stale final')
        need(color['operation'] in ['icc_conversion', 'declared_srgb', 'explicit_srgb_assumption'], 'Unknown color handling')
        need(color.get('input_sha256') and color.get('notes'), 'Color provenance required; profile label alone is insufficient')
        regions = d['regions']
        need(set(regions) == set(self.contract['required_regions']), 'Missing or unexpected semantic region')
        self.report['checks']['regions'] = {}
        for name, region in regions.items():
            ref = self.artifact(region['reference_mask'])
            obs = self.artifact(region['observed_mask'])
            need(sha(ref) == self.contract['reference_masks'][name], f'{name}: mask differs from frozen contract')
            need(ref != obs, f'{name}: reference reused as observation')
            evidence = json.loads(self.artifact(region['evidence']).read_text())
            need(evidence['final_sha256'] == sha(final), f'{name}: observation bound to another final')
            need(evidence['source_svg_sha256'] == sha(self.source), f'{name}: wrong geometry authority')
            need(evidence['reference_mask_sha256'] == sha(ref) and evidence['observed_mask_sha256'] == sha(obs), f'{name}: stale mask evidence')
            need(evidence['method'] in ['rendered_geometry_id', 'reviewed_final_rgb_segmentation'], f'{name}: copied alpha/proxy is not observed geometry')
            need(evidence.get('notes') and evidence.get('reviewer'), f'{name}: observation needs review provenance')
            with Image.open(ref) as ri, Image.open(obs) as oi:
                need(ri.mode == 'L' and oi.mode == 'L', f'{name}: masks must be explicit grayscale coverage')
                need(ri.size == oi.size == tuple(self.contract['canvas']), f'{name}: mask canvas mismatch')
                a = np.array(ri, dtype=np.int16); b = np.array(oi, dtype=np.int16)
            need(np.any(a >= 128), f'{name}: empty reference region')
            delta = np.abs(a-b)
            check = {'different_coverage_pixels': int(np.count_nonzero(delta)), 'max_delta': int(delta.max()),
                     'different_binary_pixels': int(np.count_nonzero((a >= 128) != (b >= 128)))}
            self.report['checks']['regions'][name] = check
            if self.acceptance_mode == 'exact_geometry':
                need(check['different_coverage_pixels'] == 0, f'{name}: region geometry differs (equal bbox is insufficient)')
            else:
                need(evidence.get('core_definition'), f'{name}: explain visible core versus material effects')
                effect = self.artifact(region['material_effects_mask'])
                need(evidence.get('material_effects_mask_sha256') == sha(effect), f'{name}: stale material-effect evidence')
                with Image.open(effect) as ei:
                    need(ei.mode == 'L' and ei.size == tuple(self.contract['canvas']), f'{name}: invalid effect mask')
                    effects = np.array(ei)
                check.update(self.series_region_metrics(a, b, self.series_policy['regions'][name], effects))
                need(check['passed'], f"{name}: series consistency failed: {', '.join(check['failures'])}")
        if self.acceptance_mode == 'series_consistency':
            checks = self.report['checks']['regions']
            delta = lambda n: np.array(checks[n]['center_delta_px'])
            eye_spacing = float(np.linalg.norm(delta('right_eye')-delta('left_eye')))
            face_center = (delta('left_eye')+delta('right_eye')+delta('smile'))/3
            relative = float(np.linalg.norm(face_center-delta('inner')))
            self.report['checks']['series_layout'] = {'eye_spacing_vector_change_px': eye_spacing,
                                                      'face_to_inner_relative_shift_px': relative}
            need(eye_spacing <= self.series_policy['max_eye_spacing_vector_change_px'], 'Series eye spacing changed')
            need(relative <= self.series_policy['max_face_to_inner_relative_shift_px'], 'Series face shifted within panel')
        # Optional contributing-layer reconstruction proves contribution only, not visible geometry.
        if 'composition' in d:
            comp = d['composition']
            canvas = Image.open(self.artifact(comp['background'])).convert('RGBA')
            for layer in comp['layers']:
                image = Image.open(self.artifact(layer)).convert('RGBA')
                need(image.size == canvas.size, 'Composition layer size mismatch')
                canvas.alpha_composite(image)
            actual = Image.open(final).convert('RGBA')
            need(canvas.size == actual.size and canvas.tobytes() == actual.tobytes(), 'Saved final is not the recorded composition')
            self.report['checks']['composition'] = 'MATCH; does not replace RGB review'
        review = json.loads(self.artifact(d['review']).read_text())
        need(review['final_sha256'] == sha(final) and review['contract_sha256'] == sha(self.contract_path), 'Visual review is stale')
        need(review.get('reviewer') and review.get('reviewed_at'), 'Visual reviewer and date required')
        need(review['scale_checks'] == ['native', 'fit'], 'Review at native and fit scale')
        need(set(review['region_notes']) == set(regions), 'Review every semantic region, not only outer bbox')
        need(all(isinstance(v, str) and v.strip() for v in review['region_notes'].values()), 'Region observations cannot be blank')
        for key in ['visible_edges', 'material', 'depth_construction', 'effects']:
            verdict = review[key]
            need(verdict['status'] == 'PASS' and verdict.get('notes'), f'Visual gate not passed: {key}')
        need(review.get('comparison') and review.get('overlay'), 'Reference comparison and exact-final overlay required')
        self.artifact(review['comparison']); self.artifact(review['overlay'])
        if self.acceptance_mode == 'series_consistency':
            need(review.get('series_preview_sizes') == self.series_policy['contact_sheet_sizes'], 'Series review needs 64 and 128 px comparisons')
            self.artifact(review['series_contact_sheet'])
            verdict = review.get('series_consistency', {})
            need(verdict.get('status') == 'PASS' and verdict.get('notes'), 'Series contact-sheet review not passed')
        self.report['checks']['visual_review'] = 'PASS_REVIEWER_ATTESTED'
        self.report['limitations'] = 'Visual judgments and mask provenance are reviewer-attested; this script cannot authenticate their truth or infer visible geometry from RGB automatically.'
        self.report['status'] = 'DELIVERY_READY'
        self.report['delivery_ready'] = True

    def package(self, path):
        self.validate()
        target = Path(path).resolve()
        need(not target.exists(), 'Refuse to overwrite a delivery archive')
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
            sums = []
            for file in sorted(self.files):
                rel = str(file.relative_to(self.root)); z.write(file, rel)
                sums.append(f'{sha(file)}  {rel}')
            z.writestr('delivery-validation.json', json.dumps(self.report, indent=2))
            z.writestr('SHA256SUMS', '\n'.join(sums) + '\n')
        self.report['package'] = str(target)
        self.report['package_sha256'] = sha(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['preflight', 'validate', 'package'])
    parser.add_argument('--task', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    run = None
    try:
        run = Run(args.task)
        if args.action == 'preflight': run.preflight()
        elif args.action == 'validate': run.validate()
        else:
            need(args.output is not None, 'package requires --output')
            run.package(args.output)
        report = run.report
        code = 0
    except Exception as e:
        report = run.report if run else {'schema_version': VERSION, 'checks': {}}
        report.update(status='BLOCKED', delivery_ready=False, reason=f'{type(e).__name__}: {e}')
        code = 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': report['status'], 'delivery_ready': report.get('delivery_ready', False), 'reason': report.get('reason')}, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
