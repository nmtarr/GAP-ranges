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
################################################################################

outDir = 'P:/Proj3/USGap/Vert/USRanges/2020v1/Results/'
gap_id = 'mstskx'

sql="""
SELECT ExportSHP('presence', 'geom_4326', '{0}{1}2020v1_4326', 'utf-8');
""".format(outDir, gap_id)
try:
    cursor.executescript(sql)
    print('Exported shapefile : ' + str(datetime.now() - time1))
except Exception as e:
    print(e)
