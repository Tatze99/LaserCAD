from LaserCAD.basic_optics import SquareBeam, Composition, Intersection_plane, Ray_Distribution
from LaserCAD.freecad_models import clear_doc, setview, freecad_da
from LaserCAD.basic_optics.lens import Thicklens, Lens
import numpy as np
import os 
from copy import deepcopy
import matplotlib.pyplot as plt
inch = 25.4

def set_plot_params():
    plt.rcParams["figure.figsize"] = (6,4)
    plt.rcParams["axes.grid"] = False
    plt.rcParams['grid.linewidth'] = 0.5  # Adjust the value to make it thinner
    plt.rcParams["xtick.direction"] = "in"
    plt.rcParams["ytick.direction"] = "in"
    plt.rcParams["xtick.top"] = True
    plt.rcParams["ytick.right"] = True

    plt.rc('font', family='serif')
    plt.rc('font', serif='Times New Roman')
    plt.rcParams['mathtext.fontset'] = 'custom'
    plt.rcParams['mathtext.rm'] = 'Times New Roman'
    plt.rcParams['mathtext.it'] = 'Times New Roman:italic'
    plt.rcParams['mathtext.bf'] = 'Times New Roman:bold'

Folder = os.path.dirname(os.path.abspath(__file__))

def test_radius(Lens):
  n = Lens.refractive_index
  r1 = Lens.radius1()
  r2 = Lens.radius2()
  d = Lens.thickness
  if Lens.biconvex:
    f = 1/((n-1)*(2/r1-(n-1)*d/(n*r1**2)))
  else:
    f = 1/((n-1)*(1/r1))

  print(f"lens radii: R1 = {r1:.2f}mm, R2 = {r2:.2f}mm")
  print(f"lens focal length: {f:.2f}mm")
  print(f"given focal length: {Lens.focal_length:.2f}mm")
  print(f"lens thickness: {d:.2f}mm")

def test_composition(offset=0, f=85, aperture=75, edge_thickness=3, biconvex=False, draw_spot_diagram=True, save=False, add_telescope=False, add_text="", add_propagation=0):
  pump_magnification = 0.45  
  file_name = generate_file_name(f, biconvex, aperture, pump_magnification, add_telescope, add_text, add_propagation)
  title = generate_title(f, biconvex, aperture, pump_magnification)

  pump_spot_size = 15 # mm
  final_spot_size = 1*pump_spot_size * pump_magnification
  object_distance = f * (1 + 1/pump_magnification)
  image_distance = f * (1 + pump_magnification)
  print(f"focal length: {f:.2f}mm, object distance: {object_distance:.2f}mm, image distance: {image_distance:.2f}mm")
  Lens1 = Thicklens(f=f, n=1.515, aperture=aperture, biconvex=biconvex)

  print(f"principal planes: h1 = {Lens1.h1:.2f}mm, h2 = {Lens1.h2:.2f}mm")

  steps = 3 if freecad_da else 9

  Comp = Composition()
  Comp.pos += (0, -offset,50)
  Beam = Ray_Distribution(radius=pump_spot_size/2,angle=1*2.08*np.pi/180,wavelength=940E-6, steps=steps)
  Comp.set_light_source(Beam)
  IP1 = Intersection_plane()
  IP1.draw()
  # if draw_spot_diagram and not freecad_da: 
  #   dirname = os.path.dirname(file_name)
  #   IP1.spot_diagram(Comp._beams[-1], save=save, filename=os.path.join(dirname, "initial_beam_spot_diagram.pdf"), title="Initial Beam Spot Diagram")

  Comp.propagate(object_distance+Lens1.h1)
  Comp.add_on_axis(Lens1)
  Comp.propagate(image_distance+Lens1.h2+add_propagation)

  if add_telescope: 
    Lens_telescope = Thicklens(f=100, n=1.515, aperture=aperture)
    Lens2_telescope = Thicklens(f=100, n=1.515, aperture=aperture)
    Lens3_telescope = Thicklens(f=100, n=1.515, aperture=aperture)
    Lens4_telescope = Thicklens(f=100, n=1.515, aperture=aperture)
    Comp.propagate(100+Lens_telescope.h1)
    Comp.add_on_axis(Lens_telescope)
    Comp.propagate(200+Lens2_telescope.h1+Lens_telescope.h2)
    Comp.add_on_axis(Lens2_telescope)
    Comp.propagate(200+Lens3_telescope.h1+Lens2_telescope.h2)
    Comp.add_on_axis(Lens3_telescope)
    Comp.propagate(200+Lens4_telescope.h1+Lens3_telescope.h2)
    Comp.add_on_axis(Lens4_telescope)
    Comp.propagate(100+Lens4_telescope.h2)

  IP2 = Intersection_plane()
  Comp.add_on_axis(IP2)
  IP2.draw()
  # Comp.propagate(100)
  Comp.draw()

  if draw_spot_diagram and not freecad_da: 
    point_x, point_y = IP2.spot_diagram(Comp._beams[-1], save=save, filename=file_name, title=title, draw_rectangle=True, rectangle_size=(final_spot_size, final_spot_size))
    print(f"number of rays = {len(point_x)}")
    print(f"percentage of rays inside rectangle = {calc_target_ray_number(point_x, point_y, final_spot_size):.2f}%")

    final_spot_size_array = np.linspace(0, pump_spot_size, 100)
    percentage_array = [calc_target_ray_number(point_x, point_y, s) for s in final_spot_size_array]
    plt.figure()
    plt.plot(final_spot_size_array, percentage_array, label=f"percentage at target = {calc_target_ray_number(point_x, point_y, final_spot_size):.2f}%")
    plt.xlabel("Final Spot Size (mm)")
    plt.ylabel("Percentage of Rays inside Spot Size (%)")
    plt.axvline(final_spot_size, color='red', linestyle='--', label=f'Target Spot Size={final_spot_size:.2f}mm')
    plt.legend()
  # test_radius(Lens1)

  return Comp, IP2

def calc_target_ray_number(point_x, point_y, final_spot_size):
  return np.sum( (np.abs(point_x)<=final_spot_size/2) & (np.abs(point_y)<=final_spot_size/2) ) / len(point_x) * 100

def generate_file_name(focal_length, biconvex, aperture, pump_magnification, add_telescope=False, add_text="", add_propagation=0):
  if add_text != "":
    add_text = "_"+add_text
  lens_type = "biconvex" if biconvex else "planoconvex"
  telescope_str = "_telescope" if add_telescope else ""
  return os.path.join(Folder,"plots",f"spot_diagram_{lens_type}_f{focal_length}mm_D{aperture:.1f}mm_M{pump_magnification}{telescope_str}_{add_propagation}mm-from-focus{add_text}.pdf")

def generate_title(focal_length, biconvex, aperture, pump_magnification):
  lens_type = "Biconvex" if biconvex else "Planoconvex"
  return f"Spot Diagram of {lens_type} Lens (f={focal_length}mm, D={aperture:.1f}mm, M={pump_magnification})"

if freecad_da:
  clear_doc()

save = False

set_plot_params()

aperture = 3*inch
focal_length = 85
# Comp1, IP3 = test_composition(offset=0, f=focal_length, aperture=aperture, save=save, draw_spot_diagram=True, add_telescope=True)
Comp2, IP4 = test_composition(offset=0, f=focal_length, aperture=aperture, save=save, draw_spot_diagram=True, add_telescope=False, add_text="", add_propagation=-5)
# Comp2, IP2 = test_composition(offset=100, f=focal_length, aperture=aperture, biconvex=True, save=save)

if freecad_da:
  setview()