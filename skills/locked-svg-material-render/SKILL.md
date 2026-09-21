---
name: locked-svg-material-render
description: Apply a reference material or surface style to an existing SVG or logo while preserving its exact canvas, paths, element positions, holes, and silhouette. Use for locked-geometry logo renders, Blender material studies, and app-icon styling where shape changes are forbidden; do not use for logo redesigns or freeform reinterpretation.
---

# Locked SVG Material Render

Treat the source SVG as the sole geometry authority and reference images as material authority only. Never trade geometry accuracy for a more attractive render.

## Non-negotiable contract

- Preserve the original canvas size, viewBox, path data, front-face element bounds, holes, centroids, and relative positions.
- Apply one shared canvas-to-scene transform to every front-face element. Never fit, center, or perspective-correct individual elements separately.
- Lock the front-face geometry to the SVG. Physical thickness, side faces, bevel returns, fibers, cast shadows, reflections, and glow may extend outside the front-face mask when required by the reference.
- Orthographic front view is the default. A perspective or angled camera is allowed when requested, but every front-face element must receive the same projective transform and remain correct when the front plane is rectified.
- Do not deliver or present a raw generative full-logo image. Image generation may create a boundary-free material swatch. When the user explicitly chooses a model-guided appearance workflow, it may also create a full-object RGB appearance plate from an exact depth/ID guide, but that plate never owns alpha, silhouette, region boundaries, or feature positions.
- Never clip a full-object reference image through the source mask when that reference contains old contours, internal panel edges, facial features, bevel boundaries, or cast shadows. Those RGB geometry cues survive alpha locking and create a false pass.
- For multi-region materials, isolate a boundary-free swatch for every semantic region (for example crust, crumb, biscuit face, foil frame, pearl panel). Rebuild every visible boundary from source geometry, never from the material reference.
- Treat visually similar variants as separate construction specifications. For example, an open center, a filled inset panel, and a raised center plate are three different layer stacks even when all use the same orange flock.
- Do not treat editor chrome, selection handles, guides, labels, or screenshot margins as reference content. Obtain a clean asset export when available; otherwise record and remove the UI crop before material analysis.
- Treat the reference's macro construction as immutable material evidence: recessed versus raised regions, layer order, seam behavior, edge thickness, reflection strength, lighting direction, and texture scale must not be creatively reinterpreted.
- Maintain a separate front-face coverage pass whose rectified alpha is byte-identical to the authoritative SVG mask. Total rendered alpha may be larger when approved depth or effects extend beyond the front face.
- A geometrically correct but materially poor result is still a failure. Never call an output complete merely because the mask passes.
- Default delivery is the complete background-composited image. Preserve reference-consistent backdrop, contact shadow, ground reflection, and environmental light. Produce a transparent-background deliverable only when the user explicitly requests one; a transparent front-face pass may still be kept internally for validation.
- Preserve perceived color through an explicit ICC-managed conversion. For Figma-targeted PNG delivery, convert Display P3 pixels through the embedded source profile into sRGB and embed a standard sRGB profile; never strip the profile or merely relabel unchanged P3 pixel values as sRGB. Preserve Display P3 only when the user explicitly requires a P3 deliverable. When the source declares an sRGB PNG chunk without an ICC payload, embed a standard sRGB profile in the result.

## Required workflow

1. Freeze a written requirement ledger before production: geometry authority, material references, per-variant layer order, recessed/raised state, camera allowance, background policy, and output count. Do not silently revise it during iteration.
2. Establish and record the geometry contract before material work: canvas dimensions, viewBox, full mark bbox, and component bboxes.
3. Rasterize the original SVG once with a deterministic renderer. Save that coverage image as the authoritative mask; do not derive the mask from a generated or styled result.
   - If the user has already approved the reference appearance and identifies only cross-variant scale or position inconsistency, enter **registration mode**. Preserve the complete reference image and its pixels; use the SVG-derived model's orthographic front-face projection only to calculate one whole-image transform. Do not regenerate materials, repaint facial features, inpaint the background, or reconstruct semantic regions unless registration demonstrably cannot align them.
4. Build or import the model with a single transform. Render a flat geometry proof and compare it with the authoritative mask before adding materials.
5. Analyze the material reference separately: base color, fiber/grain scale, roughness, sheen, macro lighting, layer order, and forbidden artifacts.
6. Validate every extracted source-region mask before texture mapping. Stop if a mask touches unrelated background objects, joins separate objects, contains holes from facial features, or visibly departs from its intended semantic region.
7. Produce material appearance without giving a generative model authority over logo geometry. Prefer region-specific texture swatches or procedural shaders. An RGB lighting plate is allowed only when it contains no old object boundary or feature geometry.
   - For a model-guided appearance workflow, render the exact model as the edit target and label the material image as style-only. Treat the generated result as an RGB appearance proposal; discard its geometry and snap every semantic region back through the SVG-derived masks before review.
8. Complete one representative difficult variant and pass all gates before batch-producing siblings. Do not batch an unproven pipeline.
9. Composite the approved front-face RGB appearance through the authoritative SVG masks. Composite approved depth/effect layers separately, behind or outside the front face.
10. Inspect the actual final at 100% and fit-to-screen with the source guide overlaid. Reject stretching, streaking, duplicated outlines, old features, incorrect depth, or material drift before running delivery validation.
   - Inspect the opaque, background-composited final itself, not only the isolated front-face pass. Classify every visible contour outside the SVG as an approved effect (side face, fiber, shadow, reflection, or glow). If a halo, highlight, bevel, or shadow reads as a displaced object edge, reject or repair it even when front-face alpha is byte-identical.
11. Run `scripts/verify_locked_render.py` on the front-face coverage pass, not on total rendered alpha. Bind the report to the exact final asset with its filename and SHA-256; a helper or proxy file cannot validate a different final image.
12. Deliver the background-composited final only when numeric geometry review and visual material review both pass. Deliver a transparent final only when explicitly requested. Keep raw generations, failed drafts, and unapproved candidates out of the handoff.

Read [references/acceptance.md](references/acceptance.md) before executing or reviewing a render. It contains the stage gates, rejection criteria, and the current Matters fixture.

## Decision rules

- If visible fibers cross the SVG boundary, keep them only in a separately reviewable depth/effect layer; they may not redefine the front-face path.
- If a geometric bevel changes the front-face mask, keep the original front face as a separate exact cap and place bevel/side geometry behind it.
- If the reference has fine flock but the result resembles towel loops, carpet, noise, fabric weave, or repeated tiles, reject the material stage.
- If geometry passes but material fidelity is uncertain, report that the result is not yet acceptable and continue only with the material stage. Do not regenerate geometry.
- Alpha equality proves coverage only. It cannot validate visible RGB contours. Reject any render whose RGB contains a second silhouette, old inner border, duplicated feature, or reference-derived shadow that does not align with source geometry.
- Reject any candidate that changes a recessed panel into a raised plate (or the reverse), invents extra rims or bevels, increases gloss/reflection beyond the reference, or replaces distinctive reference texture with a generic version of the material.
- Reject radial smearing, stretched pores, brush-like streaks, mirrored or repeated texture patches, inpainting seams, and any texture deformation that reveals the mapping method.
- Never let a full-logo generation become final geometry. In the explicit model-guided workflow, a full-object generation is allowed only as an internal RGB appearance plate between an exact model guide and deterministic SVG re-locking; it must not be shown or handed off before the final mask/overlay gates pass.
- When an approved reference already has the desired material, lighting, background, depth, and features, do not invoke image generation merely to normalize a series. Register the existing image as a whole to the model's locked front-face projection. Preserve the background, contact shadow, side thickness, bevels, and texture in the same transform. Treat effects beyond the locked cap as allowed overflow; do not crop them back to the SVG bbox.
- Registration mode must record the source and target front-face bboxes, the applied transform, the exact-model front-face alpha result, and an overlay review of the opaque final. If a single whole-image transform aligns the reference, stop there: local feature relocation, warping, inpainting, or texture synthesis is prohibited because it changes an already-approved appearance.
- In registration mode, inspect the input and final color profiles as part of validation. For Figma delivery, require an embedded sRGB profile and confirm that any wide-gamut input was profile-converted rather than stripped or retagged; otherwise the artwork may appear desaturated.
- When the user assigns modeling to position only, do not spend production time rebuilding the final material in Blender. Use Blender for geometry, depth, normals, ID masks, and shadow guides; use the requested drawing/generative stage for material and effects; then perform deterministic SVG re-locking.
- Never validate a background-composited final by testing the alpha of a separately constructed transparent proxy. A proxy may prove the mask implementation, but it cannot prove the visible RGB geometry of the final.
- Never report `0 pixel difference` without naming the tested layer. Say `front-face alpha: 0 differing pixels`; separately report the composited-final visible-edge review. A front-face pass cannot certify shadows, halos, side faces, or RGB edge placement in the final.
- Never call a batch complete after inspecting only a contact sheet. Every variant must be reviewed individually at 100%, and the contact sheet is supplementary.
- Never infer a semantic region from color alone when the reference contains shadows, adjacent objects, or similarly colored backgrounds. Confirm the region against the reference construction and inspect its binary mask before use.
- If a source segmentation, warp, or material extraction fails once, repair and revalidate that stage before rendering more variants. If the same failure class repeats, discard the method instead of stacking corrective patches.
- Do not expose raw tool output as a result before the required gates. Label unavoidable previews explicitly as unvalidated and never describe them as final, passed, or usable.
- Do not redefine the user's locked rules during iteration. Change only the failing stage.
