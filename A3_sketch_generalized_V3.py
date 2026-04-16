# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 12:39:52 2024

@author: Martin
"""

##################################
UsePolRotator = False
##################################

import numpy as np
import matplotlib.pyplot as plt
import sys

from LaserCAD.freecad_models import clear_doc, setview, freecad_da, model_mirror, add_to_composition
from LaserCAD.basic_optics import Mirror, Beam, Ray_Distribution, Composition, Component, inch, Curved_Mirror, Ray, Geom_Object
from LaserCAD.basic_optics import Grating, Opt_Element
import matplotlib.pyplot as plt
from LaserCAD.freecad_models.utils import thisfolder, load_STL
from LaserCAD.non_interactings import Crystal, Lambda_Plate
from LaserCAD.non_interactings.pockels_cell import Pockels_Cell_Thick
from LaserCAD.basic_optics import Composed_Mount,Unit_Mount,Lens,Post, export_to_TikZ, print_post_positions
from copy import deepcopy
from LaserCAD.moduls import Polarization_Rotator
from LaserCAD.basic_optics.lens import Thicklens


def rad(angle):
    return np.pi/180*angle

def deg(angle):
    return 180/np.pi*angle

def get_TFP_distances(TFP_ydist, TFP_angle):
    TFP_xdist = TFP_ydist*np.tan(TFP_angle)
    TFP_dist = np.sqrt(TFP_ydist**2 + TFP_xdist**2)
    TFP_delta = TFP_dist - TFP_ydist - TFP_xdist
    
    TFP_Lam = 0.1*TFP_dist
    Lam_PC = 0.7*TFP_dist  # 0.6 before
    dist_PC_TFP = TFP_dist - TFP_Lam - Lam_PC
    
    return TFP_dist, TFP_xdist, TFP_delta, TFP_Lam, Lam_PC, dist_PC_TFP

rotate_axis = np.pi
offset_axis = (950+150,300,20)

class Newport_Mirror(Mirror):
    def __init__(self, name="Newport Mirror", aperture=inch, mirror=False, **kwargs):
        super().__init__(name=name, aperture=aperture, **kwargs)
        self.aperture = aperture
        add_name = "_LH" if mirror else ""
        if aperture == inch:
            model = "U100-A2K"
        elif aperture == 2*inch:
            model = "U200-A2K"
        elif aperture == 3*inch:
            model = "U300-A2K"

        self.set_mount(Composed_Mount(unit_model_list=[model+add_name, "1inch_post"]))
            

class Newport_Curved_Mirror(Curved_Mirror):
    def __init__(self, name="Newport Mirror", aperture=inch, mirror=False, **kwargs):
        super().__init__(name=name, aperture=aperture, **kwargs)
        self.aperture = aperture
        add_name = "_LH" if mirror else ""
        if aperture == inch:
            model = "U100-A2K"
        elif aperture == 2*inch:
            model = "U200-A2K"
        elif aperture == 3*inch:
            model = "U300-A2K"
        self.set_mount(Composed_Mount(unit_model_list=[model+add_name, "1inch_post"]))

class Table(Crystal):
    def __init__(self, name="Table", width=1000, height=10, thickness=1000, **kwargs):
        super().__init__(name=name, width=width, height=height, thickness=thickness, **kwargs)
        self.draw_dict["Transparency"] = 0
        self.draw_dict["color"] = (0.3, 0.3, 0.3)

class Adapter_2inch(Composed_Mount):
  def __init__(self, angle=0):
    super().__init__()
    um = Unit_Mount()
    um.model = "2inch_adapter"
    um.path = thisfolder + "misc_meshes/"
    um.docking_obj.pos += (14.3,64,0) # from manual adjustments in FreeCAD
    um.is_horizontal = False
    um.draw_dict["color"] = (0.3,0.3,0.3)
    self.add(um)
    um.rotate(vec=um.normal, phi=angle*np.pi/180)
    self.add(Unit_Mount(model="U200-A2K"))
    self.add(Post())

class Cylindric_Crystal(Component):
  def __init__(self, name="LaserCrystal", aperture=6, thickness=3, **kwargs):
    super().__init__(name=name, **kwargs)
    self.aperture = aperture
    self.thickness = thickness
    self.draw_dict["color"] = (0.8, 0.3, 0.1)
    self.freecad_model = model_mirror
    self.pos += offset_axis

vacuum_tube = Component(name="Vacuum Tube")
vacuum_tube.draw_dict["stl_file"]= rf"{thisfolder}\mount_meshes\special_mount\Vacuum_Tube_1300mm.stl"
vacuum_tube.freecad_model = load_STL

"""
Simulation of the amplifier cavity
"""

Pol_Rotater = Polarization_Rotator()
r1 = 2000 
r2 = 2500

f1 = r1/2
f2 = r2/2

beam = Beam(radius=5, angle=0)
beam.pos=[0,0,0]

if UsePolRotator:
    g = 530 # object distance: distance between the pump region and the first curved mirror
    length_diff = Pol_Rotater.length_diff
    print(f"Using Polarization Rotator with length difference of {length_diff}mm")
else: 
    g = 550#520
    length_diff = 0
    
ydist_M2_M3 = 70

# Calculation of the image distance
b = ((f1-g)*f2**2 + f1**2 * f2) / (f1**2)

pump_angle = 90   # input-output angle on the pump mirrors, standard: 90
tele_angle1 = 4   # opening angle for coupling into telescope
tele_angle2 = 4   # opening angle for couling into telescope # 4 before

xdist_R1_M1 = 200 # cut mirror x-distance from spherical mirrors
ydist_R2_M2 = 350 # cut mirror y-distance from spherical mirrors

dist_P2_M4 = 60  # distance from pump mirror P2 to M4
dist_R1_M1 = xdist_R1_M1 / np.cos(rad(tele_angle1)) # propagation distance to first spherical mirror
dist_R2_M2 = ydist_R2_M2 / np.cos(rad(tele_angle2)) # propagation distance to second spherical mirror

ydist_R1_M1 = np.sqrt(dist_R1_M1**2 - xdist_R1_M1**2)
xdist_R2_M2 = np.sqrt(dist_R2_M2**2 - ydist_R2_M2**2)

TFP_angle = 66
TFP_angle = rad(2*TFP_angle - 90)
            
cavity_length = f1 + f2 + g + b  # total cavity length, g-object distance, b-image distance
            
pump_dist = 80    # 150            # length of pump section
dist_M4_M1 = g-dist_P2_M4-dist_R1_M1-pump_dist/2       # distance from P2 to M1
xdist_M3_TFP1 = 150                            # x-distance from M3 to TFP1
dist_vacuum_tube = xdist_R1_M1 + 150

# ydist: difference between beam y-position at TFP2 and the vacuum tube

ydist = pump_dist + dist_M4_M1 - ydist_R1_M1 
TFP_ydist = ydist - ydist_M2_M3
TFP_dist, TFP_xdist, TFP_delta, TFP_Lam, Lam_PC, dist_PC_TFP = get_TFP_distances(TFP_ydist, TFP_angle)
dist_R2_M3 = (ydist_R2_M2-ydist_M2_M3) / np.cos(rad(tele_angle2))

# print(f"lambda PC distance = {Lam_PC}mm")
print("Cavity:")
print(f"g = {g}mm, b = {b}mm")

P1 = Newport_Mirror(name="pump mirror 1", phi=pump_angle, aperture=25.4*2, mirror=True) # pump mirror 1
# P1.set_mount(Adapter_2inch(angle=90))
P2 = Newport_Mirror(name="pump mirror 2", phi=-pump_angle, aperture=25.4*2, mirror=True)  # pump mirror 2
M1 = Newport_Mirror(name="M1, cut mirror 1", phi=-pump_angle-tele_angle1) # cut mirror 1
M2 = Newport_Mirror(phi=90, name="M2, cut mirror 2") # cut mirror 2
M3 = Newport_Mirror(phi=-90+tele_angle2, name="M3, mirror towards tfp 1") # mirror to TFP1
M4 = Newport_Mirror(name="M4, after pump mirror 2", phi=pump_angle) # mirror after TFP2
R1 = Newport_Curved_Mirror(name=f"R1, f={f1:.0f}mm", phi=-180+tele_angle1, radius=r1)
R2 = Newport_Curved_Mirror(name=f"R2, f={f2:.0f}mm", phi=-180-tele_angle2, radius=r2, aperture=25.4*3)
TFP1 = Newport_Mirror(name="TFP1 (Input)", phi=-90+deg(TFP_angle), aperture=25.4*2)
TFP2 = Newport_Mirror(name="TFP2 (Output)", phi=90-deg(TFP_angle), aperture=25.4*2)
pockels_cell = Pockels_Cell_Thick(name="Pockels Cell", mount_name="Pockels_cell_thick")

Setup = Composition(name="A3")
Setup.set_light_source(beam)
Setup.pos += offset_axis

pos_start = Setup.pos.copy()
Setup.normal = (0,1,0)
Setup.propagate(pump_dist/2)
Setup.add_on_axis(P2)
Setup.propagate(dist_P2_M4)
Setup.add_on_axis(M4)
Setup.propagate(dist_M4_M1)
Setup.add_on_axis(M1)
Setup.propagate(dist_R1_M1)
Setup.add_on_axis(R1)
# print(f"distance to first curved mirror: {Setup.optical_path_length():.2f}mm, g={g}mm")
Setup.propagate(dist_vacuum_tube)
Setup.add_on_axis(vacuum_tube)
Setup.propagate(f1+f2-dist_vacuum_tube-ydist_R2_M2)
Setup.add_on_axis(M2)
Setup.propagate(ydist_R2_M2)
Setup.add_on_axis(R2)
# print(f"distance to first second curved mirror: {Setup.optical_path_length():.2f}mm, g+f1+f2={g+f1+f2}mm")
Setup.propagate(dist_R2_M3)
Setup.add_on_axis(M3)
Setup.propagate(xdist_M3_TFP1)
Setup.add_on_axis(TFP1)

Setup.propagate(TFP_Lam)
# Polarisationsdreher %%%%%%%%%%%
if UsePolRotator:
    Setup.add_supcomposition_on_axis(Pol_Rotater)
else:
    Setup.add_on_axis(Lambda_Plate())
# Polarisationsdreher Ende
Setup.propagate(Lam_PC)
Setup.add_on_axis(pockels_cell)
pockels_cell.rotate((0,0,1), np.pi)
pockels_cell.rotate(pockels_cell.normal, np.pi)

Setup.propagate(dist_PC_TFP)
Setup.add_on_axis(TFP2)
dist_TFP2_P1 = abs(TFP2.pos[0] - pos_start[0])

Setup.propagate(dist_TFP2_P1)
Setup.add_on_axis(P1)
Setup.propagate(pump_dist/2)

dist_to_ideal_imaging = Setup.optical_path_length()+length_diff - cavity_length
image_distance = dist_R2_M3+xdist_M3_TFP1+TFP_dist+dist_TFP2_P1+pump_dist/2-dist_to_ideal_imaging

print(f"Image Distance = {image_distance:.2f} (adding all lengths) = {b:.2f} (b)")
print(f"distance to ideal imaging = {dist_to_ideal_imaging:.2f}mm")
print(f"optical path length = {Setup.optical_path_length()+length_diff:.2f}mm\n")

def image_telescope(f1, f2, g=None, b=None):
    if b is None and g is not None:
        return f1/f2 * (f1 + f2 - g * f1/f2)
    elif g is None and b is not None:
        return f2/f1 * (f1 + f2 - b * f2/f1)
    else:       
        raise ValueError("Either g or b must be provided, but not both.")

"""
####################################################################
######################### Pump Setup ###############################
####################################################################
"""
pump_magnification = 1/3
max_pump_power = 13 # kW
pump_spot_size = 15 # mm
final_pump_area = 1e-2*(pump_magnification*pump_spot_size)**2 # cm^2
max_laser_fluence = 5 # J/cm^2

focal_length1 = 300 # 125
focal_length2 = 100
lasermedia_dist = 17 # distance from the image planes of the two laser media
image_plane_to_pump_module_distance = 65 # distance from the pump module to the image plane

Lens_pump_top_f1 = Lens(f=focal_length1, n=1.515, aperture=3*inch, name=f"Pump Lens top, f1={focal_length1}mm")
Lens_pump_top_f2 = Lens(f=focal_length2, n=1.515, aperture=3*inch, name=f"Pump Lens top f2={focal_length2}mm")
Lens_pump_bot_f1 = Lens(f=focal_length1, n=1.515, aperture=3*inch, name=f"Pump Lens bot, f1={focal_length1}mm")
Lens_pump_bot_f2 = Lens(f=focal_length2, n=1.515, aperture=3*inch, name=f"Pump Lens bot, f2={focal_length2}mm")

Lens_pump_top_f1.aperture = 25.4*3
Lens_pump_top_f1.set_mount_to_default()
Lens_pump_top_f2.aperture = 25.4*3
Lens_pump_top_f2.set_mount_to_default()
Lens_pump_bot_f1.aperture = 25.4*3
Lens_pump_bot_f1.set_mount_to_default()
Lens_pump_bot_f2.aperture = 25.4*3
Lens_pump_bot_f2.set_mount_to_default()

image_distance = 170
object_distance = image_telescope(focal_length1, focal_length2, b=image_distance)

print("Pump Setup:")
print(f"object distance = {object_distance:.1f}mm, image distance = {image_distance:.1f}mm")
print(f"distance from pump module to image plane = {image_plane_to_pump_module_distance}mm, distance between laser media = {lasermedia_dist}mm")
print(f"pump magnification = {pump_magnification:.2f}, final spot size = {pump_magnification*pump_spot_size:.1f}mm, A = {final_pump_area:.2f}cm²")
print(f"pump intensity = {max_pump_power/final_pump_area:.1f}kW/cm²\n")

print("Amplifier Setup:") 
print(f"maximum output fluence = {max_laser_fluence}J/cm²")
print(f"maximum laser energy = {max_laser_fluence*final_pump_area:.1f}J\n")

dist_M3_pump_lens = 50
pump_module_separation = 300
dist_to_first_pump_lens = image_plane_to_pump_module_distance + object_distance
dist_M2_pump_lens2 = 70
pump_module_xoffset = 200

total_pump_length = dist_to_first_pump_lens + focal_length1 + focal_length2 + image_distance + lasermedia_dist
remaining_length = total_pump_length - pump_module_xoffset - pump_module_separation/2 - dist_M2_pump_lens2 

remaining_length1 = remaining_length/2 - dist_M2_pump_lens2**2/(2*remaining_length)
remaining_length2 = remaining_length - remaining_length1
angle_pump_mirror = deg(np.arcsin(dist_M2_pump_lens2/remaining_length2))

print("remaining lengths:", remaining_length, remaining_length1, remaining_length2)
beamtop_1 = Ray_Distribution(radius=pump_spot_size/2,angle=1.4*2.08*np.pi/180,wavelength=940E-6, steps=3)
beamtop_1.draw_dict["color"] = (255/256,255/256,0.0)

beambot_1 = Ray_Distribution(radius=pump_spot_size/2,angle=1.4*2.08*np.pi/180,wavelength=940E-6, steps=3)
beambot_1.draw_dict["color"] = (255/256,255/256,0.0)

Pump_top = Composition(name="PM19 top")
Pump_top.set_light_source(beamtop_1)
Pump_top.pos -= (pump_module_xoffset,-pump_module_separation/2,0)


Pump_bot = Composition(name="PM19 bot")
Pump_bot.set_light_source(beambot_1)
Pump_bot.pos -= (pump_module_xoffset,pump_module_separation/2,0)

Laser_Head_in = Component(name="laser Pump Module PM19 bot")
stl_file = rf"{thisfolder}\misc_meshes\PM19_2.stl"
Laser_Head_in.draw_dict["stl_file"]=stl_file
Laser_Head_in.freecad_model = load_STL

Laser_Head_out = Component(name="laser Pump Module PM19 top")
stl_file = rf"{thisfolder}\misc_meshes\PM19_2.stl"
Laser_Head_out.draw_dict["stl_file"]=stl_file
Laser_Head_out.freecad_model = load_STL

Kuehlmount_Alumosilikatglas = Component(name="Kuehlmount Alumosilikatglas d23")
stl_file = rf"{thisfolder}\misc_meshes\Kuehlmount_Alumosilikatglas_d23.stl"
Kuehlmount_Alumosilikatglas.draw_dict["stl_file"]=stl_file
Kuehlmount_Alumosilikatglas.freecad_model = load_STL

Kuehlmount2_Alumosilikatglas = deepcopy(Kuehlmount_Alumosilikatglas)

# lens_pump_top = Lens(f=focal_length1, name=f"Pump Lens 1, f={focal_length1}mm")
# lens_pump_top.aperture = 25.4*3
# lens_pump_top.set_mount_to_default()

# lens_pump_bot = deepcopy(lens_pump_top)
# lens_pump_bot.name = f"Pump Lens 2, f={focal_length1}mm"

M3_top = Newport_Mirror(phi=180-angle_pump_mirror, name="3inch mirror", aperture=25.4*3, mirror=True)
M3_bot = Newport_Mirror(phi=180+angle_pump_mirror, name="3inch mirror 2", aperture=25.4*3)

M3_top2 = Newport_Mirror(phi=+90+angle_pump_mirror, name="3inch mirror", aperture=25.4*3, mirror=True)
M3_bot2 = Newport_Mirror(phi=-90-angle_pump_mirror, name="3inch mirror 2", aperture=25.4*3)

LiMgAS_crystal1 = Cylindric_Crystal(name="LiMgAs", aperture=23, thickness=12)
LiMgAS_crystal2 = Cylindric_Crystal(name="LiMgAs2", aperture=23, thickness=12)

Pump_top.pos += offset_axis
print(f"PM19 top position = ({Pump_top.pos[0]/10:.1f}cm, {Pump_top.pos[1]/10:.1f}cm, {Pump_top.pos[2]/10:.1f}cm)")
Pump_top.add_on_axis(Laser_Head_in)
Pump_top.propagate(dist_to_first_pump_lens)
if hasattr(Lens_pump_top_f1, "h1"): Pump_top.propagate(Lens_pump_top_f1.h1)
Pump_top.add_on_axis(Lens_pump_top_f1)
if hasattr(Lens_pump_top_f1, "h2"): Pump_top.propagate(Lens_pump_top_f1.h2)
Pump_top.propagate(pump_module_xoffset - dist_to_first_pump_lens + remaining_length1)
Pump_top.add_on_axis(M3_top)
Pump_top.propagate(remaining_length2)
Pump_top.add_on_axis(M3_top2)
Pump_top.propagate(dist_M2_pump_lens2)
if hasattr(Lens_pump_top_f2, "h1"): Pump_top.propagate(Lens_pump_top_f2.h1)
Pump_top.add_on_axis(Lens_pump_top_f2)
if hasattr(Lens_pump_top_f2, "h2"): Pump_top.propagate(Lens_pump_top_f2.h2)
Pump_top.propagate(image_distance-6)
Pump_top.add_on_axis(Kuehlmount_Alumosilikatglas)
Pump_top.add_on_axis(LiMgAS_crystal1)
Pump_top.propagate(6)


Pump_bot.pos += offset_axis
print(f"PM19 bot position = ({Pump_bot.pos[0]/10:.1f}cm, {Pump_bot.pos[1]/10:.1f}cm, {Pump_bot.pos[2]/10:.1f}cm)\n")
Pump_bot.add_on_axis(Laser_Head_out)
Pump_bot.propagate(dist_to_first_pump_lens)
if hasattr(Lens_pump_bot_f1, "h1"): Pump_bot.propagate(Lens_pump_bot_f1.h1)
Pump_bot.add_on_axis(Lens_pump_bot_f1)
if hasattr(Lens_pump_bot_f1, "h2"): Pump_bot.propagate(Lens_pump_bot_f1.h2)
Pump_bot.propagate(pump_module_xoffset - dist_to_first_pump_lens + remaining_length1)
Pump_bot.add_on_axis(M3_bot)
Pump_bot.propagate(remaining_length2)
Pump_bot.add_on_axis(M3_bot2)
Pump_bot.propagate(dist_M2_pump_lens2)
if hasattr(Lens_pump_bot_f2, "h1"): Pump_bot.propagate(Lens_pump_bot_f2.h1)
Pump_bot.add_on_axis(Lens_pump_bot_f2)
if hasattr(Lens_pump_bot_f2, "h2"): Pump_bot.propagate(Lens_pump_bot_f2.h2)
Pump_bot.propagate(image_distance-6)
Pump_bot.add_on_axis(Kuehlmount2_Alumosilikatglas)
Pump_bot.add_on_axis(LiMgAS_crystal2)
Pump_bot.propagate(6)

table = Table(name="Right Table", width=900, height=10, thickness=1500)
table.pos = (0,450,-5)

table2 = Table(name="Left Table", width=750, height=10, thickness=900)
table2.pos = (-900,375,-5)

Housing = Table(name="Housing", width=40, height=40, thickness=15)
Housing.pos = offset_axis
Housing.pos += (-18, 0, 80)
Housing.draw_dict["color"] = (181/255, 166/255, 66/255)

Housing2 = Table(name="Housing", width=40, height=40, thickness=15)
Housing2.pos = offset_axis
Housing2.pos += (3, 0, 80)
Housing2.draw_dict["color"] = (181/255, 166/255, 66/255)



if __name__ == "__main__":
    if freecad_da:
        clear_doc()
        Setup.draw()
        Pump_top.draw()
        Pump_bot.draw()
        table.draw()
        table2.draw()
        # setview()

    else:
        print_post_positions(Setup) 
        print_post_positions(Pump_top)
        print_post_positions(Pump_bot)

        # export_to_TikZ(Pump_top, draw_beams=True, beam_color="optikzred")
        # export_to_TikZ(Pump_bot, draw_beams=True, beam_color="optikzred")
        # export_to_TikZ(Setup, draw_rays=True)
