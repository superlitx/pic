from pathlib import Path

import bpy
from mathutils import Vector


BUNDLE = Path(__file__).resolve().parents[1]
MODEL_OUT = BUNDLE / "models"
PROOF_OUT = BUNDLE / "proofs"
SVG = BUNDLE / "assets/matters.svg"
CANVAS_UNITS = 6.4
MARK_UNITS = 4.8


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name, rgba, roughness=0.72):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = rgba
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return mat


def import_source():
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=str(SVG))
    curves = [obj for obj in bpy.data.objects if obj not in before and obj.type == "CURVE"]
    if not curves:
        raise RuntimeError("SVG import produced no curve")
    source = min(curves, key=lambda obj: obj.dimensions.x * obj.dimensions.y)
    for obj in curves:
        if obj != source:
            bpy.data.objects.remove(obj, do_unlink=True)
    native_mark = max(source.dimensions.x, source.dimensions.y)
    scale = MARK_UNITS / native_mark
    native_canvas = native_mark * 1024.0 / 768.0
    source.scale = (scale, scale, scale)
    source.location.x = -native_canvas * scale / 2.0
    source.location.y = -native_canvas * scale / 2.0
    source.name = "AUTHORITATIVE_SVG_ALL_SPLINES"
    source.hide_render = True
    source.hide_viewport = True
    if len(source.data.splines) != 5:
        raise RuntimeError(f"Expected five semantic splines, found {len(source.data.splines)}")
    return source


def part(source, name, indices, z, extrusion, bevel, mat, role):
    obj = source.copy()
    obj.data = source.data.copy()
    bpy.context.collection.objects.link(obj)
    obj.name = name
    for index in reversed(range(len(obj.data.splines))):
        if index not in indices:
            obj.data.splines.remove(obj.data.splines[index])
    obj.hide_render = False
    obj.hide_viewport = False
    obj.location.z = z
    obj.data.dimensions = "2D"
    obj.data.fill_mode = "BOTH"
    obj.data.resolution_u = 48
    svg_scale = abs(source.scale.x)
    obj.data.extrude = extrusion / svg_scale
    obj.data.bevel_depth = bevel / svg_scale
    obj.data.bevel_resolution = 8 if bevel else 0
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj["geometry_role"] = role
    obj["geometry_authority"] = str(SVG)
    obj["shared_canvas_transform"] = True
    return obj


def area_light(name, location, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector((0, 0, 0)) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    MODEL_OUT.mkdir(exist_ok=True)
    PROOF_OUT.mkdir(exist_ok=True)
    reset_scene()
    source = import_source()

    frame = material("ID frame", (0.82, 0.26, 0.07, 1.0))
    panel = material("ID recessed panel", (0.94, 0.72, 0.30, 1.0))
    features = material("ID raised features", (0.98, 0.46, 0.10, 1.0))
    floor_mat = material("Neutral floor", (0.055, 0.055, 0.055, 1.0), 0.9)

    # Side/depth geometry is deliberately allowed to project outside the cap.
    part(source, "Frame side and bevel", {0, 1}, 0.10, 0.12, 0.055, frame, "allowed_overflow")
    part(source, "Recessed panel body", {1}, 0.035, 0.055, 0.030, panel, "allowed_overflow")
    part(source, "Raised facial bodies", {2, 3, 4}, 0.19, 0.060, 0.030, features, "allowed_overflow")

    # These caps are the immutable front-face projection used for registration.
    part(source, "Frame exact front cap", {0, 1}, 0.34, 0.001, 0.0, frame, "locked_front_face")
    part(source, "Panel exact front cap", {1}, 0.15, 0.001, 0.0, panel, "locked_front_face")
    part(source, "Features exact front caps", {2, 3, 4}, 0.31, 0.001, 0.0, features, "locked_front_face")

    bpy.ops.mesh.primitive_plane_add(size=9.0, location=(0, 0, -0.20))
    floor = bpy.context.object
    floor.name = "Shadow receiver"
    floor.data.materials.append(floor_mat)
    floor["geometry_role"] = "background_and_contact_shadow"

    camera_data = bpy.data.cameras.new("Orthographic registration camera")
    camera = bpy.data.objects.new("Orthographic registration camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0, 0, 10)
    camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = CANVAS_UNITS
    bpy.context.scene.camera = camera

    area_light("Upper-left key", (-3.5, 4.0, 7.5), 850, 4.2)
    area_light("Right fill", (4.0, 0.5, 6.0), 420, 4.8)

    world = bpy.data.worlds.new("Constraint world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.035, 0.035, 0.035, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    bpy.context.scene.world = world

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.filepath = str(PROOF_OUT / "model-frontface-guide.png")
    bpy.ops.wm.save_as_mainfile(
        filepath=str(MODEL_OUT / "matters-frontface-constraint.blend")
    )
    bpy.ops.render.render(write_still=True)
    print(MODEL_OUT / "matters-frontface-constraint.blend")
    print(PROOF_OUT / "model-frontface-guide.png")


if __name__ == "__main__":
    main()
