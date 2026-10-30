# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 14:13:00 2026

@author: Martin
"""


import numpy as np
import sys
import os
from sympy import Matrix

from LaserCAD.freecad_models import clear_doc, setview, freecad_da
from LaserCAD.basic_optics import Mirror, Beam, Composition, Component, inch, Curved_Mirror, Ray, Geom_Object, export_to_TikZ
from LaserCAD.basic_optics import Grating, Opt_Element, Post, Unit_Mount, Composed_Mount
import matplotlib.pyplot as plt
from LaserCAD.freecad_models.utils import thisfolder, load_STL
from LaserCAD.non_interactings import Faraday_Isolator, Pockels_Cell, Lambda_Plate
from LaserCAD.basic_optics.mirror import Newport_Mirror, Newport_Curved_Mirror
from LaserCAD.basic_optics.mount import Adapter_1inch
from LaserCAD.non_interactings.pockels_cell import Pockels_Cell
from LaserCAD.moduls import Polarization_Rotator, Motorized_TSF
from Geometrical_optics import CurvedMirror, Lens, FreeSpacePropagation, OpticalSetup, beam_radius_from_q
  
def dont():
    return None

Folder = os.path.dirname(os.path.abspath(__file__))
beam = Beam(radius=1.5, angle=0.0002, wavelength=1.03e-3, name="main beam")
from LaserCAD.basic_optics import Gaussian_Beam

# define angles and components
PM_angle = 3
CM_angle = 3
M1_angle = 87 - PM_angle
M2_angle = 87 - CM_angle
TFP_angle = 66

pockels_cell = Pockels_Cell(name="Pockels Cell", mount_name="pockels_cell")
Pol_Rotater = Polarization_Rotator(flip=True)

# Prepare the setup
radius = 10000

PM = Newport_Mirror(phi = 180 - PM_angle, aperture=2*inch, name="pump mirror")
M1 = Newport_Mirror(phi = -M1_angle, name="M1")
M1.set_mount(Adapter_1inch(angle=90))
M1.Mount.reverse()
M2 = Newport_Mirror(phi = M2_angle, name="M2")
CM = Newport_Curved_Mirror(phi = - 180 + CM_angle, radius=radius, name="CM")
TFP1 = Newport_Mirror(phi = -180 + 2 * TFP_angle, aperture=2*inch, name="TFP1")
TFP2 = Newport_Mirror(phi =  180 - 2 * TFP_angle, aperture=2*inch, name="TFP2")

M1_in = Newport_Mirror(phi = 270 - 2 * TFP_angle, name="M1_in")

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
Setup.add_supcomposition_on_axis(Motorized_TSF())
L_TSF1 = Setup.optical_path_length()
Setup.propagate(l2-115)
Setup.add_on_axis(M2)
Setup.propagate(145)
Setup.add_supcomposition_on_axis(Motorized_TSF())
L_TSF2 = Setup.optical_path_length()
Setup.propagate(l3-145)
Setup.add_on_axis(CM)
L1 = Setup.optical_path_length()
Setup.propagate(l4)
Setup.add_on_axis(TFP1)
Setup.propagate(l5-400)

Setup.add_supcomposition_on_axis(Pol_Rotater)
Setup.propagate(200)

Setup.add_on_axis(pockels_cell)
L_Pockels = Setup.optical_path_length()
pockels_cell.rotate((0,0,1), np.pi)
pockels_cell.rotate(pockels_cell.normal, np.pi)

Setup.propagate(200)
Setup.add_on_axis(TFP2)
Setup.propagate(620)
L2 = Setup.optical_path_length() - L1

Resonator_beams = Setup.compute_beams()
TFP_beam_in = Resonator_beams[9]
TFP_beam_out = Resonator_beams[12]
radius, angle = TFP_beam_in.radius_angle()

Input_beam = Beam(radius=radius, angle=angle, name="input beam")

radius, angle = TFP_beam_out.radius_angle()
Output_beam = Beam(radius=radius, angle=angle, name="output beam")
Output_beam.set_geom(TFP_beam_out.get_geom())
Output_beam.pos = TFP_beam_out.inner_ray().endpoint()

Setup_in = Composition()
Setup_in.pos = TFP_beam_in._pos
Setup_in.set_geom(TFP_beam_in.get_geom())
Setup_in.normal = TFP_beam_in.normal *-1
Setup_in.set_light_source(Input_beam)
Setup_in.propagate(100)
Setup_in.add_on_axis(M1_in)
Setup_in.propagate(100)


if __name__ == "__main__":
    if freecad_da:
        clear_doc()
        Setup.draw()
        Output_beam.draw()
        Setup_in.draw()
        # setview()
    
    else:
        # export_to_TikZ(Setup, filename=os.path.join(Folder, "Polaris_setup.tex"), draw_rays = True, scale=10)
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
        print(f"cavity length: {L1+L2} mm")
        positions = np.linspace(0, L1+L2, 100)
        q_values = np.array([setup.get_q_at(z) for z in positions])
        # print(q_values)
        matrix = np.array(setup.get_total_matrix()).astype(np.float64)

        element_positions = [0, L_TSF1, L_TSF2, L_TSF2+250, L_Pockels]
        element_width = [beam_radius_from_q(q_values[np.argmin(np.abs(positions - pos))], wavelength=1.03e-3) for pos in element_positions]


        beam_sizes = [beam_radius_from_q(q, wavelength=1.03e-3) for q in q_values]
        element_names = ["pump mirror", "TSF1", "TSF2", "TSF1 (new)", "Pockels cell"]
        # print(beam_sizes)
        plt.figure(figsize=(8,4))
        plt.plot(positions, beam_sizes)
        for pos, size, name in zip(element_positions, element_width, element_names):
            plt.plot(pos, size, 'o', label=name + f", {np.pi*size**2:.2f} mm²")
        plt.xlabel("Position along the cavity (mm)")
        plt.ylabel("Beam radius w(z) (mm)")
        plt.grid()
        plt.legend()
        plt.title(f"Beam radius for R={radius*1e-3} m")
        plt.savefig(f"beam_radius_R_{radius*1e-3:.2f}m.svg", bbox_inches='tight', dpi=300)

  