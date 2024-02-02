import json
import os
import sys

import imageio.v2 as imageio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from toolbox import SceneHandler, rgba_to_rgb
from toolbox.camera import get_camera_positions_on_sphere

scener = SceneHandler()

# Initialize the render engine
scener.init_render_engine("BLENDER_EEVEE")

# Initialize the camera
cam_default = scener.init_camera()

# Import the object, preprocess it and normalize the scene into [-1, 1]
scener.import_object(
    "vertex_colored",
    "assets/objects/vertex_colored.obj",
    # vertex_color=(0.52941, 0.80784, 0.92157),
)
scener.preprocess_objs()
scener.normalize_scene(range=1.0)

# Set the environment light
# scener.set_env_light(env_light=1.0)
scener.set_env_light(env_path="assets/env_textures/brown_photostudio_02_1k.exr")

# Prepare camera layout and add to the scene
distance = 1.5
cam_positions, cam_mats, eles, azis = get_camera_positions_on_sphere(
    center=(0, 0, 0), radius=distance, elevations=[30], num_per_layer=120
)
for camera_matrix in cam_mats:
    scener.add_camera(camera_matrix)

# Set rendering output and render
output_dir = "outputs"
width, height = 512, 512
scener.set_output(
    output_dir=output_dir,
    width=width,
    height=height,
    output_types=["color"],
)
scener.render()

# Prepare and save meta info
fov_x = cam_default.data.angle_x
meta_info = {
    "distance": distance,
    "fov_x": fov_x,
    "width": 512,
    "height": 512,
    "locations": [],
}
for i in range(len(cam_positions)):
    index = "{0:04d}".format(i)
    meta_info["locations"].append(
        {
            "index": index,
            "elevation": eles[i],
            "azimuth": azis[i],
            "transform_matrix": cam_mats[i].tolist(),
        }
    )
with open(os.path.join(output_dir, "meta.json"), "w") as f:
    json.dump(meta_info, f, indent=4)

# Save rendered color images to video
rgb_images = []
for f in sorted(os.listdir(output_dir)):
    if f.startswith("render_"):
        img = imageio.imread(os.path.join(output_dir, f))
        rgb_images.append(rgba_to_rgb(img))
video_path = os.path.join(output_dir, "render.mp4")
imageio.mimsave(video_path, rgb_images, fps=24)
print(f"Video saved to {video_path}")
