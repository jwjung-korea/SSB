import os
from abaqus import *
from abaqusConstants import *
import visualization
import xyPlot

# Configuration
folder = r"C:\Abaqus_Work\lithium_electrodeposition\elastic_plastic_coldspot"
target_time = 10800.0  # 2.5 cycles (Plating end, max expansion)

# Scan folder for ODBs
odbs_to_process = []
for filename in os.listdir(folder):
    if filename.endswith(".odb") and filename.startswith("final_v2_p"):
        odbs_to_process.append(os.path.join(folder, filename))

print("Found ODBs to process: " + str(odbs_to_process))

for odb_path in odbs_to_process:
    odb_name = os.path.basename(odb_path)
    csv_name = odb_name.replace(".odb", "_interface_data_t10800.csv")
    csv_path = os.path.join(folder, csv_name)
    
    print("--------------------------------------------------")
    print("Processing: " + odb_name)
    
    try:
        odb = session.openOdb(name=odb_path)
        step = odb.steps['Step-1']
        
        # Find frame closest to target_time
        closest_frame_index = 0
        min_diff = 999999.0
        for idx, frame in enumerate(step.frames):
            diff = abs(frame.frameValue - target_time)
            if diff < min_diff:
                min_diff = diff
                closest_frame_index = idx
                
        closest_frame = step.frames[closest_frame_index]
        actual_time = closest_frame.frameValue
        print("Closest frame index: " + str(closest_frame_index) + " (Time: " + str(actual_time) + " s)")
        
        # Open in viewport to allow path extraction
        session.viewports[session.currentViewportName].setValues(displayedObject=odb)
        session.viewports[session.currentViewportName].odbDisplay.setFrame(step='Step-1', frame=closest_frame_index)
        
        # Get nodes from LITHIUM_INST at Y=5.0 (undeformed coordinate)
        # These are the nodes on the bottom surface of the Lithium instance (contact interface)
        instance = odb.rootAssembly.instances['LITHIUM_INST']
        nodes_y5 = []
        for node in instance.nodes:
            if abs(node.coordinates[1] - 5.0) < 1e-4:
                nodes_y5.append((node.coordinates[0], node.label))
        
        # Sort nodes by X coordinate to ensure path goes from left to right
        nodes_y5.sort()
        node_labels = [label for x, label in nodes_y5]
        
        # Create Path using NODE_LIST (only Lithium nodes)
        path_name = 'lithium_interface_path'
        if path_name in session.paths:
            del session.paths[path_name]
            
        node_list_expr = (('LITHIUM_INST', tuple(node_labels)), )
        my_path = session.Path(name=path_name, type=NODE_LIST, expression=node_list_expr)
        
        # Extract S22 along path (undeformed shape, tracking material points)
        s22_data = xyPlot.XYDataFromPath(
            path=my_path, 
            includeIntersections=False,
            shape=UNDEFORMED,
            pathStyle=PATH_POINTS,
            labelType=TRUE_DISTANCE,
            name='s22_data_temp',
            variable=('S', INTEGRATION_POINT, ((COMPONENT, 'S22'), ))
        )
        
        # Extract U2 along path
        u2_data = xyPlot.XYDataFromPath(
            path=my_path, 
            includeIntersections=False,
            shape=UNDEFORMED,
            pathStyle=PATH_POINTS,
            labelType=TRUE_DISTANCE,
            name='u2_data_temp',
            variable=('U', NODAL, ((COMPONENT, 'U2'), ))
        )
        
        # Convert to dictionary of x -> y
        s22_dict = {}
        for x_val, y_val in s22_data.data:
            s22_dict[round(x_val, 5)] = y_val
            
        u2_dict = {}
        for x_val, y_val in u2_data.data:
            u2_dict[round(x_val, 5)] = y_val
            
        # Get sorted list of x coordinates
        all_x = sorted(list(set(s22_dict.keys()).union(set(u2_dict.keys()))))
        
        # Save to CSV
        with open(csv_path, 'w') as f:
            f.write("X_coordinate,S22_Stress,U2_Displacement\n")
            for x in all_x:
                s22_val = s22_dict.get(x, 0.0)
                u2_val = u2_dict.get(x, 0.0)
                f.write("%f,%f,%f\n" % (x, s22_val, u2_val))
                
        print("SUCCESS: Saved data to " + csv_name)
        odb.close()
        
    except Exception as e:
        print("Error processing " + odb_name + ": " + str(e))

print("==================================================")
print("All done! Check your folder for CSV files.")
print("==================================================")
