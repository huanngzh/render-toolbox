import numpy as np


def get_local2world_mat(blender_obj) -> np.ndarray:
    """Returns the pose of the object in the form of a local2world matrix.
    :return: The 4x4 local2world matrix.
    """
    obj = blender_obj
    # Start with local2parent matrix (if obj has no parent, that equals local2world)
    matrix_world = obj.matrix_basis

    # Go up the scene graph along all parents
    while obj.parent is not None:
        # Add transformation to parent frame
        matrix_world = (
            obj.parent.matrix_basis @ obj.matrix_parent_inverse @ matrix_world
        )
        obj = obj.parent

    return np.array(matrix_world)


def rgba_to_rgb(rgba_image, bg_color=[255, 255, 255]):
    background = np.array(bg_color)

    # Separate the foreground and alpha
    foreground = rgba_image[..., :3]
    alpha = rgba_image[..., 3:]

    foreground = foreground.astype(float)
    background = background.astype(float)
    alpha = alpha.astype(float) / 255

    rgb_image = alpha * foreground + (1 - alpha) * background
    return rgb_image.astype(np.uint8)
