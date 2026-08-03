import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# Configuration
folder = r"C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot"
csv_files = glob.glob(os.path.join(folder, "*_interface_data_t10800.csv"))

if not csv_files:
    print("No interface data CSV files found. Please run the extraction script first!")
    exit(1)

# Set professional plotting style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Custom color palette for pressures
color_map = {
    'p1': '#e41a1c',   # Red for 1 MPa
    'p3': '#377eb8',   # Blue for 3 MPa
    'p5': '#4daf4a',   # Green for 5 MPa
    'p10': '#984ea3'   # Purple for 10 MPa
}

for csv_path in sorted(csv_files):
    filename = os.path.basename(csv_path)
    # Parse pressure name from file name (e.g., final_v2_p5_interface_data_t10800.csv -> p5)
    pressure_key = 'p1'
    for key in color_map.keys():
        if "_" + key + "_" in filename:
            pressure_key = key
            break
            
    pressure_label = pressure_key.replace("p", "") + " MPa"
    
    import numpy as np
    # Read data
    df = pd.read_csv(csv_path)
    
    # 2차원 quadratic element(CPE8)의 corner/midside 노드 간 응력 진동(numerical oscillation)을 완화하기 위해 이동 평균 적용
    df['S22_Stress'] = df['S22_Stress'].rolling(window=5, center=True, min_periods=1).mean()
    df['U2_Displacement'] = df['U2_Displacement'].rolling(window=5, center=True, min_periods=1).mean()
    
    # Plot S22 on ax1
    ax1.plot(df['X_coordinate'], df['S22_Stress'], 
             color=color_map.get(pressure_key, '#000000'), 
             linewidth=2.5, 
             label=pressure_label)
             
    # Plot U2 on ax2
    # Convert displacement to micrometers (if it is already in micro, keep as is, it's 1:1)
    ax2.plot(df['X_coordinate'], df['U2_Displacement'], 
             color=color_map.get(pressure_key, '#000000'), 
             linewidth=2.5, 
             label=pressure_label)

# Format S22 plot (Top)
ax1.set_title("Normal Stress $S_{22}$ along the Interface ($t = 10,800$ s)", fontsize=14, fontweight='bold', pad=10)
ax1.set_ylabel("Normal Stress $S_{22}$ (MPa)", fontsize=12, fontweight='bold')
ax1.axvspan(9.0, 11.0, color='grey', alpha=0.15, label='Coldspot Zone ($x=9\\sim 11$)')
ax1.axhline(0, color='black', linewidth=1.0, linestyle='--')
ax1.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='none', shadow=True)
ax1.tick_params(labelsize=11)

# Format U2 plot (Bottom)
ax2.set_title("Displacement $U_2$ along the Interface ($t = 10,800$ s)", fontsize=14, fontweight='bold', pad=10)
ax2.set_xlabel("Position $X$ ($\\mu$m)", fontsize=12, fontweight='bold')
ax2.set_ylabel("Displacement $U_2$ ($\\mu$m)", fontsize=12, fontweight='bold')
ax2.axvspan(9.0, 11.0, color='grey', alpha=0.15)
ax2.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='none', shadow=True)
ax2.tick_params(labelsize=11)

plt.tight_layout()

# Save comparison image
output_path = os.path.join(folder, "interface_comparison_t10800.png")
plt.savefig(output_path, dpi=300)
print("SUCCESS: Comparison graph saved to " + output_path)
plt.close()
