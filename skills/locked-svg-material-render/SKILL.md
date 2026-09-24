---
name: locked-svg-material-render
description: Apply reference materials to SVG-defined artwork with exact geometry or user-authorized visual consistency across a series. Keep shared scale, placement and facial layout, with separately bounded material edges. Includes runtime preflight and delivery checks.
---

# Locked SVG Material Render — workflow 2

SVG owns geometry. References own material, lighting and construction. An attractive image and a matching outer rectangle do not establish geometric correctness.

For a reference-only request such as “此风格”, continue the existing mark and read [regional material and construction choices](references/regional-materials.md). Resolve the user's latest center/face instructions before generating: a filled center, colored eyes and cut-through eyes are different constructions. For repeated styles, reuse checksum-verified source guides, not a previous generation's geometry or its entire task manifest.

## Select acceptance from the user's actual goal

Use `exact_geometry` for an explicit pixel-exact request. When the user allows material edges to extend and prioritizes a visually consistent series, use `series_consistency` and read [series-consistency.md](references/series-consistency.md). Keep the SVG baseline but evaluate core placement separately from bevel, refraction and fibers. Do not sacrifice approved generative appearance merely to obtain exact coverage under this mode. A full generated image may be delivered after the bounded series checks and visual review pass; it does not need replacement with a procedural beauty render.

The user's 2026-09-23 Matters instruction allows moderate edge extension while retaining stable size, position and facial layout across the series. It authorizes this session's switch to `series_consistency`; the numeric defaults are assistant-selected working limits, not numbers specified by the user. Existing strict reports keep their original meaning. Record the new choice and authorization in a new task contract; do not retroactively mark old failed candidates approved.

## Start here, before any generation

1. Read [acceptance.md](references/acceptance.md) and [workflow.md](references/workflow.md). Select `new_material`, `registration` or `depth_revision` from the user's intent. Also freeze who produces appearance: if the user assigns the model to positioning and requests image generation for effects, record `production_route: model_guided_appearance`; that choice overrides the procedural-material preference below.
2. Verify the task-required source files against a pinned repository revision. Record what is present and missing. Remote README access is not local synchronization. Unrelated old variants need not be downloaded; never describe a partial snapshot as a full clone or installation.
3. Freeze the geometry/construction contract: original SVG and checksum, canvas/viewBox, renderer, authoritative masks, ALL semantic regions and their raised/recessed/open/cut-out roles, allowed effects, background and output count. For Matters this includes outer silhouette, inner boundary, left eye, right eye and smile—not just a union alpha. White SVG canvas rectangles are background; document foreground extraction without changing paths.
   For the current Matters source, load [the absolute geometry policy](references/matters-absolute-geometry.json), copy it unchanged into the task, and bind it as `contract.absolute_geometry_rules: {path, sha256}`. This freezes the original SVG, 1024 canvas and five complete reference masks. The execution gate rejects substituted references or omitted regions in either mode. Freeze final-image tolerances before generation; a later explicit user scope change requires a newly recorded contract, not an overwritten historical verdict. These are release criteria, not generator coordinate-control capabilities.
4. Create the local task manifest in the documented schema. Run `scripts/workflow.py preflight` using the actual planned runtime. A failed smoke render, missing source or dependency is `BLOCKED`. Fix the environment within available permissions or report the concrete blocker. Do not silently replace modeling with image generation, a height-filter approximation or hand-written gradients.

On another machine, verify the actual local skill/scripts against the intended Git revision before production. A successful push, a remote README, or an old source-asset revision does not prove that this machine loaded the new skill. The pinned source SVG revision and the version of the workflow are separate facts.

For the bundled Matters project, `build_constraint_model.py` creates an emission-colored geometry guide, not a finished material renderer. `register_reference.py` creates an unvalidated whole-image registration proposal only. Neither is a working sandstone/material production pipeline. Do not invent a successful production stage when only those helpers exist.

## Choose the right production route

- **Model-guided appearance, when selected by the user:** the model is used only for exact position, silhouette, regional IDs, depth, normals and optional shadow guides. Use the image-generation stage for the requested material, lighting and surface appearance. Do not replace that stage with a fully procedural beauty render, even if a CPU/GPU renderer is available. Start with one difficult variant, inspect its actual RGB boundaries, and reject a drifting result before making siblings. The generative tool's reference-image input is guidance, not an enforced per-pixel geometry lock. Deterministic compositing may use SVG coverage only after RGB boundary checks; it cannot erase wrong geometry already visible inside a plate.
- **New material:** construct exact geometry from the original SVG or verified model. Establish the flat geometry proof and regional ID masks first. Add volume, depth, surface normals, material and effects appropriate to the reference. Procedural methods are valid when they actually represent the required construction; texture plus offset shadow is not a substitute for modeled rounded volume, refraction or carved walls.
- **Registration:** only for an already accepted complete appearance. Preserve the whole image and perform one shared transform, including shadows/background. Bbox fitting is a candidate stage, never a final verdict. Check every semantic region afterward. If internal boundaries disagree, report registration as insufficient; do not pretend another global scale fixes it. Return to SVG-constrained production for failed regions while preserving accepted appearance where possible.
- **Depth revision:** freeze a new layer-stack contract reflecting the user's change (for example raised eyes become cavities). Start from the authoritative geometry and retained material evidence. A previous image is appearance reference, not replacement geometry. Do not infer a raised center panel merely because the user changed the eyes.

## Image generation has no geometry authority

A material/light probe may also be generated for normal-indexed appearance projection. The model owns all XY coverage and surface normals; the generated probe supplies only sampled radiance. Calibrate the specimen's texture coordinates separately, exclude its background/silhouette pixels, and never use its shape as logo geometry. This is baked, view-dependent appearance, not a claim of physical glass transmission. Validate actual contributing model IDs plus final RGB and reject stretched grain, streaks, or inadequate material quality. Fine grain belongs in boundary-free surface coordinates, not a normal-indexed lookup that stretches it. This route does not permit warping an inaccurate full-logo generation.

A material-only swatch must contain no object boundaries, features, panel rims or cast shadows. In exact mode, a full-object generated plate is an internal appearance candidate until source-derived construction and independent checks establish exact geometry. In series mode, preserve a high-quality full generation when its independently observed core placement, bounded material effects and series review pass. Asking for coordinates is guidance in both modes. Copying SVG alpha onto an unchanged RGB plate does not remove wrong internal features.

Never chain an unverified generated result as the geometry source of the next style. Do not expose a raw generation or failed candidate as the answer to a strict-geometry task. If the user explicitly requests an appearance-only preview, label its limits; that request does not approve its geometry or admit it into final delivery. If a tool automatically exposes raw output, warn before the call that it is unvalidated and do not describe it as a result.

Failed registration is not permission to use TPS, radial warps, per-feature fitting, smudge repair, or painted edges. In exact mode, reconstruct the scene from SVG geometry. In series mode, regenerate a drifting candidate using the original guide and a specific measured correction, with a bounded retry budget. A manually traced generated contour may be an observation, never the reference for subsequent styles. Runtime failure does not authorize a silent route change.

## Mandatory release path

Use `workflow.py validate` and `workflow.py package`, not the legacy alpha helper, for final delivery. The documented task manifest binds all evidence to exact files. The gate requires:

- all source-defined regional coverage checks, including holes and the inner panel;
- observations from real rendered geometry IDs or reviewed segmentation of the exact final RGB, never copied authoritative masks;
- review of actual RGB edges and approved effect extents at native and fit size;
- side-by-side material review, correct depth construction, source-region/texture quality;
- explicit color handling and embedded sRGB, exact-final SHA-256, and nonstale evidence.

`verify_locked_render.py` is a coverage diagnostic only. Its compatibility `status: PASS` never authorizes delivery. A proxy is labeled as a proxy. The package command refuses incomplete/failed/stale evidence; do not hand-build a final ZIP or edit a report to bypass it. Never mark a visual check PASS merely because coverage passed.

## Production invariants

- Preserve source paths, element locations, canvas and one shared canvas-to-scene transform. No per-feature fitting to hide geometry drift. Rectify a permitted perspective before testing the original plane.
- Distinguish front cap, aperture, cavity wall/bottom and total effect silhouette. A cavity-opening mask cannot certify a recessed floor. Keep depth effects separate from exact front coverage.
- Preserve reference construction, grain scale, light direction, texture detail and reflection strength. No invented panels, glossy rims or missing background unless user requests that change. Remove screenshot UI before using pixel material evidence; never transfer grids/handles/text.
- Inspect extracted semantic masks before mapping. Reject contaminated regions, smears, radial stretching, duplicated contours, repeated tiles or old facial geometry. Repair a failing stage rather than adding corrective patches indefinitely.
- Profile-convert wide-gamut input into sRGB before processing. Never strip/retag P3 pixels. Record explicit assumptions for truly untagged input; sRGB chunks can be promoted to a standard embedded profile.
- Keep drafts, rejected work and historical approvals distinct. Do not overwrite an approved asset or rewrite its history. Revalidate after every final-image change.

## Honest limit

This skill is an instruction set plus a release gate, not an image renderer or a security boundary. The scripts detect absent/stale evidence and numerical mismatch; they cannot prove that a reviewer is truthful or automatically judge material fidelity. Never promise that editing a skill alone makes an unconstrained generator exact. Report unresolved limits instead of declaring success.
