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
from LaserCAD.basic_optics import Grating, Opt_Element, Post, Unit_Mount, Composed_Mount, Lens, ThinBeamsplitter, Ray_Distribution
import matplotlib.pyplot as plt
from LaserCAD.freecad_models.utils import thisfolder, load_STL
from LaserCAD.non_interactings import Faraday_Isolator, Pockels_Cell, Lambda_Plate, Spectrometer, Detector
from LaserCAD.basic_optics.mirror import Newport_Mirror, Newport_Curved_Mirror
from LaserCAD.basic_optics.mount import Adapter_1inch
from LaserCAD.non_interactings import Pockels_Cell, Faraday_Isolator, Iris
from LaserCAD.moduls import Polarization_Rotator, Motorized_TSF
from Geometrical_optics import CurvedMirror, FreeSpacePropagation, OpticalSetup, beam_radius_from_q
from Geometrical_optics import Lens as Geometrical_Lens
from LaserCAD.non_interactings.crystal import Crystal_with_mount
  
def dont():
    return None

class Beamsplitter(ThinBeamsplitter):
    def __init__(self, transmission=False, angle=0, name="Beamsplitter"):
        super().__init__(name=name, transmission=transmission, angle_of_incidence=angle)
        self.aperture = 25.4*1
        self.set_mount(Composed_Mount(unit_model_list=["U100-A2K", "1inch_post"]))


class Newport_Curved_Mirror(Curved_Mirror):
    def __init__(self, name="Newport Mirror", aperture=inch, thickness=6, mirror=False, **kwargs):
        super().__init__(name=name, aperture=aperture, thickness=thickness, **kwargs)
        self.aperture = aperture
        add_name = "_LH" if mirror else ""
        if aperture == inch:
            model = "U100-A2K"
        elif aperture == 2*inch:
            model = "U200-A2K"
        elif aperture == 3*inch:
            model = "U300-A2K"
        self.set_mount(Composed_Mount(unit_model_list=[model+add_name, "1inch_post"]))
        self.set_mount_back_mounted()

class Pump_beam(Ray_Distribution):
    def __init__(self, radius=1, angle=1.9*2.08*np.pi/180, wavelength=940E-6, steps=3):
        super().__init__(radius=radius, angle=angle, wavelength=wavelength, steps=steps)
        self.draw_dict["color"] = (255/256,255/256,0.0)

Folder = os.path.dirname(os.path.abspath(__file__))
beam = Beam(radius=1.5, angle=0.0002, wavelength=1.03e-3, name="main beam")
from LaserCAD.basic_optics import Gaussian_Beam

# define angles and components
PM_angle = 3
CM_angle = 3
M1_angle = 87 - PM_angle
M2_angle = 87 - CM_angle
TFP_angle = 66

faraday_isolator = Faraday_Isolator(name="Faraday Isolator", mount_name="faraday_isolator")
pockels_cell = Pockels_Cell(name="Pockels Cell", mount_name="pockels_cell")
Pol_Rotator1 = Polarization_Rotator(flip=True, name="Polarization Rotator Cavity")
Pol_Rotator2 = Polarization_Rotator(flip=False, name="Polarization Rotator Input")
Laser_crystal = Crystal_with_mount(name="Laser crystal", stl_file="Kuehlmount_Alumosilikatglas_d23.stl", thickness=12, flip=True)

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
TL0 = Lens(f=500, name="Telescope Lens 0")
TL1 = Lens(f=100, name="Telescope Lens 1")
TL2 = Lens(f=200, name="Telescope Lens 2")

M1_in = Newport_Mirror(phi = 270 - 2 * TFP_angle, name="M1_in")
M2_in = Newport_Mirror(phi = 90, name="M2_in")
M3_in = Newport_Mirror(phi = 90, name="M3_in")
M4_in = Newport_Mirror(phi = -90, name="M4_in")

M1_out = Newport_Mirror(phi = - 2 * TFP_angle, name="M1_out")
M2_out = Beamsplitter(angle = -45, transmission=True, name="M2_out")
M3_out = Beamsplitter(angle = 3, transmission=False, name="M3_out")
M4_out = Newport_Mirror(phi = 186, name="M4_out")
M5_out = Newport_Mirror(phi = -90, name="M5_out")

PumpL1 = Lens(f=100, aperture=2*inch, name="Pump lens 1")  # f????
PumpL2 = Lens(f=1000, aperture=2*inch, name="Pump lens 2")  # f????
PumpL3 = Lens(f=1000, aperture=2*inch, name="Pump lens 3")  # f????

l1 = 565
l2 = 325 - 8.3
l3 = 1060
l4 = 660
l5 = 540

## Make the setup
Setup = Composition(name="A2 Resonator")
Setup.pos = (0,0,140)
Setup.set_light_source(beam)

# We start at the position of the Glan_in
# Setup.propagate(100)
Setup.add_on_axis(PM)
Setup.propagate(25)
Setup.add_supcomposition_on_axis(Laser_crystal)
Setup.propagate(l1-25)
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

Setup.add_supcomposition_on_axis(Pol_Rotator1)
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
TFP_beam_out = Resonator_beams[13]
radius, angle = TFP_beam_in.radius_angle()
Input_beam = Beam(radius=radius, angle=angle, name="input beam")

radius, angle = TFP_beam_out.radius_angle()
Output_beam = Beam(radius=radius, angle=angle, name="output beam")


Setup_in = Composition(name="Setup_in")
Setup_in.pos = TFP_beam_in._pos
Setup_in.set_geom(TFP_beam_in.get_geom())
Setup_in.normal = TFP_beam_in.normal *-1
Setup_in.set_light_source(Input_beam)
Setup_in.propagate(60)
Setup_in.add_on_axis(M1_in)
Setup_in.propagate(248)
Setup_in.add_on_axis(Iris(name="A2 shutter in"))
Setup_in.propagate(30)
Setup_in.add_on_axis(faraday_isolator)
Setup_in.propagate(75+52)
Setup_in.add_on_axis(TL0) 
Setup_in.propagate(84)
Setup_in.add_on_axis(M2_in)
Setup_in.propagate(210)
Setup_in.add_on_axis(TL1) 
Setup_in.propagate(TL1.focal_length + TL2.focal_length)
Setup_in.add_on_axis(TL2)
Setup_in.propagate(290)
Setup_in.add_on_axis(M3_in)
Setup_in.propagate(104)
Setup_in.add_supcomposition_on_axis(Pol_Rotator2)
Setup_in.propagate(80)
Setup_in.add_on_axis(M4_in)

# Setup out

Setup_out = Composition(name="Setup_out")
Setup_out.pos = TFP_beam_out._pos
Setup_out.set_geom(Resonator_beams[13].get_geom())
Setup_out.normal = Resonator_beams[12].normal 
Setup_out.set_light_source(Output_beam)
Setup_out.propagate(100)
Setup_out.add_on_axis(M1_out)
Setup_out.propagate(600)
Setup_out.add_on_axis(M2_out)
Setup_out.propagate(200)
Setup_out.add_on_axis(M3_out)
Setup_out.propagate(800)
Setup_out.add_on_axis(M4_out)
Setup_out.propagate(200)

# Energy_head
Setup_out.compute_beams()

Lens_energy = Lens(f=-30, name="Energy head lens")
arm2_lightsource = M2_out._alternative_beam
Setup_Energy = Composition(name="Energy head")
Setup_Energy.set_geom(arm2_lightsource.get_geom())
Setup_Energy.set_light_source(arm2_lightsource) 
Setup_Energy.propagate(100)
Setup_Energy.add_on_axis(Lens_energy)
Setup_Energy.propagate(100)
Setup_Energy.add_on_axis(Detector(name="Energy head detector"))

# Spectrometer 

Lens_spectrometer = Lens(f=75, name="Energy head lens")
arm3_lightsource = M3_out._alternative_beam
Setup_Spectrometer = Composition(name="Spectrometer")
Setup_Spectrometer.set_geom(arm3_lightsource.get_geom())
Setup_Spectrometer.set_light_source(arm3_lightsource)
Setup_Spectrometer.propagate(100)
Setup_Spectrometer.add_on_axis(M5_out)
Setup_Spectrometer.propagate(100)
Setup_Spectrometer.add_on_axis(Lens_spectrometer)
Setup_Spectrometer.propagate(70)
Setup_Spectrometer.add_on_axis(Spectrometer(name="Spectrometer", model="SR"))

# Pump optics 

Setup_pump = Composition(name="Pump optics")
pump_beam = Pump_beam()

laser_diode_stack = Component(name="Laser diode stack")
laser_diode_stack.draw_dict["stl_file"]= rf"{thisfolder}\misc_meshes\Jenoptik_Laserdiodenstack.stl"
laser_diode_stack.freecad_model = load_STL
Setup_pump.set_geom(Laser_crystal.get_geom())
# pump_beam.normal *= -1
Setup_pump.normal *= -1
Setup_pump.set_light_source(pump_beam)
Setup_pump.propagate(25+42)
Setup_pump.add_on_axis(PumpL1)
Setup_pump.propagate(64)
Setup_pump.add_on_axis(PumpL2)
Setup_pump.propagate(54)
Setup_pump.add_on_axis(PumpL3)
Setup_pump.propagate(158-170/2)
Setup_pump.add_on_axis(laser_diode_stack)


if __name__ == "__main__":
    if freecad_da:
        clear_doc()
        Setup.draw()
        Setup_in.draw()
        Setup_out.draw()
        Setup_Energy.draw()
        Setup_Spectrometer.draw()
        Setup_pump.draw()
        setview()
    
    else:
        # export_to_TikZ(Setup_out, filename=os.path.join(Folder, "Polaris_setup.tex"), draw_rays = True, scale=10)
        setup = OpticalSetup()
        # setup.add_element(Geometrical_Lens(f=2300))
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

  