from ...layers.utils.layer_utils import register_layer_action
from ...utils.translations import trans
from ..labels.labels import Labels
from .image import Image


def register_image_base_action(description):
    return register_layer_action(Image, description)(
        register_layer_action(Labels, description)
    )


@register_image_base_action(
    trans._("Cycle through axis aligned plane orientations")
)
def cycle_through_plane_orientations(layer):
    layer.plane.cycle_orientation()


@register_image_base_action(
    trans._("Align plane normal to axis 0 in data coordinates.")
)
def align_plane_axis_0(layer):
    layer.plane.align_normal_to_axis(0)


@register_image_base_action(
    trans._("Align plane normal to axis 1 in data coordinates.")
)
def align_plane_axis_1(layer):
    layer.plane.align_normal_to_axis(1)


@register_image_base_action(
    trans._("Align plane normal to axis 2 in data coordinates.")
)
def align_plane_axis_2(layer):
    layer.plane.align_normal_to_axis(2)


@register_image_base_action(
    trans._("Align plane normal to its most similar axis in data coordinates")
)
def align_plane_to_most_similar_axis(layer):
    layer.plane.align_normal_to_nearest_axis()
