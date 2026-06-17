# NOTE: bl_info removed — blender_manifest.toml is the single source of
# metadata for Blender 4.2+ extensions.

from . import dependencies
from . import height_map_tools


def register():
    dependencies.register()
    height_map_tools.register()


def unregister():
    height_map_tools.unregister()
    dependencies.unregister()


if __name__ == "__main__":
    register()
