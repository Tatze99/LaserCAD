from LaserCAD.basic_optics import SquareBeam, Composition, Intersection_plane
from LaserCAD.freecad_models import clear_doc, setview, freecad_da
from LaserCAD.basic_optics.lens import Thicklens


if freecad_da:
  clear_doc()

C = Composition()

# B = SquareBeam(radius=25, ray_in_line=10)
B = Ray_Distribution(radius=pump_spot_size/2,angle=1.0*2.08*np.pi/180,wavelength=940E-6, steps=3)

C.set_light_source(B)
C.propagate(100)
a= Thicklens(f=85, n=1.515)
a.aperture = 75
C.add_on_axis(a)
C.propagate(150)
IP = Intersection_plane()
C.add_on_axis(IP)
IP.draw()
C.propagate(30)
C.draw()

IP.spot_diagram(C._beams[1])

radius = a.radius1()

print("Lens radius 1:", radius)
print("Lens focal length:", ((a.refractive_index-1)*(1/radius))**(-1))


b = Thicklens(f=150, biconvex=True)
n = b.refractive_index
R = b.radius1()
print("Biconvex lens radius 1:", R)
print("Biconvex lens focal length:", 1/((n-1)*(2/R-(n-1)*b.thickness/(n*R**2))))
b.draw()

if freecad_da:
  setview()