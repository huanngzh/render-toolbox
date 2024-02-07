from typing import IO, Any, Dict, List, Optional, Set, Tuple, Union

import bpy
import numpy as np


def read_trimesh_obj(file_path):
    """Read a trimesh obj file.

    For example, the obj file may look like this:
    ```
    v 0.000000 0.000000 0.000000 0.52941 0.80784 0.92157
    v 0.000000 0.000000 1.000000 0.52941 0.80784 0.92157
    v 0.000000 1.000000 0.000000 0.52941 0.80784 0.92157
    f 1 2 3
    ```

    Args:
        file_path (str): The path to the obj file.

    Returns:
        Tuple[List[Tuple], List[Tuple], List[Tuple]]:
            A tuple containing the vertices, colors, and faces.
    """
    vertices, colors, faces = [], [], []
    with open(file_path, "r") as file:
        for line in file:
            parts = line.split()
            if len(parts) == 0:
                continue

            if parts[0] == "v" and len(parts) == 7:  # Vertex with color
                x, y, z = map(float, parts[1:4])
                r, g, b = map(float, parts[4:7])
                vertices.append((x, y, z))
                colors.append((r, g, b))  # Normalize colors

            elif parts[0] == "f" and len(parts) >= 4:  # Face
                face = [int(idx) - 1 for idx in parts[1:]]  # Adjust for 0-based index
                faces.append(tuple(face))

    return vertices, colors, faces


def import_vertex_colored_models(
    filepath: str, vertex_color: Optional[Tuple] = None
) -> bpy.types.Object:
    """Import vertex colored models (like exported obj from trimesh).

    Args:
        filepath (`str`): The local path to the obj file.
        vertex_color (`Tuple`, *optional*, defaults to None):
            color of the vertices. Set to None to use the color from the obj file.
            If specified, the color will be set to all vertices. Defaults to None.

    Returns:
        `bpy.types.Object`: The imported object.
    """
    # Read data from file
    try:
        vertices, colors, faces = read_trimesh_obj(filepath)
    except:
        return {"CANCELLED"}

    # Create a new mesh and object
    mesh = bpy.data.meshes.new(name="ColoredMesh")
    obj = bpy.data.objects.new("ColoredMeshObject", mesh)

    # Link the object to the scene
    bpy.context.collection.objects.link(obj)

    # Create vertices
    mesh.from_pydata(vertices, [], faces)

    # Create a vertex color layer
    color_layer = mesh.vertex_colors.new()

    # Assign colors to each vertex
    for poly in mesh.polygons:  # Iterate over all polygons
        for idx in poly.loop_indices:  # Iterate over all loop indices in the polygon
            loop = mesh.loops[idx]
            vertex_index = loop.vertex_index

            if vertex_color is not None:
                color_layer.data[idx].color = vertex_color + (1.0,)  # RGB + Alpha
            else:
                color_layer.data[idx].color = colors[vertex_index] + (1.0,)

    # Update mesh with new data
    mesh.update()

    # Ensure the mesh is linked to the object
    obj.data = mesh

    # Create a new material
    material = bpy.data.materials.new(name="VertexColorMaterial")

    # Use nodes for the material
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Clear all nodes to start clean
    for node in nodes:
        nodes.remove(node)

    # Create a Vertex Color node
    vertex_color_node = nodes.new(type="ShaderNodeVertexColor")
    vertex_color_node.layer_name = color_layer.name  # Use the name of your color layer

    # Create a Diffuse BSDF node
    diffuse_node = nodes.new(type="ShaderNodeBsdfDiffuse")

    # Create an Output node
    output_node = nodes.new(type="ShaderNodeOutputMaterial")

    # Link nodes
    material.node_tree.links.new(
        vertex_color_node.outputs["Color"], diffuse_node.inputs["Color"]
    )
    material.node_tree.links.new(
        diffuse_node.outputs["BSDF"], output_node.inputs["Surface"]
    )

    # Assign material to object
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

    return {"FINISHED"}


def modify_obj_vertex_color(obj: bpy.types.Object, color: Tuple):
    """Modify the vertex color of an object.

    Args:
        obj (bpy.types.Object): The object to modify.
        color (Tuple): The color to set.

    Returns:
        `bpy.types.Object`: The modified object.
    """
    mesh = obj.data

    # Create a vertex color layer
    color_layer = mesh.vertex_colors.new()

    # Assign colors to each vertex
    for poly in mesh.polygons:  # Iterate over all polygons
        for idx in poly.loop_indices:  # Iterate over all loop indices in the polygon
            color_layer.data[idx].color = color + (1.0,)  # RGB + Alpha

    # Update mesh with new data
    mesh.update()

    # Ensure the mesh is linked to the object
    obj.data = mesh

    # Create a new material
    material = bpy.data.materials.new(name="VertexColorMaterial")

    # Use nodes for the material
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Clear all nodes to start clean
    for node in nodes:
        nodes.remove(node)

    # Create a Vertex Color node
    vertex_color_node = nodes.new(type="ShaderNodeVertexColor")
    vertex_color_node.layer_name = color_layer.name  # Use the name of your color layer

    # Create a Diffuse BSDF node
    diffuse_node = nodes.new(type="ShaderNodeBsdfDiffuse")

    # Create an Output node
    output_node = nodes.new(type="ShaderNodeOutputMaterial")

    # Link nodes
    material.node_tree.links.new(
        vertex_color_node.outputs["Color"], diffuse_node.inputs["Color"]
    )
    material.node_tree.links.new(
        diffuse_node.outputs["BSDF"], output_node.inputs["Surface"]
    )

    # Assign material to object
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)

    return obj


def preprocess_obj(obj: bpy.types.Object, smooth_angle: float = 30.0):
    """Preprocess the object."""
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = np.deg2rad(smooth_angle)

    return obj
