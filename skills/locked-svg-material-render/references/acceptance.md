# Acceptance gates

Every gate is mandatory. A later gate cannot compensate for an earlier failure.

## Gate 0: requirement ledger

Before producing assets, record and freeze:

- the exact source geometry authority;
- the role of every reference image (material/background/depth only unless explicitly stated otherwise);
- whether each semantic region is open, filled, recessed, raised, or cut out;
- whether perspective, side thickness, fibers, shadows, reflections, and glow may extend beyond the front-face mask;
- whether the default deliverable keeps its background;
- the expected variant count and names.
- a separate layer-stack description for variants that reuse a material but differ in open, filled, inset, raised, or cut-out construction.

Any ambiguity must be resolved before batch work. Later clarification updates the ledger; it does not excuse earlier unverified output.

## Gate A: source geometry

Record:

- source SVG path and immutable copy or checksum;
- canvas width and height;
- viewBox;
- antialiased source mask path;
- binary full-mark bbox;
- connected-component bboxes, pixel areas, and centroids.

The SVG paths and source mask are authoritative. A screenshot, generated image, Blender render, or visual estimate is not authoritative geometry.

## Gate B: model and camera

- Use one shared transform from the complete SVG canvas into the scene.
- Preserve front-plane geometry. Add depth, side faces, bevel returns, fibers, and effects as separate geometry or render layers.
- Use an orthographic front camera by default. Perspective is allowed when the requested reference has a view angle, but all front-face components must share one projective transform.
- Render a front-face ID/coverage pass before materials. If perspective is used, rectify that plane back to the source canvas before comparison.
- Compare the rectified front-face proof with the source mask. Do not accept “visually close.”
- Total visible silhouette may exceed the SVG because of approved depth/effects. Those pixels must not be included in the front-face coverage pass.

## Gate C: material fidelity

Before rendering, write a short material target with:

- dominant and highlight colors;
- apparent fiber or grain size at final resolution;
- roughness, sheen, and reflectance;
- macro volume and light direction;
- explicit rejection examples.

For orange short-flock references, reject:

- coarse terry loops, chenille, carpet, knitting, or visible weave;
- speckled red/black noise or large blotches;
- repeated or mirrored tile patterns;
- plastic, clay, or uniform flat fill;
- long hairs or a halo crossing the SVG mask;
- material-generated folds or object shapes unrelated to the model.

Material appearance must be visually reviewed at 100% and fit-to-screen. A mask pass alone is insufficient.

Also perform an RGB geometry-cue review with the source guide overlaid. Reject if:

- a previous generated silhouette remains visible inside the locked alpha;
- a crust, bevel, inner-panel outline, eye, mouth, highlight rim, or shadow follows the reference object's old geometry instead of the source geometry;
- a full-object style plate was merely cropped, scaled, or masked to obtain the final appearance;
- any semantic material boundary cannot be traced back to a source-derived region mask.
- the reference's depth sign or construction changes, such as an inset panel becoming raised;
- distinctive texture, diffraction layout, grain scale, highlight pattern, or reflection intensity is regenerated into a different look instead of preserved.
- source-region masks include surrounding tiles, background, unrelated objects, facial holes, or neighboring semantic materials;
- texture mapping creates radial stretching, streaks, wedges, mirrored repetition, inpainting smears, or visible seams;
- a result looks plausible in a contact sheet but fails at 100% inspection.

The source-region masks themselves are review artifacts. Inspect them before any warp, projection, or batch render. A malformed source mask is a hard stop.

For model-guided generative appearance, validate the exact gray/depth/ID guide first. The generated full-object image is only an RGB appearance plate. Its silhouette, panel edge, feature positions, alpha, and scale are rejected and replaced by SVG-derived semantic masks before the final is eligible for review.

Reference screenshots must be cleaned before analysis. Editor selection borders, resize handles, guide lines, labels, and surrounding UI are not material evidence and must not enter source masks, texture swatches, lighting plates, or final crops.

## Gate D: final front-face lock

Run:

```bash
python3 scripts/lock_svg_alpha.py \
  --material material-rgb.png \
  --mask source-mask.png \
  --output-transparent final-transparent.png \
  --output-background final.png

python3 scripts/verify_locked_render.py \
  --mask source-mask.png \
  --candidate final-transparent.png \
  --report validation.json
```

Run the verifier on the isolated front-face pass. It must report:

- identical canvas size;
- zero differing alpha pixels;
- maximum alpha delta of zero;
- identical full-mark bbox;
- identical component geometry.

The composited final may have additional alpha outside the source mask for side faces, fibers, perspective depth, shadows, reflections, or glow. Keep that total-alpha result distinct from the verified front-face pass.

### No proxy validation

- The validation report must name the exact final asset and include its SHA-256.
- A transparent helper proves only its own alpha. It cannot be cited as proof that an opaque or differently composited final is correct.
- For opaque finals, also save an overlay made from that exact final and the authoritative guides. Inspect visible RGB boundaries, not only alpha.
- The final overlay must make the distinction between the exact SVG front-face edge and permitted effect extents explicit. Review the full perimeter at 100%, including all four outer corners and every concave notch. Reject any effect whose direction, opacity, blur, or asymmetry makes it read as a shifted or enlarged object boundary.
- Geometry reporting must use two separate verdicts: `front-face alpha` and `composited visible edge`. Never summarize the first verdict as proof of the second.
- If the final is regenerated, recomposited, resized, or edited after validation, all validation for that final is invalid and must be rerun.

## Gate E: delivery

Deliver only when both are true:

1. Geometry validation is `PASS`.
2. Material review is `PASS` against the supplied reference.

If either fails, label the result as rejected and do not present it as a final or usable output.

Before batch delivery, the hardest representative variant must pass every gate. Batch production before that pilot passes is prohibited.

Unless the user explicitly requests transparency, the primary deliverable must retain the reference-consistent background, contact shadow, ground reflection, and environmental lighting. Transparent front-face or object passes remain validation artifacts, not the default final.

## Current Matters fixture

When the source is `/Users/z/Desktop/matters.svg`, the locked contract is:

- canvas: `1024 x 1024`;
- full mark bbox: `(128, 128, 896, 896)`, right/bottom exclusive;
- frame component: bbox `(128, 128, 896, 896)`, binary area `265881`;
- left eye: bbox `(374, 394, 434, 502)`, binary area `5089`;
- right eye: bbox `(590, 394, 650, 502)`, binary area `5089`;
- smile: bbox `(434, 568, 621, 659)`, binary area `7631`.

These values describe the current 128-threshold antialiased mask. Re-rasterizing with a different renderer may change edge coverage; if the renderer changes, establish a new authoritative mask once and then keep it fixed for the entire run.
