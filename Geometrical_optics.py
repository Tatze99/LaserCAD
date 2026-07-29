import sympy as sp
from sympy import symbols, Matrix
import numpy as np
from matplotlib import pyplot as plt

class JonesVector:
    """Jones vector with common polarization operations."""
    def __init__(self, x, y):
        self.vector = Matrix([sp.sympify(x), sp.sympify(y)])

    @property
    def x(self):
        return self.vector[0]

    @property
    def y(self):
        return self.vector[1]

    def norm(self):
        """Euclidean norm sqrt(|x|^2 + |y|^2)."""
        return sp.sqrt(sp.Abs(self.x) ** 2 + sp.Abs(self.y) ** 2)

    def normalize(self):
        """Normalize in-place to unit norm."""
        n = self.norm()
        if n == 0:
            raise ValueError("Cannot normalize a zero Jones vector.")
        self.vector /= n
        return self

    def apply_matrix(self, matrix):
        """Apply a Jones matrix and return a new JonesVector."""
        out = matrix * self.vector
        return JonesVector(out[0], out[1])

    def polarization_state(self):
        """Return ellipse angles (azimuth psi, ellipticity angle chi)."""
        ex = self.x
        ey = self.y
        s0 = sp.Abs(ex) ** 2 + sp.Abs(ey) ** 2
        if s0 == 0:
            raise ValueError("Polarization state is undefined for zero intensity.")

        s1 = sp.Abs(ex) ** 2 - sp.Abs(ey) ** 2
        s2 = 2 * sp.re(ex * sp.conjugate(ey))
        s3 = -2 * sp.im(ex * sp.conjugate(ey))

        psi = sp.atan2(s2, s1) / 2
        chi = sp.asin(s3 / s0) / 2
        return psi, chi

def rotation(matrix, theta):
    """Rotation matrix for angle theta"""
    rotation = Matrix([[sp.cos(theta), -sp.sin(theta)], [sp.sin(theta), sp.cos(theta)]])

    return rotation * matrix * rotation.T

class OpticalElement:
    """Base class for optical elements"""
    def get_matrix(self):
        raise NotImplementedError

class PolarizationElement:
    """Base class for polarization elements"""
    def get_matrix(self):
        raise NotImplementedError

# Optical elements
class FreeSpacePropagation(OpticalElement):
    """Free space propagation over distance d"""
    def __init__(self, d):
        self.d = d
    
    def get_matrix(self):
        return Matrix([[1, self.d], [0, 1]])

class Lens(OpticalElement):
    """Thin lens with focal length f"""
    def __init__(self, f):
        self.f = f
    
    def get_matrix(self):
        if self.f == 0:
            return Matrix([[1, 0], [0, 1]])  # Identity matrix for zero focal length
        else:
            return Matrix([[1, 0], [-1/self.f, 1]])

class CurvedMirror(OpticalElement):
    """Curved mirror with radius of curvature R, positive for concave (focusing), negative for convex (defocusing)"""
    def __init__(self, R):
        self.R = R
    
    def get_matrix(self):
        return Matrix([[1, 0], [-2/self.R, 1]])

# Polarization elements
class LinearPolarizer(PolarizationElement):
    """Linear polarizer at angle phi"""
    def __init__(self, theta):
        self.theta = theta
    
    def get_matrix(self):
        return rotation(Matrix([[1, 0], [0, 0]]), self.theta)

class GenericPhasePlate(PolarizationElement):
    """Generic phase plate with fast axis at angle theta"""
    def __init__(self, phi, theta):
        self.phi = phi
        self.theta = theta
    
    def get_matrix(self):
        return rotation(Matrix([[1, 0], [0, sp.exp(sp.I * self.phi)]]), self.theta)

class QuarterWavePlate(GenericPhasePlate):
    """Quarter wave plate with fast axis at angle theta"""
    def __init__(self, theta):
        super().__init__(phi=sp.pi/2, theta=theta)

class HalfWavePlate(GenericPhasePlate):
    """Half wave plate with fast axis at angle theta"""
    def __init__(self, theta):
        super().__init__(phi=sp.pi, theta=theta)

class Pockelscell(GenericPhasePlate):
    """Pockels cell with voltage-dependent phase shift phi and fast axis at angle 45°"""
    def __init__(self, phi):
        super().__init__(phi=phi, theta=sp.pi/4)

class OpticalSetup:
    """Calculates total matrix of an optical setup"""
    def __init__(self):
        self.elements = []
        self.total_matrix = Matrix([[1, 0], [0, 1]])  # Initialize total matrix as identity
    
    def add_element(self, element):
        self.elements.append(element)

    def remove_element(self, element):
        """Remove an element from the optical setup."""
        if element in self.elements:
            self.elements.remove(element)
        else:
            raise ValueError("Element not found in the optical setup.")
    
    def get_total_matrix(self):
        """Multiply matrices in reverse order (light propagates left to right)"""
        if not self.elements:
            return sp.eye(2)
        
        total_matrix = self.elements[-1].get_matrix()
        for element in reversed(self.elements[:-1]):
            total_matrix *= element.get_matrix()

        self.total_matrix = sp.simplify(total_matrix)
        return self.total_matrix 

    def get_matrix_at(self, z_target):
        """Calculate the total matrix up to a specific position z_target in the optical setup."""
        if not self.elements:
            return sp.eye(2)

        total_matrix = sp.eye(2)
        current_position = 0

        for element in self.elements:
            if isinstance(element, FreeSpacePropagation):
                current_position += element.d
                if current_position >= z_target:
                    total_matrix = FreeSpacePropagation(d=z_target - (current_position - element.d)).get_matrix() * total_matrix
                    break
            total_matrix = element.get_matrix()*total_matrix

        return sp.simplify(total_matrix)


    def get_matrix_elements(self):
        """Return the elements A, B, C, D of the total matrix."""
        total_matrix = self.get_total_matrix()
        return float(total_matrix[0, 0]), float(total_matrix[0, 1]), float(total_matrix[1, 0]), float(total_matrix[1, 1])

    def get_initial_q(self):
        """Calculate the initial q-parameter for the optical setup."""
        A, B, C, D = self.get_matrix_elements()
        return (A - D) / (2 * C) + 1j * np.sqrt(4 - (A + D) ** 2) / (2 * C)

    def get_q_at(self, z_target):
        """Calculate the q-parameter at a specific position z_target in the optical setup."""
        total_matrix = self.get_matrix_at(z_target)
        q_in = self.get_initial_q()
        A, B, C, D = float(total_matrix[0, 0]), float(total_matrix[0, 1]), float(total_matrix[1, 0]), float(total_matrix[1, 1])

        q_out = (A * q_in + B) / (C * q_in + D)
        return q_out

    def stability_condition(self):
        """Calculate the stability condition G = (A+D)/2 for the total matrix."""
        A, B, C, D = self.get_matrix_elements()
        G = sp.Abs(A + D) / 2
        return G

    def beam_waist_position(self):
        """Calculate the beam waist position z and Rayleigh range zR for the total matrix."""
        A, B, C, D = self.get_matrix_elements()
        z = (A - D) / (2 * C)

        return z

    def rayleigh_length(self):
        """Calculate the Rayleigh range zR for the total matrix."""
        A, B, C, D = self.get_matrix_elements()
        zR = sp.sqrt(4 - (A + D) ** 2) / (2 * C)

        return zR

    def beam_waist_radius(self, wavelength):
        """Calculate the beam waist radius w0 for the total matrix.
        wavelength: Wavelength of the light in the same units as the optical setup (e.g., mm).
        """
        zR = self.rayleigh_length()
        w0 = sp.sqrt(abs(zR) * wavelength / np.pi)

        return w0

def beam_radius_from_q(q, wavelength):
    """Calculate the beam radius w from the q-parameter and wavelength.
    q: Complex q-parameter (can be a sympy expression or a complex number).
    wavelength: Wavelength of the light in the same units as the optical setup (e.g., mm).
    """
    w = np.sqrt(1/abs(np.imag(1/q)) * wavelength / np.pi)

    return w
def polarization_round_trip():
    #######################################################
    # Polarization example:
    # Vertical polarizer -> Pockels cell(phi) -> QWP(theta)
    # -> back propagation through QWP(theta) -> Pockels cell(phi) -> vertical polarizer.
    phi, theta = symbols('phi theta', real=True)

    forward_path = [
        LinearPolarizer(0),
        Pockelscell(phi),
        QuarterWavePlate(theta),
        QuarterWavePlate(theta),
        Pockelscell(phi),
        LinearPolarizer(0)
    ]
    backward_path = list(reversed(forward_path))

    total_pol_matrix = sp.eye(2)
    for element in forward_path:
        total_pol_matrix = element.get_matrix() * total_pol_matrix
    total_pol_matrix = sp.simplify(total_pol_matrix)

    input_state = JonesVector(1, 0).normalize()
    input_intensity = sp.simplify(input_state.norm() ** 2)

    output_state = input_state.apply_matrix(total_pol_matrix)
    output_intensity = sp.simplify(output_state.norm() ** 2)

    transmission = sp.simplify(sp.trigsimp(output_intensity / input_intensity))
    psi_out, chi_out = output_state.polarization_state()


    print("\n--- Polarization round-trip example ---")
    print("Total Jones matrix (symbolic):")
    sp.pprint(total_pol_matrix)

    transmission_func = sp.lambdify((phi, theta), sp.re(transmission), modules="numpy")
    phi_values = np.linspace(0.0, 2.0 * np.pi, 500)
    theta_values = [np.pi/180*45, np.pi/180*55, np.pi/180*65, np.pi/180*75, np.pi/2]

    plt.figure(figsize=(9, 5))
    for theta_value in theta_values:
        transmission_values = transmission_func(phi_values, theta_value)
        plt.plot(
            phi_values,
            transmission_values,
            linewidth=2,
            label=rf"$\theta={theta_value*180/np.pi:.0f}^\circ$",
        )

    plt.title("Round-trip transmission vs Pockels-cell phase")
    plt.xlabel(r"$\phi$ (rad)")
    plt.ylabel(r"Transmission $I_{out}/I_{in}$")
    plt.xlim(0.0, 2.0 * np.pi)
    plt.ylim(0.0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    f1, f2, R, d, g, b = symbols('f1 f2 R d, g, b', positive=True, real=True)
    
    setup = OpticalSetup()
    setup.add_element(FreeSpacePropagation(g))
    setup.add_element(Lens(f1))
    setup.add_element(FreeSpacePropagation(f1+f2))
    setup.add_element(Lens(f2))
    setup.add_element(FreeSpacePropagation(b))


    total_matrix = setup.get_total_matrix()
    print("Total optical matrix:")
    print(total_matrix)
    print("\n")

    sp.pprint(total_matrix)
