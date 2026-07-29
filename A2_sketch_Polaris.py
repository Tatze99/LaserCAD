# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 14:13:00 2026

@author: Martin
"""


import numpy as np
import sys
from sympy import Matrix

from LaserCAD.freecad_models import clear_doc, setview, freecad_da
from LaserCAD.basic_optics import Mirror, Beam, Composition, Component, inch, Curved_Mirror, Ray, Geom_Object
from LaserCAD.basic_optics import Grating, Opt_Element, Post, Unit_Mount, Composed_Mount
import matplotlib.pyplot as plt
from LaserCAD.freecad_models.utils import thisfolder, load_STL
from LaserCAD.non_interactings import Faraday_Isolator, Pockels_Cell, Lambda_Plate
from A3_sketch_generalized_V3 import Newport_Mirror, Newport_Curved_Mirror
from LaserCAD.non_interactings.pockels_cell import Pockels_Cell
from LaserCAD.moduls import Polarization_Rotator
from Geometrical_optics import CurvedMirror, Lens, FreeSpacePropagation, OpticalSetup, beam_radius_from_q
  
def dont():
    return None


beam = Beam(radius=1, angle=0)
from LaserCAD.basic_optics import Gaussian_Beam

# define angles and components
PM_angle = 3
CM_angle = 3
M1_angle = 87 - PM_angle
M2_angle = 87 - CM_angle
TFP_angle = 66

class Adapter_1inch(Composed_Mount):
  def __init__(self, angle=0, post="1inch_post", model="U100-A2K"):
    super().__init__()
    um = Unit_Mount()
    um.model = "1inch_adapter"
    um.path = thisfolder + "misc_meshes/"
    um.docking_obj.pos += (6.5,38,0) # from manual adjustments in FreeCAD
    um.is_horizontal = False
    um.draw_dict["color"] = (0.3,0.3,0.3)
    self.add(um)
    self.post_model = post
    self.model = model
    um.rotate(vec=um.normal, phi=angle*np.pi/180)
    self.add(Unit_Mount(model=model))
    self.add(Post(model=post))

def motorized_TSF():
    Housing = Unit_Mount("Spiegelhalter_160021_V1")
    # Housing.draw_dict["color"]=(0.2, 0.2, 0.2)
    # Housing.docking_obj.pos += (33.5,9.2, -37.99)
    # Housing.docking_obj.normal = (0,0,1)

    Rotator_box = Composed_Mount()
    Rotator_box.add(Housing)
    Rotator_box.add(Post())
    Rotator_housing=Component()
    Rotator_housing.draw_dict["stl_file"]="dont_draw"
    Rotator_housing.freecad_model = load_STL
    Rotator_housing.Mount = Rotator_box

    return Rotator_housing

pockels_cell = Pockels_Cell(name="Pockels Cell", mount_name="pockels_cell")
Pol_Rotater = Polarization_Rotator()

# Prepare the setup
radius = 8000

PM = Newport_Mirror(phi = 180 - PM_angle, aperture=2*inch, name="pump mirror")
M1 = Newport_Mirror(phi = -M1_angle, name="M1")
M1.set_mount(Adapter_1inch(angle=90))
M1.Mount.reverse()
M2 = Newport_Mirror(phi = M2_angle, name="M2")
CM = Newport_Curved_Mirror(phi = - 180 + CM_angle, radius=radius, name="CM")
TFP1 = Newport_Mirror(phi = -180 + 2 * TFP_angle, aperture=2*inch, name="TFP1")
TFP2 = Newport_Mirror(phi =  180 - 2 * TFP_angle, aperture=2*inch, name="TFP2")

l1 = 565
l2 = 325 - 8.3
l3 = 1060
l4 = 660
l5 = 540

## Make the setup
Setup = Composition()
Setup.pos = (0,0,140)
Setup.set_light_source(beam)

# We start at the position of the Glan_in
# Setup.propagate(100)
Setup.add_on_axis(PM)
Setup.propagate(l1)
Setup.add_on_axis(M1)
Setup.propagate(115)
Setup.add_on_axis(motorized_TSF())
Setup.propagate(l2-115)
Setup.add_on_axis(M2)
Setup.propagate(145)
Setup.add_on_axis(motorized_TSF())
Setup.propagate(l3-145)
Setup.add_on_axis(CM)
L1 = Setup.optical_path_length()
Setup.propagate(l4)
Setup.add_on_axis(TFP1)
Setup.propagate(l5-400)

Setup.add_supcomposition_on_axis(Pol_Rotater)
Setup.propagate(200)

Setup.add_on_axis(pockels_cell)
pockels_cell.rotate((0,0,1), np.pi)
pockels_cell.rotate(pockels_cell.normal, np.pi)

Setup.propagate(200)
Setup.add_on_axis(TFP2)
Setup.propagate(620)
L2 = Setup.optical_path_length() - L1


if __name__ == "__main__":
    if freecad_da:
        clear_doc()
        Setup.draw()
        # setview()
    
    else:
        setup = OpticalSetup()
        # setup.add_element(Lens(f=2300))
        setup.add_element(FreeSpacePropagation(d=L1))
        setup.add_element(CurvedMirror(R=radius))
        setup.add_element(FreeSpacePropagation(d=L2))

        total_matrix = setup.get_total_matrix()
        print("Total optical matrix:")
        print(total_matrix)
    
        print(f"Stability condition: {setup.stability_condition()}")
        print(f"Beam waist position z: {setup.beam_waist_position()} mm")
        print(f"Rayleigh range zR: {setup.rayleigh_length()} mm")
        print(f"Beam waist radius w0: {setup.beam_waist_radius(wavelength=1.03e-3)} mm")
        print(f"initial q-parameter: {setup.get_initial_q()}")
    
        print(f"total_matrix: {setup.get_total_matrix()}")
        print(f"matrix at z=3200: {setup.get_matrix_at(3201)}")
        positions = np.linspace(0, 3200, 100)
        q_values = np.array([setup.get_q_at(z) for z in positions])
        # print(q_values)
    
        beam_sizes = [beam_radius_from_q(q, wavelength=1.03e-3) for q in q_values]
        # print(beam_sizes)
        plt.figure()
        plt.plot(positions, beam_sizes)

  