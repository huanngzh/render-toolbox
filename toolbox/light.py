import os

import bpy
from mathutils import Vector


def set_env_map(env_path: str):
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    else:
        world.use_nodes = True
        world.node_tree.nodes.clear()

    env_texture_node = world.node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    env_texture_node.location = (0, 0)

    bg_node = world.node_tree.nodes.new(type="ShaderNodeBackground")
    bg_node.location = (400, 0)

    output_node = world.node_tree.nodes.new(type="ShaderNodeOutputWorld")
    output_node.location = (800, 0)

    links = world.node_tree.links
    links.new(env_texture_node.outputs["Color"], bg_node.inputs["Color"])
    links.new(bg_node.outputs["Background"], output_node.inputs["Surface"])

    bpy.ops.image.open(filepath=env_path)
    env_texture_node.image = bpy.data.images.get(os.path.basename(env_path))


def set_global_light(env_light: float = 0.5):
    world_tree = bpy.context.scene.world.node_tree
    back_node = world_tree.nodes["Background"]
    back_node.inputs["Color"].default_value = Vector(
        [env_light, env_light, env_light, 1.0]
    )
    back_node.inputs["Strength"].default_value = 1.0
