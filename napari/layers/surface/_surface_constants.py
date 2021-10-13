from enum import auto

from ...utils.misc import StringEnum
from ...utils.translations import trans


class Shading(StringEnum):
    """Shading: Shading mode for the surface.

    Selects a preset shading mode in vispy that determines how
    color is computed in the scene.
    See also: https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/glShadeModel.xml
            Shading.NONE
                Computed color is interpreted as input color, unaffected by
                lighting. Corresponds to shading='none'.
            Shading.FLAT
                Computed colours are the color at a specific vertex for each
                primitive in the mesh. Corresponds to shading='flat'.
            Shading.SMOOTH
                Computed colors are interpolated between vertices for each
                primitive in the mesh. Corresponds to shading='smooth'
    """

    NONE = auto()
    FLAT = auto()
    SMOOTH = auto()


SHADING_TRANSLATION = {
    trans._("none"): Shading.NONE,
    trans._("flat"): Shading.FLAT,
    trans._("smooth"): Shading.SMOOTH,
}


class Wireframe(StringEnum):
    """Wireframe: Wireframe mode for the surface.

    Selects a preset wireframe mode in vispy.
            Wireframe.NONE
                No wireframe on the surface.
            Wireframe.OVERLAY
                Wireframe and surface faces are both drawn.
            Wireframe.WIREFRAME_ONLY
                Only the wireframe of the surface is shown.
    """

    NONE = auto()
    OVERLAY = auto()
    WIREFRAME_ONLY = auto()


WIREFRAME_TRANSLATION = {
    trans._("none"): Wireframe.NONE,
    trans._("overlay"): Wireframe.OVERLAY,
    trans._("wireframe_only"): Wireframe.WIREFRAME_ONLY,
}
