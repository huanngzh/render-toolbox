# Render Toolbox
Blender toolbox for rendering 3D scenes.

Tested in Blender 3.5.1 and Python 3.9.

## 📽️ Example

## 🔨 Quick Start
First, get your blender python env path to install necessary packages into blender python correctly. Run the following command in your Blender Python Console.
```Bash
>>> import sys
>>> print(sys.executable)
/opt/blender-3.5.1/3.5/python/bin/python3.10
```

Then install packages:
```Bash
# Update the actual output you get to the following command 
/opt/blender-3.5.1/3.5/python/bin/python3.10 -m pip install -r requirements.txt
```

Run the example script to render:
```Bash
blender -b -P example.py
```

## 📖 Tutorial

**Create a scene handler** to handle most rendering configuration operations.
```Python
scener = SceneHandler()
```

**Initialize the render engine.**
You can select *BLENDER_EEVEE* or *BLENDER_EEVEE* as your rendering engine. The former is faster.
```Python
scener.init_render_engine("BLENDER_EEVEE")
# Or
scener.init_render_engine("CYCLES")
```

**Initialize the intrinsics of camera.**
Modify the camera lens and sensor width as you need.
```Python
cam_default = scener.init_camera(camera_lens, camera_sensor_width)
```

**Import object.**
Now formats including object with color on vertex(exported by [trimesh](https://github.com/mikedh/trimesh)), object with mtl, glb are supported. You can use `type` to select one of it.
```Python
scener.import_object(type="vertex_colored", filepath="**.obj")
# Or import object with mtl. You may need to specify the forward-axis and up-axis, with "Y" and "Z" are default values.
scener.import_object(type="obj", filepath="**.obj")
# Or import glb
scener.import_object(type="glb", filepath="**.glb")
```

Other functions to process on the imported object.
```Python
# Modify the color into a single one
scener.modify_vertex_color(((0.52941, 0.80784, 0.92157))) # Sky blue

# Preprocess the objects, like using auto smooth and clear the animation
scener.preprocess_objs()

# Normalize the scene into a sphere
scener.normalize_scene(range=1.0)
```

**Set the environment light.**
You can set global light with a specified light intensity, or use an environment map.
```Python
scener.set_env_light(env_light=1.0)
# Or use an environment map
scener.set_env_light(env_path="**.exr")
```

**Prepare camera layout and add to the scene.**
Now sphere layout is supported. Specify the center (lookat), radius (camera distance from the center), elevations, num_per_layer.
```Python
# The following code will create a circle of cameras at elevation 30 above the object.
distance = 1.5
cam_positions, cam_mats, eles, azis = get_camera_positions_on_sphere(
    center=(0, 0, 0), radius=distance, elevations=[30], num_per_layer=120
)
for camera_matrix in cam_mats:
    scener.add_camera(camera_matrix)
```

**Rendering output setting.**
Render color, normal, depth, albedo or pbr maps. Note that the export works well or bad may depend on whether the object has corresponding maps.
```Python
scener.set_output(
    output_dir="outputs",
    width=512,
    height=512,
    output_types=["color"], # "color", "normal", "depth", "albedo", "pbr"
)
```

**Perform rendering.**
```Python
scener.render()
```

You can also export the meta info of the cameras, or save the rendered images to a video. Please refer to [example.py](example.py) for details.

## Other Statements
Source of model assets:
- vertex_colored.obj generated by [EpiDiff](https://huanngzh.github.io/EpiDiff/).
- Mario.glb generated by [Tripo](https://www.tripo3d.ai/).
- Android_Figure_Panda comes from [Google Scanned Objects](https://app.gazebosim.org/GoogleResearch/fuel/collections/Scanned%20Objects%20by%20Google%20Research).