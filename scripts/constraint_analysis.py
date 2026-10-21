import numpy as np
import matplotlib.pyplot as plt

# --- EIDOLON AESTHETIC ---
plt.style.use('dark_background')

# --- PHYSICAL CONSTANTS & TARGETS ---
W0_kg = 750.0                 # Gross Weight (kg)
W0_N = W0_kg * 9.80665        # Gross Weight (N)
rho0, rho_cruise, rho_ceil = 1.225, 1.0581, 0.9093

# Targets in m/s
V_max = 225.0 / 3.6       
V_cr = 200.0 / 3.6         
V_stall = 85.0 / 3.6               
ROC_0, ROC_ceil = 3.0, 0.5                

# Aerodynamic Estimates
CD0, AR, e = 0.024, 8.5, 0.80                      
K = 1.0 / (np.pi * e * AR)    
CL_max = 1.8                  

# --- WING LOADING ARRAY (W/S) ---
WS = np.linspace(200, 1000, 500)

# --- CONSTRAINT EQUATIONS ---
# 1. Stall Limit
WS_stall = 0.5 * rho0 * (V_stall**2) * CL_max

# 2. Max Speed Limit
q_max = 0.5 * rho0 * (V_max**2)
TW_max = (q_max * CD0 / WS) + (K * WS / q_max)

# 3. Cruise Speed Limit
q_cr = 0.5 * rho_cruise * (V_cr**2)
TW_cruise = (q_cr * CD0 / WS) + (K * WS / q_cr)

# 4. Rate of Climb Limit
V_vy = np.sqrt((2.0 / rho0) * WS * np.sqrt(K / CD0))
TW_ROC = (ROC_0 / V_vy) + 2.0 * np.sqrt(CD0 * K)

# 5. Service Ceiling Limit
sigma_ceil = rho_ceil / rho0
TW_ceiling = (1.0 / sigma_ceil) * ((ROC_ceil / V_vy) + 2.0 * np.sqrt(CD0 * K))

# --- DESIGN POINT SELECTION ---
WS_design = 520.0
TW_design = max(np.interp(WS_design, WS, TW_max), np.interp(WS_design, WS, TW_ROC)) * 1.15 

# --- TERMINAL OUTPUT ---
print("\n[ EIDOLON SIZING MATRIX INITIATED ]")
print(f"Optimal Wing Area (S):    {W0_N / WS_design:.2f} m^2")
print(f"Required Engine Power:    {(TW_design * W0_N * V_max) / (0.75 * 1000.0):.2f} kW\n")

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
ax.plot(WS, TW_max, color='#ff3366', linewidth=2, label='Max Speed (225 km/h)')
ax.plot(WS, TW_cruise, color='#00ffcc', linestyle='--', linewidth=1.5, label='Cruise (200 km/h)')
ax.plot(WS, TW_ROC, color='#33ccff', linewidth=2, label='Rate of Climb (3 m/s)')
ax.plot(WS, TW_ceiling, color='#cc66ff', linestyle='-.', linewidth=1.5, label='Ceiling (3000m)')
ax.axvline(x=WS_stall, color='#ffcc00', linestyle=':', linewidth=2, label='Stall Limit')

ax.plot(WS_design, TW_design, 'wo', markersize=8, label='Eidolon Design Point')
ax.fill_between(WS, np.maximum(TW_max, TW_ROC), 1.0, where=(WS <= WS_stall), color='#33ccff', alpha=0.1)

ax.set_title('PROJECT EIDOLON: Algorithmic Constraint Analysis', fontsize=14, fontweight='bold', color='white')
ax.set_xlabel('Wing Loading (W/S) [N/m²]', fontsize=11, color='#cccccc')
ax.set_ylabel('Thrust-to-Weight Ratio (T/W)', fontsize=11, color='#cccccc')
ax.set_xlim([200, 1000])
ax.set_ylim([0.05, 0.40])
ax.grid(True, color='#333333', linestyle='--')
ax.legend(loc='upper left', facecolor='#111111', edgecolor='#333333', labelcolor='white')

plt.tight_layout()
plt.savefig('../docs/eidolon_constraint_graph.png', facecolor=fig.get_facecolor())
print("[ EIDOLON SIZING GRAPH EXPORTED TO /docs ]\n")

