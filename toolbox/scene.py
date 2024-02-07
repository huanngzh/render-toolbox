import math
from typing import Literal, Optional, Tuple

import bpy
from mathutils import Vector

from .camera import add_camera, init_camera
from .engine import init_render_engine
from .light import set_env_map, set_global_light
from .object import (
    import_vertex_colored_models,
    modify_obj_vertex_color,
    preprocess_obj,
)
from .output import *


class SceneHandler:
    def __init__(self):
        self.clear_scene()

        # Prepare functions
        self.init_camera = init_camera
        self.add_camera = add_camera
        self.init_render_engine = init_render_engine

    @property
    def objects(self):
        return bpy.context.scene.objects

    @property
    def scene_meshes(self):
        return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]

    @property
    def data_meshes(self):
        return [obj for obj in bpy.data.objects if obj.type == "MESH"]

    @property
    def root_objects(self):
        for obj in bpy.context.scene.objects.values():
            if not obj.parent:
                yield obj

    @property
    def bbox(self):
        return self.get_scene_bbox()

    def set_env_light(self, env_path: Optional[str] = None, env_light: float = 1.0):
        if env_path is not None:
            set_env_map(env_path)
        else:
            set_global_light(env_light)

    def set_output(
        self,
        output_dir: str,
        width: int,
        height: int,
        output_types: [Literal["color", "normal", "depth", "albedo", "pbr"]],
    ):
        os.makedirs(output_dir, exist_ok=True)
        set_color_output(width, height, output_dir)

        if "normal" in output_types:
            enable_normals_output(output_dir)
        if "depth" in output_types:
            enable_depth_output(output_dir)
        if "albedo" in output_types:
            enable_albedo_output(output_dir)
        if "pbr" in output_types:
            enable_pbr_output(output_dir, attr_name="Roughness", color_mode="RGBA")
            enable_pbr_output(output_dir, attr_name="Base Color", color_mode="RGBA")
            enable_pbr_output(output_dir, attr_name="Metallic", color_mode="RGBA")

    def import_object(
        self,
        type: Literal["vertex_colored", "obj", "glb"],
        filepath: str,
        forward_axis: str = "Y",
        up_axis: str = "Z",
        vertex_color: Vector = None,
    ):
        if type == "vertex_colored":
            result = import_vertex_colored_models(filepath, vertex_color)
        elif type == "obj":
            base_name = os.path.basename(filepath)
            result = bpy.ops.wm.obj_import(
                filepath=filepath,
                directory=os.path.dirname(filepath),
                files=[{"name": base_name}],
                forward_axis=forward_axis,
                up_axis=up_axis,
            )
        elif type == "glb":
            result = bpy.ops.import_scene.gltf(filepath=filepath)
        else:
            raise ValueError(f"Unsupported object type: {type}")

        if result != {"FINISHED"}:
            raise Exception(f"Failed to import vrm: {result}")

    def modify_vertex_color(self, vertex_color: Tuple[float, float, float]):
        for obj in self.data_meshes:
            modify_obj_vertex_color(obj, vertex_color)

    def preprocess_objs(self):
        for obj in self.scene_meshes:
            preprocess_obj(obj)

        for obj in self.data_meshes:
            if obj.animation_data is not None:
                obj.animation_data_clear()

    def get_scene_bbox(self, single_obj=None, ignore_matrix=False):
        bbox_min = (math.inf,) * 3
        bbox_max = (-math.inf,) * 3

        meshes = self.scene_meshes if single_obj is None else [single_obj]
        if len(meshes) == 0:
            raise RuntimeError("No objects in scene to compute bounding box for")

        for obj in meshes:
            for coord in obj.bound_box:
                coord = Vector(coord)
                if not ignore_matrix:
                    coord = obj.matrix_world @ coord
                bbox_min = tuple(min(x, y) for x, y in zip(bbox_min, coord))
                bbox_max = tuple(max(x, y) for x, y in zip(bbox_max, coord))

        return Vector(bbox_min), Vector(bbox_max)

    def normalize_scene(self, range: float = 1.0):
        bbox_min, bbox_max = self.bbox
        scale = range / (bbox_max - bbox_min).length

        # Apply scale to objects
        for obj in self.root_objects:
            obj.scale = obj.scale * scale
        bpy.context.view_layer.update()

        # Recompute bounding box and translate to origin
        bbox_min, bbox_max = self.bbox
        offset = -(bbox_min + bbox_max) / 2
        for obj in self.root_objects:
            obj.matrix_world.translation += offset

        bpy.ops.object.select_all(action="DESELECT")

    def render(self):
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree

        if "Render Layers" not in tree.nodes:
            rl = tree.nodes.new("CompositorNodeRLayers")
        else:
            rl = tree.nodes["Render Layers"]
        if bpy.context.scene.frame_end != bpy.context.scene.frame_start:
            bpy.context.scene.frame_end -= 1
            bpy.ops.render.render(animation=True, write_still=True)
            bpy.context.scene.frame_end += 1
        else:
            raise RuntimeError(
                "No camera poses have been registered, therefore nothing can be rendered. A camera "
                "pose can be registered via bproc.camera.add_camera_pose()."
            )

    def clear_scene(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()
        bpy.context.scene.use_nodes = True

        node_tree = bpy.context.scene.node_tree
        # Clear all nodes
        for node in node_tree.nodes:
            node_tree.nodes.remove(node)

        # Reset keyframes
        bpy.context.scene.frame_start = 0
        bpy.context.scene.frame_end = 0
        for a in bpy.data.actions:
            bpy.data.actions.remove(a)
