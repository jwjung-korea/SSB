# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2017 replay file
# Internal Version: 2016_09_28-06.54.59 126836
# Run by 정진욱 on Tue May 26 19:49:25 2026
#

# from driverUtils import executeOnCaeGraphicsStartup
# executeOnCaeGraphicsStartup()
#: Executing "onCaeGraphicsStartup()" in the site directory ...
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(0.994792, 0.99537), width=146.433, 
    height=98.7407)
session.viewports['Viewport: 1'].makeCurrent()
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
execfile('extract_interface_data.py', __main__.__dict__)
#: Found ODBs to process: ['C:\\Abaqus_Work\\lithium_electrodeposition\\elastic_plastic_coldspot\\final_v2_p1.odb', 'C:\\Abaqus_Work\\lithium_electrodeposition\\elastic_plastic_coldspot\\final_v2_p10.odb', 'C:\\Abaqus_Work\\lithium_electrodeposition\\elastic_plastic_coldspot\\final_v2_p3.odb', 'C:\\Abaqus_Work\\lithium_electrodeposition\\elastic_plastic_coldspot\\final_v2_p5.odb']
#: --------------------------------------------------
#: Processing: final_v2_p1.odb
#: Model: C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/final_v2_p1.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     2
#: Number of Meshes:             2
#: Number of Element Sets:       5
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Closest frame index: 1082 (Time: 10797.7753906 s)
#: SUCCESS: Saved data to final_v2_p1_interface_data_t10800.csv
#: --------------------------------------------------
#: Processing: final_v2_p10.odb
#: Model: C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/final_v2_p10.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     2
#: Number of Meshes:             2
#: Number of Element Sets:       5
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Closest frame index: 1083 (Time: 10803.8964844 s)
#: SUCCESS: Saved data to final_v2_p10_interface_data_t10800.csv
#: --------------------------------------------------
#: Processing: final_v2_p3.odb
#: Model: C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/final_v2_p3.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     2
#: Number of Meshes:             2
#: Number of Element Sets:       5
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Closest frame index: 1083 (Time: 10800.7744141 s)
#: SUCCESS: Saved data to final_v2_p3_interface_data_t10800.csv
#: --------------------------------------------------
#: Processing: final_v2_p5.odb
#: Model: C:/Abaqus_Work/lithium_electrodeposition/elastic_plastic_coldspot/final_v2_p5.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     2
#: Number of Meshes:             2
#: Number of Element Sets:       5
#: Number of Node Sets:          5
#: Number of Steps:              1
#: Closest frame index: 1082 (Time: 10797.5253906 s)
#: SUCCESS: Saved data to final_v2_p5_interface_data_t10800.csv
#: ==================================================
#: All done! Check your folder for CSV files.
#: ==================================================
print 'RT script done'
#: RT script done
