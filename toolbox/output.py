import math
import os
from typing import List, Optional

import bpy
import mathutils

from .util import get_local2world_mat


def set_color_output(
    width: int,
    height: int,
    output_dir: Optional[str] = "",
    file_prefix: str = "render_",
):
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "16"
    scene.render.film_transparent = True
    scene.render.filepath = os.path.join(output_dir, file_prefix)


def enable_normals_output(output_dir: Optional[str] = "", file_prefix: str = "normal_"):
    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree

    if "Render Layers" not in tree.nodes:
        rl = tree.nodes.new("CompositorNodeRLayers")
    else:
        rl = tree.nodes["Render Layers"]
    bpy.context.view_layer.use_pass_normal = True
    bpy.context.scene.render.use_compositing = True

    separate_rgba = tree.nodes.new("CompositorNodeSepRGBA")
    space_between_nodes_x = 200
    space_between_nodes_y = -300
    separate_rgba.location.x = space_between_nodes_x
    separate_rgba.location.y = space_between_nodes_y
    tree.links.new(rl.outputs["Normal"], separate_rgba.inputs["Image"])

    combine_rgba = tree.nodes.new("CompositorNodeCombRGBA")
    combine_rgba.location.x = space_between_nodes_x * 14

    c_channels = ["R", "G", "B"]
    offset = space_between_nodes_x * 2
    multiplication_values: List[List[bpy.types.Node]] = [[], [], []]
    channel_results = {}
    for row_index, channel in enumerate(c_channels):
        # matrix multiplication
        mulitpliers = []
        for column in range(3):
            multiply = tree.nodes.new("CompositorNodeMath")
            multiply.operation = "MULTIPLY"
            # setting at the end for all frames
            multiply.inputs[1].default_value = 0
            multiply.location.x = column * space_between_nodes_x + offset
            multiply.location.y = row_index * space_between_nodes_y
            tree.links.new(
                separate_rgba.outputs[c_channels[column]], multiply.inputs[0]
            )
            mulitpliers.append(multiply)
            multiplication_values[row_index].append(multiply)

        first_add = tree.nodes.new("CompositorNodeMath")
        first_add.operation = "ADD"
        first_add.location.x = space_between_nodes_x * 5 + offset
        first_add.location.y = row_index * space_between_nodes_y
        tree.links.new(mulitpliers[0].outputs["Value"], first_add.inputs[0])
        tree.links.new(mulitpliers[1].outputs["Value"], first_add.inputs[1])

        second_add = tree.nodes.new("CompositorNodeMath")
        second_add.operation = "ADD"
        second_add.location.x = space_between_nodes_x * 6 + offset
        second_add.location.y = row_index * space_between_nodes_y
        tree.links.new(first_add.outputs["Value"], second_add.inputs[0])
        tree.links.new(mulitpliers[2].outputs["Value"], second_add.inputs[1])

        channel_results[channel] = second_add

    rot_around_x_axis = mathutils.Matrix.Rotation(math.radians(-90.0), 4, "X")
    for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end):
        bpy.context.scene.frame_set(frame)
        used_rotation_matrix = (
            get_local2world_mat(bpy.context.scene.camera) @ rot_around_x_axis
        )
        for row_index in range(3):
            for column_index in range(3):
                current_multiply = multiplication_values[row_index][column_index]
                current_multiply.inputs[1].default_value = used_rotation_matrix[
                    column_index
                ][row_index]
                current_multiply.inputs[1].keyframe_insert(
                    data_path="default_value", frame=frame
                )

    offset = 8 * space_between_nodes_x
    for index, channel in enumerate(c_channels):
        multiply = tree.nodes.new("CompositorNodeMath")
        multiply.operation = "MULTIPLY"
        multiply.location.x = space_between_nodes_x * 2 + offset
        multiply.location.y = index * space_between_nodes_y
        tree.links.new(channel_results[channel].outputs["Value"], multiply.inputs[0])
        multiply.inputs[1].default_value = 0.5
        if channel == "G":
            multiply.inputs[1].default_value = -0.5
        add = tree.nodes.new("CompositorNodeMath")
        add.operation = "ADD"
        add.location.x = space_between_nodes_x * 3 + offset
        add.location.y = index * space_between_nodes_y
        tree.links.new(multiply.outputs["Value"], add.inputs[0])
        add.inputs[1].default_value = 0.5
        output_channel = channel
        if channel == "G":
            output_channel = "B"
        elif channel == "B":
            output_channel = "G"
        tree.links.new(add.outputs["Value"], combine_rgba.inputs[output_channel])

    normal_file_output = tree.nodes.new("CompositorNodeOutputFile")
    normal_file_output.base_path = output_dir
    normal_file_output.format.file_format = "OPEN_EXR"
    normal_file_output.format.color_mode = "RGBA"
    normal_file_output.format.color_depth = "32"
    normal_file_output.location.x = space_between_nodes_x * 15
    normal_file_output.file_slots.values()[0].path = file_prefix
    tree.links.new(combine_rgba.outputs["Image"], normal_file_output.inputs["Image"])


def enable_depth_output(output_dir: Optional[str] = "", file_prefix: str = "depth_"):
    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree
    links = tree.links

    if "Render Layers" not in tree.nodes:
        rl = tree.nodes.new("CompositorNodeRLayers")
    else:
        rl = tree.nodes["Render Layers"]
    bpy.context.view_layer.use_pass_z = True

    depth_output = tree.nodes.new("CompositorNodeOutputFile")
    depth_output.base_path = output_dir
    depth_output.name = "DepthOutput"
    depth_output.format.file_format = "OPEN_EXR"
    depth_output.format.color_depth = "32"
    depth_output.file_slots.values()[0].path = file_prefix

    links.new(rl.outputs["Depth"], depth_output.inputs["Image"])


def enable_albedo_output(output_dir: Optional[str] = "", file_prefix: str = "albedo_"):
    bpy.context.scene.render.use_compositing = True
    bpy.context.scene.use_nodes = True

    tree = bpy.context.scene.node_tree

    if "Render Layers" not in tree.nodes:
        rl = tree.nodes.new("CompositorNodeRLayers")
    else:
        rl = tree.nodes["Render Layers"]
    bpy.context.view_layer.use_pass_diffuse_color = True

    alpha_albedo = tree.nodes.new(type="CompositorNodeSetAlpha")
    tree.links.new(rl.outputs["DiffCol"], alpha_albedo.inputs["Image"])
    tree.links.new(rl.outputs["Alpha"], alpha_albedo.inputs["Alpha"])

    albedo_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
    albedo_file_output.base_path = output_dir
    albedo_file_output.file_slots[0].use_node_format = True
    albedo_file_output.format.file_format = "PNG"
    albedo_file_output.format.color_mode = "RGBA"
    albedo_file_output.format.color_depth = "16"
    albedo_file_output.file_slots.values()[0].path = file_prefix

    tree.links.new(alpha_albedo.outputs["Image"], albedo_file_output.inputs[0])


def enable_pbr_output(output_dir, attr_name, color_mode="RGBA", file_prefix: str = ""):
    if file_prefix == "":
        file_prefix = attr_name.lower().replace(" ", "-") + "_"

    for material in bpy.data.materials:
        material.use_nodes = True
        node_tree = material.node_tree
        nodes = node_tree.nodes
        roughness_input = nodes["Principled BSDF"].inputs[attr_name]
        if roughness_input.is_linked:
            linked_node = roughness_input.links[0].from_node
            linked_socket = roughness_input.links[0].from_socket

            aov_output = nodes.new("ShaderNodeOutputAOV")
            aov_output.name = attr_name
            node_tree.links.new(linked_socket, aov_output.inputs[0])

        else:
            fixed_roughness = roughness_input.default_value
            if isinstance(fixed_roughness, float):
                roughness_value = nodes.new("ShaderNodeValue")
                input_idx = 1
            else:
                roughness_value = nodes.new("ShaderNodeRGB")
                input_idx = 0

            roughness_value.outputs[0].default_value = fixed_roughness

            aov_output = nodes.new("ShaderNodeOutputAOV")
            aov_output.name = attr_name
            node_tree.links.new(roughness_value.outputs[0], aov_output.inputs[0])

    tree = bpy.context.scene.node_tree
    links = tree.links
    if "Render Layers" not in tree.nodes:
        rl = tree.nodes.new("CompositorNodeRLayers")
    else:
        rl = tree.nodes["Render Layers"]

    roughness_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
    roughness_file_output.base_path = output_dir
    roughness_file_output.file_slots[0].use_node_format = True
    roughness_file_output.format.file_format = "PNG"
    roughness_file_output.format.color_mode = color_mode
    roughness_file_output.format.color_depth = "16"
    roughness_file_output.file_slots.values()[0].path = file_prefix

    bpy.ops.scene.view_layer_add_aov()
    bpy.context.scene.view_layers["ViewLayer"].active_aov.name = attr_name
    roughness_alpha = tree.nodes.new(type="CompositorNodeSetAlpha")
    tree.links.new(rl.outputs[attr_name], roughness_alpha.inputs["Image"])
    tree.links.new(rl.outputs["Alpha"], roughness_alpha.inputs["Alpha"])

    links.new(roughness_alpha.outputs["Image"], roughness_file_output.inputs["Image"])
