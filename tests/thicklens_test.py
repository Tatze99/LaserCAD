from LaserCAD.basic_optics import SquareBeam, Composition, Intersection_plane
from LaserCAD.freecad_models import clear_doc, setview, freecad_da
from LaserCAD.basic_optics.lens import Thicklens

def test_radius(Lens):
  n = Lens.refractive_index
  r = Lens.radius1()
  r2 = Lens.radius2()

  print("lens radii:", r, r2)
  print(f"lens focal length: {1/((n-1)*(2/r-(n-1)*Lens.thickness/(n*r**2)))}mm")

if freecad_da:
  clear_doc()

prop1 = 100
prop2 = 150
prop3 = 30

Comp1 = Composition()

Beam1 = SquareBeam(radius=20, ray_in_line=5)

Comp1.set_light_source(Beam1)
Comp1.propagate(prop1)
Lens1 = Thicklens(f=85, n=1.515, aperture=75)
Comp1.add_on_axis(Lens1)
Comp1.propagate(prop2)
IP1 = Intersection_plane()
Comp1.add_on_axis(IP1)
IP1.draw()
Comp1.propagate(prop3)
Comp1.draw()

IP1.spot_diagram(Comp1._beams[1])


Comp2 = Composition()
Comp2.pos -= (0,100,0)
Beam2 = SquareBeam(radius=20, ray_in_line=5)

Comp2.set_light_source(Beam2)
Comp2.propagate(prop1)
Lens2 = Thicklens(f=85, n=1.515, aperture=75, biconvex=True)
Comp2.add_on_axis(Lens2)
Comp2.propagate(prop2)
IP2 = Intersection_plane()
Comp2.add_on_axis(IP2)
IP2.draw()
Comp2.propagate(prop3)
Comp2.draw()
IP2.spot_diagram(Comp2._beams[1])

test_radius(Lens1)
test_radius(Lens2)

if freecad_da:
  setview()