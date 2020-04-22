import os
import sqlite3
import platform
# Environment variables need to be handled
if platform.system() == 'Windows':
    os.environ['PATH'] = os.environ['PATH'] + ';' + 'C:/Spatialite'
    os.environ['SPATIALITE_SECURITY'] = 'relaxed'# DOES THIS NEED TO BE RUN BEFORE EVERY CONNECTION????? ?NOT WORKING  ???????????

connection = sqlite3.connect("P:/Proj3/USGap/Vert/USRanges/2020v1/Results/mstskx2020v1.sqlite")
cursor = connection.cursor()
os.putenv('SPATIALITE_SECURITY', 'relaxed')
connection.enable_load_extension(True)
cursor.execute('SELECT load_extension("mod_spatialite");')

sql="""
/* NOTE:  The order of these statements matters and reflects their rank */
UPDATE presence SET presence_2020v1 = predicted_presence;
/* Reclass some values */
UPDATE presence SET presence_2020v1 = 3 WHERE presence_2020v1 in (1,2,3);
UPDATE presence SET presence_2020v1 = 2 WHERE documented_historical=1;
UPDATE presence SET presence_2020v1 = 1 WHERE documented_recent=1;
"""
try:
    cursor.executescript(sql)
except Exception as e:
    print(e)
