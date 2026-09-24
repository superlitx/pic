# Acceptance: independent gates, no substitute evidence

Select the acceptance mode before production. Historical tasks and omitted mode use `exact_geometry`. A user-authorized `series_consistency` task follows [series-consistency.md](series-consistency.md): the same source baseline is pinned, but final core placement and material extension have separate bounded allowances. Its series review replaces the demand for exact final coverage; source integrity, independent observations, material quality, color and hash binding still apply. Do not call a series pass pixel-exact.

## A. Source and runtime

Pin the repository commit and hash the files actually used. Verify original SVG, source masks, model and scripts for this task. A list of files on GitHub is not a downloaded bundle. Smoke-test the chosen runtime before spending on appearance generation. Missing Blender/OpenCV/source data is a blocker for a route requiring it, not implicit permission to downgrade the route.

## B. Geometry and construction

Extract/freeze masks directly from SVG with one recorded renderer. Record viewBox, canvas and shared transform. Inventory every region, its holes and depth role. For Matters require `outer`, `inner`, `left_eye`, `right_eye`, `smile`. Outer and inner are separate masks; eyes/smile are evaluated whether represented by solids or cavities. A depth change requires an updated construction contract, not new XY geometry.

Compare independently observed regions with the source using the selected mode. Exact mode requires byte equality; series mode measures core centers, dimensions, overlap, relative facial layout and separate material effects. Equal boxes or union alpha alone cannot pass either mode. Do not loosen thresholds solely to pass a failure. Explicit new user scope changes are recorded as new contracts.

The current Matters source baseline is pinned in [matters-absolute-geometry.json](matters-absolute-geometry.json). Its 4x raster coverage is fixed independently of each task. Both modes reject substituted reference masks, omitted facial regions or changed canvas. Series mode changes final-image acceptance while retaining this source. Reference-image prompts do not enforce coordinates inside the generator.

Observed masks must come from actual geometry/render IDs or a reviewed segmentation tied to the final RGB. Copying the reference mask and setting an alpha channel is a proxy; it cannot be relabeled as observation. Actual contributing layers and reproducible compositing are useful evidence but still cannot certify the RGB inside them.

## C. Appearance and final visible boundaries

Review exact final and authoritative overlay at 100% plus fit view. Inspect every lobe/corner/notch, inner boundary, both eyes and smile. Distinguish front cap edge from side return, bevel, reflection, shadow, fibers and glow. Reject displaced/double edges, old generated features and apparent boundary shifts.

Compare final and clean style reference at comparable scale, including material-specific crops. Explicitly assess:
- depth sign/layer order: raised versus inset versus cavity;
- texture character and scale, pressure/roughness variation;
- volume, edge transitions and interaction with light;
- light direction, highlight breadth, reflection strength and contact shadow;
- background and reference-specific details.

Fine flock is not carpet or terry cloth. Paper is not generic noise. Sandstone is not a blurry bevel filter. Copper needs coherent curved reflection bands, not a painted gradient. A plausible thumbnail is insufficient. Uncertain review stays pending; failed material cannot become final merely because geometry passes.

## D. Binding and color

Final must be the exact reviewed bytes. Every region observation, visual review, color record and overlay must name/hash that final (overlay bytes are separately hashed). Changing the image, model, masks, contract or source invalidates affected evidence. Perform actual ICC conversion for tagged wide-gamut input. Profile presence or the word sRGB alone cannot prove conversion happened.

## E. Release

Only `workflow.py package` after all gates can produce an eligible final archive. It reruns checks. Legacy alpha `PASS` is never a whole-delivery result. A failed/incomplete run yields a blocker report; it must not emit an apparently final picture merely accompanied by a disclaimer.

### Regression cases that MUST be rejected

1. Same outer bbox, but smile or eyes exceed the selected placement limits (any difference in exact mode).
2. Exact alpha on a plate containing wrong inner panel RGB.
3. An inherited generated image offered as geometry authority.
4. Correct mask with materially poor flat-shaded texture.
5. Raised panel when ledger requires recessed panel.
6. Blender startup failure or missing OpenCV while claiming original workflow executed.
7. Stale hash/review after resizing/recoloring.
8. Missing masks or reviews hidden behind a blanket PASS.

## Historical Matters raster fixture

The original supplied fixture is 1024 square; union bbox `(128,128,896,896)` (exclusive right/bottom). Frame binary area 265881; eye bboxes `(374,394,434,502)` and `(590,394,650,502)`, each area 5089; smile bbox `(434,568,621,659)`, area 7631. These figures belong to the historical 128-threshold renderer, not every rasterizer. Preserve the supplied authoritative mask when available. If deliberately changing renderer, establish and document one new mask; do not mix it with old numeric claims.
