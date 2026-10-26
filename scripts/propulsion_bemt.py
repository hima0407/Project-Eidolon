"""
Blade Element Momentum Theory (BEMT) Solver
Project Eidolon - Propulsion Architecture Validation
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class PropellerBEMT:
    def __init__(self, diameter: float, blades: int, velocity: float, rpm: float):
        self.D = diameter
        self.R = diameter / 2.0
        self.B = blades
        self.V_inf = velocity
        self.RPM = rpm
        self.n = rpm / 60.0
        self.omega = 2 * np.pi * self.n
        self.rho = 1.225 # Standard Sea Level (kg/m^3)
        
    def execute_solver(self, pitch_angle_deg: float):
        """Runs the iterative BEMT convergence loop across the blade span."""
        r_R = np.linspace(0.15, 0.98, 100)
        r = r_R * self.R
        
        # Blade Geometry (Chord and Twist)
        chord = 0.12 * np.sqrt(1 - r_R**2) + 0.05
        theta_75 = np.deg2rad(pitch_angle_deg)
        beta = theta_75 * (0.75 / r_R)**0.8
        
        dT = np.zeros_like(r)
        dQ = np.zeros_like(r)
        
        for i in range(len(r)):
            rad, c, theta = r[i], chord[i], beta[i]
            a, b = 0.1, 0.01 # Initial induction factors
            
            for _ in range(100): # Convergence limit
                V_axial = self.V_inf * (1 + a)
                V_rot = self.omega * rad * (1 - b)
                phi = np.arctan2(V_axial, V_rot)
                alpha = theta - phi
                
                # Airfoil Aerodynamics (Simplified NLF)
                Cl = 6.2 * alpha
                Cd = 0.008 + 0.005 * Cl**2
                
                # Tip Loss Factor (Prandtl)
                f = (self.B / 2) * (1 - rad/self.R) / (np.sin(phi) + 1e-6)
                F = (2/np.pi) * np.arccos(np.exp(-np.clip(f, 0, 50)))
                if np.isnan(F) or F < 0.01: F = 0.01
                
                sigma = (self.B * c) / (2 * np.pi * rad)
                
                # Analytical Update
                K_T = sigma * (Cl * np.cos(phi) - Cd * np.sin(phi))
                K_Q = sigma * (Cl * np.sin(phi) + Cd * np.cos(phi))
                
                a_new = K_T / (4 * F * np.sin(phi)**2 - K_T + 1e-6)
                b_new = K_Q / (4 * F * np.sin(phi) * np.cos(phi) + K_Q + 1e-6)
                
                a = 0.1 * a_new + 0.9 * a
                b = 0.1 * b_new + 0.9 * b
                
            V_local = np.sqrt(V_axial**2 + V_rot**2)
            dT[i] = 0.5 * self.rho * V_local**2 * self.B * c * (Cl * np.cos(phi) - Cd * np.sin(phi))
            dQ[i] = 0.5 * self.rho * V_local**2 * self.B * c * rad * (Cl * np.sin(phi) + Cd * np.cos(phi))
            
        T_total = np.trapezoid(dT, r)
        Q_total = np.trapezoid(dQ, r)
        P_total = Q_total * self.omega
        eta_prop = (T_total * self.V_inf) / P_total
        
        return eta_prop, T_total, P_total

if __name__ == "__main__":
    # Eidolon Target Specs
    solver = PropellerBEMT(diameter=1.75, blades=3, velocity=55.56, rpm=2400)
    eta, thrust, power = solver.execute_solver(pitch_angle_deg=28.5)
    
    print(f"--- PROJECT EIDOLON: PROPULSION BEMT ---")
    print(f"Advance Ratio (J):   {solver.V_inf / (solver.n * solver.D):.3f}")
    print(f"Mean Efficiency:     {eta * 100:.2f} %")
    print(f"Total Thrust:        {thrust:.2f} N")
    print(f"Power Absorbed:      {power / 1000:.2f} kW")
    print(f"----------------------------------------")

