"""
Aircraft Constraint Analysis & Engine Sizing Matrix
Project Eidolon - Piston-Propeller Architecture
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class EidolonSizer:
    def __init__(self):
        # Physical Constants
        self.W_kg = 750.0
        self.W_N = self.W_kg * 9.80665
        self.WS_design = 520.0
        
        # Atmospherics (kg/m^3)
        self.rho0 = 1.225
        self.rho_cr = 1.0581 
        self.rho_ceil = 0.9093 
        
        # Aerodynamics (NLF Profile)
        self.CD0 = 0.022
        self.e = 0.85
        self.AR = 8.55
        self.K = 1.0 / (np.pi * self.e * self.AR)
        self.CL_max = 2.1
        self.eta_p = 0.776  # BEMT verified

        # Mission Targets (m/s)
        self.V_stall = 85.0 / 3.6
        self.V_max = 225.0 / 3.6
        self.V_cr = 200.0 / 3.6
        self.ROC = 3.0
        self.ROC_ceil = 0.5

    def analyze(self):
        WS = np.linspace(200, 1000, 500)
        
        # 1. Stall Limit
        WS_stall = 0.5 * self.rho0 * (self.V_stall**2) * self.CL_max
        
        # 2. Max Speed (P/W)
        q_max = 0.5 * self.rho0 * self.V_max**2
        PW_max = (self.V_max / self.eta_p) * ((q_max * self.CD0 / WS) + (self.K * WS / q_max))
        
        # 3. Cruise (P/W)
        q_cr = 0.5 * self.rho_cr * self.V_cr**2
        PW_cr = (self.V_cr / self.eta_p) * ((q_cr * self.CD0 / WS) + (self.K * WS / q_cr))
        
        # 4. Rate of Climb (P/W)
        V_vy = np.sqrt((2.0 / self.rho0) * WS * np.sqrt(self.K / self.CD0))
        PW_roc = (self.ROC / self.eta_p) + (V_vy / self.eta_p) * (2.0 * np.sqrt(self.CD0 * self.K))
        
        # 5. Ceiling (P/W)
        sigma_ceil = self.rho_ceil / self.rho0
        PW_ceil = (self.ROC_ceil / self.eta_p) + (V_vy / (self.eta_p * np.sqrt(sigma_ceil))) * (2.0 * np.sqrt(self.CD0 * self.K))
        
        # Identify Target
        PW_design = max(np.interp(self.WS_design, WS, PW_max), 
                        np.interp(self.WS_design, WS, PW_roc), 
                        np.interp(self.WS_design, WS, PW_cr)) * 1.05 # 5% Engine margin
        
        # Convert PW (W/N) back to absolute HP
        engine_watts = PW_design * self.W_N
        hp_req = engine_watts / 745.7

        print(f"\n[ EIDOLON POWER SIZING INITIATED ]")
        print(f"Optimal Wing Area (S):    {self.W_N / self.WS_design:.2f} m^2")
        print(f"Design Power Loading:     {PW_design:.2f} W/N")
        print(f"Minimum Engine Rating:    {hp_req:.1f} HP\n")
        
        self.plot(WS, WS_stall, PW_max, PW_cr, PW_roc, PW_ceil, PW_design)

    def plot(self, WS, WS_stall, PW_max, PW_cr, PW_roc, PW_ceil, PW_design):
        plt.style.use('dark_background')
        sns.set_palette("mako")
        fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
        
        ax.plot(WS, PW_max, color='#ff3366', linewidth=2, label='Max Speed (225 km/h)')
        ax.plot(WS, PW_cr, color='#00ffcc', linestyle='--', linewidth=1.5, label='Cruise (200 km/h)')
        ax.plot(WS, PW_roc, color='#33ccff', linewidth=2, label='Rate of Climb (3 m/s)')
        ax.plot(WS, PW_ceil, color='#cc66ff', linestyle='-.', linewidth=1.5, label='Ceiling (3000m)')
        ax.axvline(x=WS_stall, color='#ffcc00', linestyle=':', linewidth=2, label='Stall Limit')
        
        ax.plot(self.WS_design, PW_design, 'w*', markersize=14, label=f'Eidolon Design (P/W: {PW_design:.1f})')
        PW_feasible = np.maximum.reduce([PW_max, PW_cr, PW_roc, PW_ceil])
        ax.fill_between(WS, PW_feasible, 35, where=(WS <= WS_stall), color='#00ffcc', alpha=0.1)
        
        ax.set_title('PROJECT EIDOLON: Algorithmic Constraint Analysis', fontsize=14, fontweight='bold', color='white')
        ax.set_xlabel('Wing Loading (W/S) [N/m²]', fontsize=11, color='#cccccc')
        ax.set_ylabel('Power Loading (P/W) [W/N]', fontsize=11, color='#cccccc')
        ax.set_xlim([200, 1000])
        ax.set_ylim([0, 25])
        ax.grid(True, color='#333333', linestyle='--')
        ax.legend(loc='upper left', facecolor='#111111', edgecolor='#333333', labelcolor='white')
        
        plt.tight_layout()
        plt.savefig('../docs/eidolon_constraint_graph.png', facecolor=fig.get_facecolor())
        print("[ EIDOLON SIZING GRAPH EXPORTED TO /docs ]\n")

if __name__ == "__main__":
    EidolonSizer().analyze()

