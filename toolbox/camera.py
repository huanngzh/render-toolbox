import math
from typing import List, Tuple

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector


def init_camera(camera_lens: int = 35, camera_sensor_width: int = 32):
    bpy.ops.object.camera_add(location=(0, 0, 0))
    camera = bpy.context.object
    camera.data.lens = camera_lens
    camera.data.sensor_width = camera_sensor_width
    bpy.context.scene.camera = camera

    return camera


def get_camera_positions_on_sphere(
    center: Tuple[float, float, float],
    radius: float,
    elevations: List[float],
    num_per_layer: int,
):
    points, mats, elevation_t, azimuth_t = [], [], [], []

    elevation_deg = elevations
    elevation = np.deg2rad(elevation_deg)
    azimuth_deg = np.linspace(0, 360, num_per_layer + 1)[:-1]
    azimuth_deg = azimuth_deg % 360
    azimuth = np.deg2rad(azimuth_deg)

    for theta in azimuth:
        for _phi in elevation:
            phi = 0.5 * math.pi - _phi
            elevation_t.append(_phi)
            azimuth_t.append(theta)

            r = radius
            x = center[0] + r * math.sin(phi) * math.cos(theta)
            y = center[1] + r * math.sin(phi) * math.sin(theta)
            z = center[2] + r * math.cos(phi)
            cam_pos = Vector((x, y, z))
            points.append(cam_pos)

            center = Vector(center)
            rotation_euler = (center - cam_pos).to_track_quat("-Z", "Y").to_euler()
            cam_matrix = build_transformation_mat(cam_pos, rotation_euler)
            mats.append(cam_matrix)

    return points, mats, elevation_t, azimuth_t


def add_camera(cam2world_matrix: Matrix) -> int:
    if not isinstance(cam2world_matrix, Matrix):
        cam2world_matrix = Matrix(cam2world_matrix)

    cam_ob = bpy.context.scene.camera
    cam_ob.matrix_world = cam2world_matrix

    frame = bpy.context.scene.frame_end
    if bpy.context.scene.frame_end < frame + 1:
        bpy.context.scene.frame_end = frame + 1

    cam_ob.keyframe_insert(data_path="location", frame=frame)
    cam_ob.keyframe_insert(data_path="rotation_euler", frame=frame)
    return frame


def build_transformation_mat(translation, rotation) -> np.ndarray:
    """Build a transformation matrix from translation and rotation parts.

    :param translation: A (3,) vector representing the translation part.
    :param rotation: A 3x3 rotation matrix or Euler angles of shape (3,).
    :return: The 4x4 transformation matrix.
    """
    translation = np.array(translation)
    rotation = np.array(rotation)

    mat = np.eye(4)
    if translation.shape[0] == 3:
        mat[:3, 3] = translation
    else:
        raise RuntimeError(
            f"Translation has invalid shape: {translation.shape}. Must be (3,) or (3,1) vector."
        )
    if rotation.shape == (3, 3):
        mat[:3, :3] = rotation
    elif rotation.shape[0] == 3:
        mat[:3, :3] = np.array(Euler(rotation).to_matrix())
    else:
        raise RuntimeError(
            f"Rotation has invalid shape: {rotation.shape}. Must be rotation matrix of shape "
            f"(3,3) or Euler angles of shape (3,) or (3,1)."
        )

    return mat
