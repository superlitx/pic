# Visually consistent material series

Use after the user explicitly permits small edge differences and prioritizes stable series placement. The current Matters session authorized this on 2026-09-23. The working defaults below are engineering choices, not a user demand for these precise numbers. Source paths, reference masks and 1024 canvas remain unchanged.

## Separate placement from material effects

Observe five cores in the actual final image: outer body, inner panel, two eyes, smile. Identify the structural edge separately from the bevel/refraction/fiber footprint. Use independent final-RGB segmentation with documented interpretation, or IDs from geometry that actually produces that final. Do not copy the SVG into observation fields. If core versus effect is ambiguous, leave the review pending rather than choosing whatever edge makes the numbers pass.

At 1024 pixels, [the working profile](matters-series-consistency.json) allows:

| Item | Working limit |
|---|---|
| Body and inner-panel center | Up to 6 px from source, Euclidean distance |
| Each eye and smile center | Up to 5 px from source |
| Body and inner-panel core dimensions | Up to 2% change in each axis |
| Facial core dimensions | Up to 12% change in each axis; contour overlap is also checked |
| Eye-spacing vector | Up to 6 px change |
| Face group relative to inner panel | Up to 5 px change |
| Local material extension | Up to 12 px around outer core, 8 px around inner/facial cores |

Material extension is measured independently; it never increases the center-shift allowance. Detached cast shadows and background are excluded from material footprints and reviewed separately. Core IoU additionally rejects local contour changes that matching centers and boxes can conceal. Numerical limits do not approve ugly, asymmetric, doubled or inconsistent-looking edges.

## Production

Prefer the full-image generative appearance the user likes. Supply the original SVG-derived guide every time, plus an accepted image as an appearance reference only. Fix canvas mapping, subject occupancy, face centers and spacing. Never use a preceding generation as the next geometry reference. Preserve the common orthographic/front view. Keep the user-selected background and avoid screenshot grids or app-template decorations in generation.

Inspect one candidate before making background/style siblings. Allow at most two targeted generation attempts for one unresolved placement issue per run; then report the measured outcome and retain the best candidate as unapproved. Do not continue open-ended retries or replace attractive material with a poor procedural render to satisfy this mode.

Compare every candidate at native scale and in a contact sheet at 64 and 128 pixels, using equal canvas size and placement without per-image auto-fit. Include the source guide and available approved series members; if no members are approved, label the source comparison as such. Check apparent body size, lobe/notch placement, eye baseline, eye spacing and smile placement. This visual check is mandatory even if numerical limits pass.

## Executable contract

Keep `schema_version: "2.0"`, the same source/absolute baseline and normal color/SHA evidence. Add to the new contract:

```json
{
  "acceptance_mode": "series_consistency",
  "acceptance_authorization": {
    "user_statement": "允许边缘适当超出，但位置不要偏得太离谱，保持系列轮廓一致。",
    "numeric_limits_selected_by": "assistant; working defaults"
  },
  "series_policy": {"path": "series-policy.json", "sha256": "actual SHA-256"}
}
```

Copy the bundled profile unchanged to `series-policy.json`. Each region's `observed_mask` represents its independently observed core. Also provide a `material_effects_mask` artifact (L mode, same canvas; zero mask only when reviewed as no separate effect), and bind its SHA in region evidence as `material_effects_mask_sha256`. Evidence must explain `core_definition`. Include core and effect edges in the final overlay.

The visual review additionally requires `series_preview_sizes: [64,128]`, a `series_contact_sheet` artifact and `series_consistency: {"status":"PASS", "notes":"actual observations"}`. Use the existing `workflow.py preflight/validate/package` commands. Missing mode retains historical exact checks. A series pass must never be described as pixel-exact geometry.
