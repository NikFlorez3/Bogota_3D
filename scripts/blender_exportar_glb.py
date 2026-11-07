"""
Procesa el MDT 2025 de Bogotá en Blender y lo exporta para el visor web.
Ejecutado por el agente (OpenCode) mediante la herramienta MCP `execute_blender_code`.

- Importa bogota_3d_completo.glb y lo nombra MDT_2025_Bogota.
- Aplica sombreado suave y un material Principled BSDF mate.
- Guarda el proyecto .blend.
- Exporta bogota_3d_blender.glb (glTF binario, +Y arriba, con normales, sin Draco).
No mueve, no escala ni modifica la geometría: se conserva la georreferenciación
(x = E - 4.870.000, z = -(N - 2.046.000) en glTF; elevación real en m s.n.m.).
"""
import bpy, os, mathutils

src = r"C:\Users\angel\Documents\Bogota_3D\entrega_github\bogota_3d_completo.glb"
out = r"C:\Users\angel\Documents\Bogota_3D\entrega_github\bogota_3d_blender.glb"
blend = r"C:\Users\angel\Documents\Bogota_3D\blender\bogota_3d.blend"

antes = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=src)
obj = [o for o in bpy.data.objects if o not in antes and o.type == 'MESH'][0]
obj.name = "MDT_2025_Bogota"
me = obj.data
me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
me.update()

mat = bpy.data.materials.new("Terreno_MDT_2025")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.667, 0.792, 0.627, 1)
bsdf.inputs["Roughness"].default_value = 1.0
bsdf.inputs["Metallic"].default_value = 0.0
me.materials.clear(); me.materials.append(mat)

os.makedirs(os.path.dirname(blend), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=blend, copy=True)

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True,
    export_yup=True, export_normals=True, export_draco_mesh_compression_enable=False)

bb = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
print("Objeto:", obj.name, "| vertices:", len(me.vertices))
print("BBox X:", round(min(v.x for v in bb)), "a", round(max(v.x for v in bb)))
print("BBox Y:", round(min(v.y for v in bb)), "a", round(max(v.y for v in bb)))
print("BBox Z (elev):", round(min(v.z for v in bb), 1), "a", round(max(v.z for v in bb), 1))
print("GLB:", out, round(os.path.getsize(out) / 1048576, 1), "MB")
