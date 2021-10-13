from vispy.scene.visuals import create_visual_node
from vispy.visuals import MeshVisual

from .clipping_planes_mixin import ClippingPlanesMixin

Mesh = create_visual_node(MeshVisual)


class SurfaceVisual(ClippingPlanesMixin, Mesh):
    """
    Surface vispy visual with clipping plane functionality
    """
