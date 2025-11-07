from setuptools import setup, find_packages

setup(
    name="LaserCAD",
    version="1.2.0",
    packages=find_packages(include=["LaserCAD", "LaserCAD.*"]),
)