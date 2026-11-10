from LaserCAD.non_interactings import Cylindric_Crystal
from LaserCAD.basic_optics import Beam, Composition, Unit_Mount, Composed_Mount, Post
from LaserCAD.freecad_models import freecad_da, setview, clear_doc
from LaserCAD.freecad_models.utils import thisfolder

class Crystal_with_mount(Composition):
    def __init__(self, name="Laser crystal", stl_file="Kuehlmount_Alumosilikatglas_d23.stl", housing_color = (212/255, 162/255, 78/255), thickness=4, flip=False, **kwargs):
        """Laser Crystal with Mount

        params: name: str, name of the crystal
                housing_color: tuple, RGB color of the housing
        """
        super().__init__(name=name,**kwargs)
        self.name = name 
        self.flip = flip
        self.stl_file = thisfolder + f"misc_meshes/{stl_file}"
        self.housing_color = housing_color  

        if stl_file == "Kuehlmount_Alumosilikatglas_d23.stl":
            aperture = 23
            geometry = "cylindrical"
      
        else:
            raise ValueError("Invalid .stl file or file not in database. Please add the aperture and geometry to the crystal.py file")


        if geometry == "cylindrical":
            crystal = Cylindric_Crystal(aperture=aperture, thickness=thickness)
        elif geometry == "rectangular":
            crystal = Crystal(width=aperture, height=aperture, thickness=thickness)

        crystal_housing = self.crystal_housing()
        self.add_on_axis(crystal_housing)
        self.add_on_axis(crystal)
        if self.flip:
            for element in self.non_opticals:
                element.rotate(self.get_coordinate_system()[2], np.pi)

    def crystal_housing(self):
        Crystal_housing = Component(name="Laser crystal housing")
        Crystal_housing.draw_dict["stl_file"] = self.stl_file
        Crystal_housing.freecad_model = load_STL
        Crystal_housing.draw_dict["color"] = self.housing_color

        return Crystal_housing
    
if freecad_da:
  clear_doc()

Setup = Composition()
beam = Beam(radius=2)

Setup.set_light_source(beam)
Setup.propagate(150)
# Setup.add_supcomposition_on_axis(Crystal_with_mount(flip=True))

copper_mount = Unit_Mount()
copper_mount.model = "Kuehlmount_Alumosilikatglas_d23"
copper_mount.path = thisfolder + "misc_meshes/"
copper_mount.draw_dict["color"] = (212/255, 162/255, 78/255)
copper_mount.docking_obj.pos += (6, 0, -20)

crystal_mount = Composed_Mount(name="crystal_mount")
crystal_mount.add(copper_mount)
crystal_mount.add(Post(model="0.5inch_post"))

crys = Cylindric_Crystal(aperture=23, thickness=4)
crys.set_mount(crystal_mount)


Setup.add_on_axis(crys)

print(copper_mount.draw_dict)

if freecad_da:
  Setup.draw()
  setview()