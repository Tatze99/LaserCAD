# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import sys

from LaserCAD.freecad_models import clear_doc, setview, freecad_da, model_mirror, add_to_composition
from LaserCAD.basic_optics import Mirror, Beam, Ray_Distribution, Composition, Component, inch, Curved_Mirror, Ray, Geom_Object
from LaserCAD.basic_optics import Grating, Opt_Element
import matplotlib.pyplot as plt
from LaserCAD.freecad_models.utils import thisfolder, load_STL
from LaserCAD.non_interactings import Crystal, LaserPointer, Camera
from LaserCAD.basic_optics import Composed_Mount,Unit_Mount,Lens,Post, export_to_TikZ, print_post_positions, ThinBeamsplitter
from copy import deepcopy
from LaserCAD.moduls import Polarization_Rotator

from A3_sketch_generalized import Newport_Mirror, Newport_Curved_Mirror, table, table2, Housing, Housing2, Cylindric_Crystal, rad, deg, Pump_bot, Pump_top, LiMgAS_crystal1, LiMgAS_crystal2


rotate_axis = np.pi
offset_axis = (950+110-15,500,20)

class Adapter_1inch(Composed_Mount):
  def __init__(self, angle=0):
    super().__init__()
    um = Unit_Mount()
    um.model = "1inch_adapter"
    um.path = thisfolder + "misc_meshes/"
    um.docking_obj.pos += (6,38,0) # from manual adjustments in FreeCAD
    um.is_horizontal = False
    um.draw_dict["color"] = (0.3,0.3,0.3)
    self.add(um)
    um.rotate(vec=um.normal, phi=angle*np.pi/180)
    self.add(Unit_Mount(model="Newport-9771-M"))
    self.add(Post())


"""
#####################################
Mach Zehnder Setup
#####################################
"""
focal_length_tele1 = -30
focal_length_tele2 = 400
x_deviation = -950
y_deviation = 180
total_deviation = np.sqrt(x_deviation**2 + y_deviation**2)
angle_of_incidence = np.arctan(y_deviation/x_deviation) * 180 / np.pi
angle_mach_zehnder = 35

beam = Beam(radius=0.8, angle=0)
beam.draw_dict["color"] = (0.0,1.0,0.0)
# beam.pos=[0,0,0]

Laser = LaserPointer(name="Laser Pointer 1")
Camera1 = Camera(name="Camera 1")
M1 = Newport_Mirror(name="M1", phi=180+50, aperture=25.4) # pump mirror 1
M1.set_mount(Adapter_1inch(angle=180))
M2 = Newport_Mirror(name="M2", phi=180-50-angle_of_incidence, aperture=2*25.4)
M3 = Newport_Mirror(name="M3", phi=-90)
M4 = Newport_Mirror(name="M4", phi=-90)
M5 = Newport_Mirror(name="M5", phi=180-2*angle_mach_zehnder-angle_of_incidence, aperture=25.4)
TFP1 = ThinBeamsplitter(transmission=True, angle_of_incidence=-angle_mach_zehnder, name="TFP1")
TFP1.aperture = 25.4*2
TFP1.set_mount(Composed_Mount(unit_model_list=["U200-A2K", "1inch_post"]))
TFP1.Mount.flip()

TFP2 = ThinBeamsplitter(transmission=False, angle_of_incidence=25+angle_of_incidence/2, name="TFP2")
TFP2.aperture = 25.4*2
TFP2.set_mount(Composed_Mount(unit_model_list=["U200-A2K", "1inch_post"]))


telelens1 = Lens(f=focal_length_tele1, name=f"telescope lens 1, f={focal_length_tele1}mm")
telelens1.aperture = 25.4*1
telelens1.set_mount_to_default()
telelens2 = Lens(f=focal_length_tele2, name=f"telescope lens 2, f={focal_length_tele2}mm")
telelens2.aperture = 25.4*2
telelens2.set_mount_to_default()


Setup = Composition(name="Mach Zehnder")
Setup.set_light_source(beam)
Setup.normal = (-x_deviation, -y_deviation,0)
Setup.pos += offset_axis
Setup.pos += (x_deviation, y_deviation,0)
Setup.add_on_axis(Laser)
Setup.propagate(200)
Setup.add_on_axis(telelens1)
Setup.propagate(focal_length_tele1+focal_length_tele2)
Setup.add_on_axis(telelens2)
Setup.propagate(200)
Setup.add_on_axis(TFP1)
Setup.propagate(total_deviation-(200+200+focal_length_tele1+focal_length_tele2))
Setup.propagate(170)
Setup.add_on_axis(M1)
Setup.propagate(240)
Setup.add_on_axis(TFP2)
Setup.propagate(50)
Setup.add_on_axis(M3)
Setup.propagate(240)
Setup.add_on_axis(M4)
Setup.propagate(400)
Setup.add_on_axis(Camera1)

Setup.compute_beams()
arm2_lightsource = TFP1._alternative_beam
Setup2 = Composition(name="Mach Zehnder 2")
Setup2.set_geom(arm2_lightsource.get_geom())
Setup2.set_light_source(arm2_lightsource) 
Setup2.propagate(256)
Setup2.add_on_axis(M5)
Setup2.propagate(305)

# Setup2.propagate(100.1)
# rotator= Polarization_Rotator()
# Setup2.add_supcomposition_on_axis(rotator)
# Setup2._optical_axis[-1] = rotator._optical_axis[-1]
# Setup2.propagate(0)

if freecad_da:
    clear_doc()
    Pump_bot = deepcopy(Pump_bot)
    Pump_top = deepcopy(Pump_top)
    Pump_bot.draw()
    Pump_top.draw()
    Setup.draw()
    Setup2.draw()
    table.draw()
    table2.draw()
    Housing.draw()
    Housing2.draw()
    LiMgAS_crystal2.draw()
    LiMgAS_crystal1.draw()
    setview()

else:
    print_post_positions(Pump_top)
    print_post_positions(Pump_bot)
    print_post_positions(Setup)
    print_post_positions(Setup2)

    # export_to_TikZ(Pump_top, draw_beams=True, beam_color="optikzred")
    # export_to_TikZ(Pump_bot, draw_beams=True, beam_color="optikzred")
    # export_to_TikZ(Setup, draw_beams=True, beam_color="green")
    # export_to_TikZ(Setup2, draw_beams=True, beam_color="green")