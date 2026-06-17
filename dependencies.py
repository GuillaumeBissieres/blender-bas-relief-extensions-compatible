# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import bpy
import subprocess
import sys
import importlib

REQUIRED_PACKAGES = [
    ("numpy",       "numpy",                 ""),
    ("cv2",         "opencv-python-headless",""),
    ("PIL",         "Pillow",                ""),
    ("torch",       "torch",                 ""),
    ("torchvision", "torchvision",           ""),
]


def _check_package(import_name):
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False


def get_status():
    return [(pip, _check_package(imp)) for imp, pip, _ in REQUIRED_PACKAGES]


def all_installed():
    return all(ok for _, ok in get_status())


def install_package(pip_name, report_fn=None):
    python = sys.executable
    cmd = [python, "-m", "pip", "install", "--upgrade", pip_name]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            if report_fn:
                report_fn(f"✓ {pip_name} installed successfully")
            return True
        else:
            if report_fn:
                report_fn(f"✗ {pip_name} failed: {result.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        if report_fn:
            report_fn(f"✗ {pip_name} timed out")
        return False
    except Exception as e:
        if report_fn:
            report_fn(f"✗ {pip_name} error: {e}")
        return False


# -----------------------------------------------------------------------
# Operators
# -----------------------------------------------------------------------
class HEIGHTMAP_OT_InstallDependencies(bpy.types.Operator):
    bl_idname   = "heightmap.install_dependencies"
    bl_label    = "Install All Dependencies"
    bl_description = (
        "Download and install the required Python libraries "
        "(numpy, opencv-python-headless, Pillow, torch, torchvision). "
        "Requires an internet connection. torch is ~200 MB CPU version — "
        "this may take several minutes."
    )
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        def report_fn(msg):
            print(f"[Height Map Generator] {msg}")

        self.report({'INFO'}, "Installing dependencies… check the system console.")
        failed = []
        for imp_name, pip_name, _ in REQUIRED_PACKAGES:
            if _check_package(imp_name):
                report_fn(f"✓ {pip_name} already installed — skipped")
                continue
            ok = install_package(pip_name, report_fn)
            if not ok:
                failed.append(pip_name)

        if failed:
            self.report({'ERROR'},
                f"Some packages failed: {', '.join(failed)}. "
                "Check the system console for details.")
        else:
            self.report({'INFO'},
                "All dependencies installed! Restart Blender to activate.")
        return {'FINISHED'}


class HEIGHTMAP_OT_CheckDependencies(bpy.types.Operator):
    bl_idname   = "heightmap.check_dependencies"
    bl_label    = "Refresh Status"
    bl_description = "Check which required libraries are currently installed"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        status = get_status()
        lines  = [f"{'✓' if ok else '✗'} {pip}" for pip, ok in status]
        level  = 'INFO' if all(ok for _, ok in status) else 'WARNING'
        self.report({level}, " | ".join(lines))
        return {'FINISHED'}


# -----------------------------------------------------------------------
# Addon Preferences
# -----------------------------------------------------------------------
class HEIGHT_MAP_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout  = self.layout
        status  = get_status()
        all_ok  = all(ok for _, ok in status)

        box = layout.box()
        box.label(text="Height Map Generator — Required Libraries", icon='SCRIPT')

        col = box.column(align=True)
        for pip_name, ok in status:
            row = col.row()
            row.label(text=pip_name, icon='CHECKMARK' if ok else 'X')
            row.label(text="Installed" if ok else "Not found")

        layout.separator()

        if not all_ok:
            warn = layout.box()
            warn.label(text="Some libraries are missing.", icon='ERROR')
            warn.label(text="torch (~200 MB CPU) requires a stable internet connection.")
            layout.separator()
            col = layout.column()
            col.scale_y = 1.5
            col.operator("heightmap.install_dependencies",
                         text="Install All Dependencies", icon='IMPORT')
        else:
            layout.label(
                text="All dependencies are installed. Height Map Generator is ready.",
                icon='CHECKMARK')

        layout.separator()
        layout.operator("heightmap.check_dependencies",
                        text="Refresh Status", icon='FILE_REFRESH')
        layout.separator()
        layout.label(text="Third-party licenses:", icon='INFO')
        layout.label(text="numpy (BSD) • opencv-python (Apache 2.0) • Pillow (HPND)")
        layout.label(text="torch & torchvision (BSD 3-Clause, Meta Platforms)")
        layout.label(text="MiDaS model weights (MIT, Intel ISL) — downloaded at runtime")


# -----------------------------------------------------------------------
# Register
# -----------------------------------------------------------------------
classes = (
    HEIGHTMAP_OT_InstallDependencies,
    HEIGHTMAP_OT_CheckDependencies,
    HEIGHT_MAP_Preferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
