import os
import sqlite3
import platform
# Environment variables need to be handled
if platform.system() == 'Windows':
    os.environ['PATH'] = os.environ['PATH'] + ';' + 'C:/Spatialite'
    os.environ['SPATIALITE_SECURITY'] = 'relaxed'# DOES THIS NEED TO BE RUN BEFORE EVERY CONNECTION????? ?NOT WORKING  ???????????

connection = sqlite3.connect("P:/Proj3/USGap/Vert/USRanges/2020v1/Results/mhoskx2020v1.sqlite")
cursor = connection.cursor()
os.putenv('SPATIALITE_SECURITY', 'relaxed')
connection.enable_load_extension(True)
cursor.execute('SELECT load_extension("mod_spatialite");')
################################################################################

outDir = 'P:/Proj3/USGap/Vert/USRanges/2020v1/Results/'
gap_id = 'messkx'

sql = """SELECT UPDATE presence SET age_of_last = 999 WHERE age_of_last IS NULL;"""
try:
    a = cursor.execute(sql).fetchall()
    print(a)
except Exception as e:
    print(e)

connection.commit()
connection.close()
