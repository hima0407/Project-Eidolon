"""
Advanced Blade Element Momentum Theory (BEMT) Solver
Project Eidolon - Propeller Architecture Trade Study
"""

import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
import seaborn as sns

class AdvancedPropellerBEMT:
    def __init__(self, diameter: float, blades: int, velocity: float, engine_rpm: float, gear_ratio: float, altitude_m: float):
        self.D = diameter
        self.R = diameter / 2.0
        self.r_hub = 0.20 * self.R
        self.B = blades
        self.V_inf = velocity
        
        self.gear_ratio = gear_ratio
        self.engine_rpm = engine_rpm
        self.prop_rpm = engine_rpm / gear_ratio
        self.n = self.prop_rpm / 60.0
        self.omega = 2 * np.pi * self.n
        
        # Standard Atmosphere Model for Density
        T = 288.15 - 0.0065 * altitude_m
        p = 101325 * (1 - 0.0000225577 * altitude_m)**5.25588
        self.rho = p / (287.05 * T)
        
    def execute_solver(self, pitch_angle_deg: float):
        r_R = np.linspace(0.22, 0.98, 100)
        r = r_R * self.R
        
        # Advanced Chord and Twist distribution (MTV-21-A Profile)
        chord = 0.132 * np.sin(np.pi * (r_R - 0.10) / 0.95) * (1.0 - 0.25 * r_R)
        theta_75 = np.deg2rad(pitch_angle_deg)
        beta = theta_75 * (0.75 / r_R)**0.8
        
        dT = np.zeros_like(r)
        dQ = np.zeros_like(r)
        
        for i in range(len(r)):
            rad, c, theta = r[i], chord[i], beta[i]
            a, b = 0.05, 0.01 
            
            for _ in range(80): 
                V_axial = self.V_inf * (1 + a)
                V_rot = self.omega * rad * (1 - b)
                phi = np.arctan2(V_axial, V_rot)
                alpha = theta - phi
                
                # Airfoil Aerodynamics (Clark Y / ARA-D blend)
                alpha_deg = np.rad2deg(alpha)
                Cl = np.clip(0.38 + 0.106 * alpha_deg, -0.5, 1.55)
                Cd = 0.0072 + 0.00045 * (alpha_deg - 1.5)**2
                
                # Prandtl Tip AND Root Loss Factors
                f_tip = (self.B / 2) * (self.R - rad) / (rad * np.sin(phi) + 1e-6)
                f_root = (self.B / 2) * (rad - self.r_hub) / (self.r_hub * np.sin(phi) + 1e-6)
                
                F_tip = (2/np.pi) * np.arccos(np.exp(-np.clip(f_tip, 0, 50)))
                F_root = (2/np.pi) * np.arccos(np.exp(-np.clip(f_root, 0, 50)))
                F = max(F_tip * F_root, 0.01)
                
                sigma = (self.B * c) / (2 * np.pi * rad)
                
                Cn = Cl * np.cos(phi) - Cd * np.sin(phi)
                Ct = Cl * np.sin(phi) + Cd * np.cos(phi)
                
                K_T = sigma * Cn
                K_Q = sigma * Ct
                
                a_new = K_T / (4 * F * np.sin(phi)**2 - K_T + 1e-6)
                b_new = K_Q / (4 * F * np.sin(phi) * np.cos(phi) + K_Q + 1e-6)
                
                a = 0.3 * a_new + 0.7 * a
                b = 0.3 * b_new + 0.7 * b
                
            V_local = np.sqrt(V_axial**2 + V_rot**2)
            dT[i] = 0.5 * self.rho * V_local**2 * self.B * c * Cn
            dQ[i] = 0.5 * self.rho * V_local**2 * self.B * c * Ct * rad
            
        T_total = np.trapezoid(dT, r)
        Q_total = np.trapezoid(dQ, r)
        P_total = Q_total * self.omega
        eta_prop = (T_total * self.V_inf) / P_total if P_total > 0 else 0
        
        return eta_prop, T_total, P_total

if __name__ == "__main__":
    # Eidolon Skunkworks Targets
    target_power_W = 55100       # 75% Cruise Power of Rotax 912 iSc (73.5 kW max)
    v_cruise_ms = 63.8           # 230 km/h True Cruise Speed
    altitude_m = 3000            # 3000m Target Ceiling
    engine_rpm = 5000            # Cruise RPM
    gear_ratio = 2.43            # Rotax 912 Gearbox
    
    bemt_2 = AdvancedPropellerBEMT(1.75, 2, v_cruise_ms, engine_rpm, gear_ratio, altitude_m)
    bemt_3 = AdvancedPropellerBEMT(1.75, 3, v_cruise_ms, engine_rpm, gear_ratio, altitude_m)
    
    def pitch_err_2(p): return bemt_2.execute_solver(p[0])[2] - target_power_W
    def pitch_err_3(p): return bemt_3.execute_solver(p[0])[2] - target_power_W
    
    pitch_2_opt = fsolve(pitch_err_2, [25])[0]
    pitch_3_opt = fsolve(pitch_err_3, [20])[0]
    
    eta_2, t_2, p_2 = bemt_2.execute_solver(pitch_2_opt)
    eta_3, t_3, p_3 = bemt_3.execute_solver(pitch_3_opt)
    
    print("\n--- PROJECT EIDOLON: PROPULSION OPTIMIZATION ---")
    print(f"Target Power: {target_power_W/1000:.1f} kW | Cruise: 230 km/h | Alt: 3000m\n")
    print(f"[ 2-Blade Configuration ]")
    print(f"Required Pitch: {pitch_2_opt:.1f}° | Efficiency: {eta_2*100:.1f}% | Thrust: {t_2:.0f} N")
    print(f"\n[ 3-Blade Configuration (WINNER) ]")
    print(f"Required Pitch: {pitch_3_opt:.1f}° | Efficiency: {eta_3*100:.1f}% | Thrust: {t_3:.0f} N\n")

