# Regional material and construction choices

Use for an existing logo series when a user supplies a style reference or changes a region's color/depth. References supply appearance; the original SVG supplies the outer contour, inner boundary, eyes and smile. Keep the latest explicit user choice ahead of inferred reference construction. Do not make one style's colors a permanent series default.

## Interpret the requested regions before generation

Record the following in the new task contract; use a concise implementation statement instead of asking again when the intent is clear.

| User request | Construction to preserve or change |
|---|---|
| “此风格” | Apply the new palette, material and lighting to the current mark. Preserve its geometry and relevant explicit filled/open decisions. Do not copy the reference's letters, star, app-tile shape, grid or labels. |
| “不要镂空” | Keep the central region as a continuous opaque surface. Do not silently return to the open-frame variant. If the instruction names another region, apply it to that region. |
| “中间用顶上那个颜色” | Identify the referenced swatch and assign it to the central panel. State the interpretation, such as “顶部银白金属”. Retain unrelated colors; if facial contrast needs adjustment, describe that choice. |
| “中间白色，五官镂空” | White central plate over the chosen backing, with the original two eyes and smile cut through that plate. Show the backing through the apertures with restrained inward edge/shadow cues. Do not substitute raised white pieces, painted shapes or an entirely empty center. |
| Raised versus recessed face revision | Change the declared region roles and layer stack in a new `depth_revision` task. Keep all original XY paths and masks. |
| Transparent background | Use the requested generated transparency and inspect its actual alpha. A white background or checkerboard is not transparency. |

A cutout needs an explicit backing: the existing colored layer, an empty opening or another user-selected material. The color visible through a hole is not a new raised facial piece. Keep aperture, inward wall and visible floor separate in evidence; a color mask does not prove all three surfaces.

## Efficient production loop

1. Reuse the original SVG, full-canvas guide and five masks only after checking their frozen hashes. Create a fresh material/construction contract. Do not inherit an old final, PASS review, output filename, material description or absolute smoke-test path by copying a whole previous task.
2. Provide the original guide plus the clean style reference. An existing candidate can supply retained appearance for a correction, but it never replaces the guide. A short prompt with explicit image roles, regional assignments and framing is preferable to accumulating contradictory corrections.
3. Inspect one candidate before siblings. Check appearance, filled/open state and actual facial placement. For a failure, give a measured correction in normalized final-canvas pixels. Follow the retry limit in [series-consistency.md](series-consistency.md); do not spend indefinitely on unchanged prompts.
4. Normalize the entire canvas once to the target export size, handle color explicitly, and inspect the exact saved file. If an opaque image was requested but generation returns alpha, composite onto the declared background before measuring; do not mistake the tool's black transparency display for the requested background. Preserve alpha for a transparent delivery.
5. Observe all five regions from that final RGB; compare source/core/effect overlays at native scale and 64/128 pixels. Bind evidence to the exact export and use `workflow.py validate` then `package`. A useful style draft is still unapproved when a required region is missing or fails.

## Reviewed example: white panel with gradient apertures

The 2026-09-24 Matters example uses a blue/violet/orange/yellow gradient base, a white bowed-square plate, and two oval plus one smile aperture revealing that base. This is a recipe and an acceptance example, not a new geometry reference or a mandate to use these colors for other styles.

- Source SVG SHA-256: `a38a29edf2a354456593eb2b8178f2ecec4ef15cd69d30629679832882429aa2`.
- Reviewed 1024 sRGB export SHA-256: `ec3f4bf84ea11a62deb74c0cca9f1f8f833078b606b9f52837f36db5f7925df1`.
- The unchanged series profile passed all five regions, relative facial layout, effect bounds and native/64/128 visual review. `validate` and `package` returned `DELIVERY_READY`; this is bounded series consistency, not pixel-exact or independent 3D certification.
- At the selected observation settings, center errors were approximately 0.49 px outer, 1.09 px inner, 0.75 px left eye, 0.47 px right eye and 0.21 px smile. These measurements belong only to the named export.

The example's first pure-chroma segmentation disconnected a muted, low-chroma section of the actual frame. That is a failed observation method, not permission to fill the gap with the SVG. After inspecting the RGB, the observation combined chroma greater than 24 with mean RGB below 210; sensitivity cutoffs 200 and 220 also passed. The faint effect footprint used chroma greater than 12 or mean RGB below 230. Connected regions were labeled by their observed spatial arrangement; the white panel was recovered as the frame's enclosed region. No source mask was pasted into an observed mask or the output.

Those thresholds are specific to this near-neutral white background and colorful material. Do not reuse them on metal, glass, foliage or another background. First verify that observed masks follow visible boundaries, document any segmentation-method change and retain failed attempts. Never select thresholds by whether they produce a passing score, loosen the geometry policy, or treat a source overlay alone as independent measurement.
