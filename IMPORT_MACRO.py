import sys
import importlib

if rf"E:\Martin\GitHub\LaserCAD\venv\Lib\site-packages" not in sys.path:
	sys.path.append(rf"E:\Martin\GitHub\LaserCAD\LaserCAD")
	sys.path.append(rf"E:\Martin\GitHub\LaserCAD\venv\Lib\site-packages")
	sys.path.append(rf"E:\Martin\GitHub\LaserCAD")

import LaserCAD

def reload_package(package):
    """Reload all modules belonging to a package."""

    package_name = package.__name__

    # Find all loaded submodules
    modules = [
        name for name in sys.modules
        if name == package_name or name.startswith(package_name + ".")
    ]

    # Reload submodules first, then the main package
    modules.sort(key=lambda name: name.count("."), reverse=True)

    for name in modules:
        importlib.reload(sys.modules[name])

reload_package(LaserCAD)

print("(Re)loaded LaserCAD")