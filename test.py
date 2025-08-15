# -*- coding: utf-8 -*-
"""
Created on Wed Dec 13 14:35:32 2023

@author: Martin
"""
import numpy as np

from LaserCAD.freecad_models import clear_doc, setview, freecad_da, model_mirror
from LaserCAD.basic_optics import Mirror, Beam, Composition, Component, inch, Curved_Mirror, Ray, Geom_Object
from LaserCAD.freecad_models.utils import thisfolder, load_STL
from LaserCAD.non_interactings import Crystal, Faraday_Isolator, Pockels_Cell, Lambda_Plate

if freecad_da:
  clear_doc()
  
comp1 = Composition()
comp1.propagate(200)
comp1.add_on_axis(Mirror(phi=90))
comp1.propagate(200)

  
beam = Beam(radius=1, angle=0)
beam.pos = [0,0,0]

Setup = Composition(name="Test")
Setup.set_light_source(beam)
Setup.propagate(100)
Setup.add_on_axis(Mirror(phi=90))
Setup.propagate(100)
Setup.add_on_axis(Mirror(phi=90))
Setup.propagate(100)

if freecad_da:
  Setup.draw()
  setview()