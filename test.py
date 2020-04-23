import os
import sqlite3
import platform
# Environment variables need to be handled
if platform.system() == 'Windows':
    os.environ['PATH'] = os.environ['PATH'] + ';' + 'C:/Spatialite'
    os.environ['SPATIALITE_SECURITY'] = 'relaxed'# DOES THIS NEED TO BE RUN BEFORE EVERY CONNECTION????? ?NOT WORKING  ???????????

connection = sqlite3.connect("P:/Proj3/USGap/Vert/USRanges/2020v1/Results/messkx2020v1.sqlite")
cursor = connection.cursor()
os.putenv('SPATIALITE_SECURITY', 'relaxed')
connection.enable_load_extension(True)
cursor.execute('SELECT load_extension("mod_spatialite");')
################################################################################

outDir = 'P:/Proj3/USGap/Vert/USRanges/2020v1/Results/'
gap_id = 'messkx'

sql="""
DROP TABLE out;
CREATE TABLE out AS SELECT geom_4326, age_of_last AS age, presence_2020v1 AS presence
                    FROM presence;
SELECT RecoverGeometryColumn('out', 'geom_4326', 4326, 'POLYGON', 'XY');
SELECT ExportSHP('out', 'geom_4326', '{0}{1}out', 'utf-8');
""".format(outDir, gap_id)

try:
    cursor.executescript(sql)
except Exception as e:
    print(e)

connection.commit()
connection.close()
