from enum import auto
from ...utils.misc import StringEnum


class Shader(StringEnum):
    """Shader: base shader for rendering

    Selects a preset shader for rendering
            * volume: render an entire volume.
            * plane: render an arbitrary plane through a volume.
    """

    VOLUME = auto()
    PLANE = auto()