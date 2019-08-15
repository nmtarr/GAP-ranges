twsSpp = ["aCYTRx", "aWESPx", "bSHCOx", "mVASHh", "rBCCOx", "bTACRx", "aTSSAx", "bBBWAx", "rMEGAx", "rGHLIx", "mMAORn", "mSEWEa", "bCOMOx", "mMAORn", "aERBSx", "aSRBSx", "aVFSAx", "aSGCSx", "mLECHt", "rAZTUx", "rSOWAx", "mHASEx", "bWESAx", "rCHTUx", "mPJMOx", "rBMTUx", "mMEDEx", "rSIDEx", "bWTSWx", "rRNSNx"]

# Define a function for displaying the maps that will be created.


def MapShapefilePolygons(map_these, title):
    """
    Displays shapefiles on a simple CONUS basemap.  Maps are plotted in the order
    provided so put the top map last in the listself.  You can specify a column
    to map as well as custom colors for it.  This function may not be very robust
    to other applications.

    NOTE: The shapefiles have to be in WGS84 CRS.

    (dict, str) -> displays maps, returns matplotlib.pyplot figure

    Arguments:
    map_these -- list of dictionaries for shapefiles you want to display in
                CONUS. Each dictionary should have the following format, but
                some are unneccesary if 'column' doesn't = 'None'.  The critical
                ones are file, column, and drawbounds.  Column_colors is needed
                if column isn't 'None'.  Others are needed if it is 'None'.
                    {'file': '/path/to/your/shapfile',
                     'alias': 'my layer'
                     'column': None,
                     'column_colors': {0: 'k', 1: 'r'}
                    'linecolor': 'k',
                    'fillcolor': 'k',
                    'linewidth': 1,
                    'drawbounds': True
                    'marker': 's'}
    title -- title for the map.
    """
    # Packages needed for plotting
    import matplotlib.pyplot as plt
    from mpl_toolkits.basemap import Basemap
    import numpy as np
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import PathPatch

    # Basemap
    fig = plt.figure(figsize=(15,12))
    ax = plt.subplot(1,1,1)
    map = Basemap(projection='aea', resolution='l', lon_0=-95.5, lat_0=39.0,
                  height=3200000, width=5000000)
    map.drawcoastlines(color='grey')
    map.drawstates(color='grey')
    map.drawcountries(color='grey')
    map.fillcontinents(color='#a2d0a2',lake_color='#a9cfdc')
    map.drawmapboundary(fill_color='#a9cfdc')

    for mapfile in map_these:
        if mapfile['column'] == None:
            # Add shapefiles to the map
            if mapfile['fillcolor'] == None:
                map.readshapefile(mapfile['file'], 'mapfile',
                                  drawbounds=mapfile['drawbounds'],
                                  linewidth=mapfile['linewidth'],
                                  color=mapfile['linecolor'])
                # Empty scatter plot for the legend
                plt.scatter([], [], c='', edgecolor=mapfile['linecolor'],
                            alpha=1, label=mapfile['alias'], s=100,
                            marker=mapfile['marker'])

            else:
                map.readshapefile(mapfile['file'], 'mapfile',
                          drawbounds=mapfile['drawbounds'])
                # Code for extra formatting -- filling in polygons setting border
                # color
                patches = []
                for info, shape in zip(map.mapfile_info, map.mapfile):
                    patches.append(Polygon(np.array(shape), True))
                ax.add_collection(PatchCollection(patches,
                                                  facecolor= mapfile['fillcolor'],
                                                  edgecolor=mapfile['linecolor'],
                                                  linewidths=mapfile['linewidth'],
                                                  zorder=2))
                # Empty scatter plot for the legend
                plt.scatter([], [], c=mapfile['fillcolor'],
                            edgecolors=mapfile['linecolor'],
                            alpha=1, label=mapfile['alias'], s=100,
                            marker=mapfile['marker'])

        else:
            map.readshapefile(mapfile['file'], 'mapfile', drawbounds=mapfile['drawbounds'])
            for info, shape in zip(map.mapfile_info, map.mapfile):
                for thang in mapfile['column_colors'].keys():
                    if info[mapfile['column']] == thang:
                        x, y = zip(*shape)
                        map.plot(x, y, marker=None, color=mapfile['column_colors'][thang])

            # Empty scatter plot for the legend
            for seal in mapfile['column_colors'].keys():
                plt.scatter([], [], c=mapfile['column_colors'][seal],
                            edgecolors=mapfile['column_colors'][seal],
                            alpha=1, label=mapfile['value_alias'][seal],
                            s=100, marker=mapfile['marker'])

    # Legend -- the method that works is ridiculous but necessary; you have
    #           to add empty scatter plots with the symbology you want for
    #           each shapefile legend entry and then call the legend.  See
    #           plt.scatter(...) lines above.
    plt.legend(scatterpoints=1, frameon=True, labelspacing=1, loc='lower left',
               framealpha=1, fontsize='x-large')

    # Title
    plt.title(title, fontsize=20, pad=-40, backgroundcolor='w')
    return


def download_GAP_range_CONUS2001v1(gap_id, toDir):
    """
    Downloads GAP Range CONUS 2001 v1 file and returns path to the unzipped
    file.  NOTE: doesn't include extension in returned path so that you can
    specify if you want csv or shp or xml when you use the path.
    """
    import sciencebasepy
    import zipfile

    # Connect
    sb = sciencebasepy.SbSession()

    # Search for gap range item in ScienceBase
    gap_id = gap_id[0] + gap_id[1:5].upper() + gap_id[5]
    item_search = '{0}_CONUS_2001v1 Range Map'.format(gap_id)
    items = sb.find_items_by_any_text(item_search)

    # Get a public item.  No need to log in.
    rng =  items['items'][0]['id']
    item_json = sb.get_item(rng)
    get_files = sb.get_item_files(item_json, toDir)

    # Unzip
    rng_zip = toDir + item_json['files'][0]['name']
    zip_ref = zipfile.ZipFile(rng_zip, 'r')
    zip_ref.extractall(toDir)
    zip_ref.close()

    # Return path to range file without extension
    return rng_zip.replace('.zip', '')

def make_evaluation_db(eval_db, gap_id, inDir, shucLoc):
    """
    Builds an sqlite database in which to store range evaluation information.  
    shucloc needs to be eventually be replaced with ScienceBase download of shucs.
    
    Arguments:
    eval_db -- name of database to create for evaluation.
    gap_id -- gap species code. For example, 'bAMROx'
    shucLoc -- path to GAP's 12 digit hucs shapefile
    inDir -- project's input directory    
    """
    import sqlite3
    import pandas as pd
    import os

    # Delete db if it exists
    if os.path.exists(eval_db):
        os.remove(eval_db)

    # Create or connect to the database
    conn = sqlite3.connect(eval_db)
    cursor = conn.cursor()
    os.putenv('SPATIALITE_SECURITY', 'relaxed')
    conn.enable_load_extension(True)
    cursor.execute('SELECT load_extension("mod_spatialite")')
    cursor.execute('SELECT InitSpatialMetadata(1);')

    # Add Albers Conic Equal Area 102008 to the spatial sys ref tables
    cursor.execute("""/* Add Albers_Conic_Equal_Area 102008 to the spatial sys ref tables */
                 INSERT into spatial_ref_sys
                 (srid, auth_name, auth_srid, proj4text, srtext)
                 values (102008, 'ESRI', 102008, '+proj=aea +lat_1=20 +lat_2=60
                 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m
                 +no_defs ', 'PROJCS["North_America_Albers_Equal_Area_Conic",
                 GEOGCS["GCS_North_American_1983",
                 DATUM["North_American_Datum_1983",
                 SPHEROID["GRS_1980",6378137,298.257222101]],
                 PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],
                 PROJECTION["Albers_Conic_Equal_Area"],
                 PARAMETER["False_Easting",0],
                 PARAMETER["False_Northing",0],
                 PARAMETER["longitude_of_center",-96],
                 PARAMETER["Standard_Parallel_1",20],
                 PARAMETER["Standard_Parallel_2",60],
                 PARAMETER["latitude_of_center",40],
                 UNIT["Meter",1],AUTHORITY["EPSG","102008"]]');""")
    
    # Add the hucs shapefile to the db.
    cursor.execute("""SELECT ImportSHP(?, 'shucs', 'utf-8', 102008, 'geom_102008', 'HUC12RNG', 'POLYGON');""", (shucLoc,))

    # Load the GAP range csv, filter out some columns, rename others
    csvfile = inDir + gap_id + "_CONUS_RANGE_2001v1.csv"
    sp_range = pd.read_csv(csvfile)
    sp_range.to_sql('sp_range', conn, if_exists='replace', index=False)

    sql2="""
    ALTER TABLE sp_range RENAME TO garb;

    CREATE TABLE sp_range AS
                          SELECT strHUC12RNG,
                                 intGapOrigin AS intGAPOrigin,
                                 intGapPres AS intGAPPresence,
                                 intGapRepro AS intGAPReproduction,
                                 intGapSeas AS intGAPSeason,
                                 Origin AS strGAPOrigin,
                                 Presence AS strGAPPresence,
                                 Reproduction AS strGAPReproduction,
                                 Season AS strGAPSeason
                          FROM garb;
    DROP TABLE garb;
    """
    cursor.executescript(sql2)
    conn.commit()
    conn.close()
    del cursor

def get_GBIF_species_key(scientific_name):
    """
    Description: Species-concepts change over time, sometimes with a spatial
    component (e.g., changes in range delination of closely related species or
    subspecies).  Retrieval of data for the wrong species-concept would introduce
    error.  Therefore, the first step is to sort out species concepts of different
    datasets to identify concepts that can be investigated.

    For this project/effort, individual species-concepts will be identified,
    crosswalked to concepts from various datasets, and stored in a table within
    a database.

    For now, a single species has been manually entered into species-concepts
    for development.
    """
    from pygbif import species
    key = species.name_backbone(name = 'Lithobates capito', rank='species')['usageKey']
    return key

def evaluate_GAP_range(eval_id, gap_id, eval_db, outDir, codeDir, method='Proportion in polygon'):
    """
    Uses occurrence data collected with the occurrence records wrangler repo
    to evaluate the GAP range map for a species.  A table is created for the GAP
    range and columns reporting the results of evaluation and validation are
    populated after evaluating spatial relationships of occurrence records (circles)
    and GAP range.

    The results of this code are new columns in the GAP range table (in the db
    created for work in this repository) and a range shapefile.

    The primary use of code like this would be range evaluation and revision.

    Unresolved issues:
    1. Can the runtime be improved with spatial indexing?  Minimum bounding rectangle?
    3. Locations of huc files. -- can sciencebase be used?
    4. Condition data used on the parameters, such as filter_sets in the evaluations
       table.

    Arguments:
    eval_id -- name/code of the evaluation
    gap_id -- gap species code.
    eval_db -- path to the evaluation database.  It should have been created with 
                make_evaluation_db() so the schema is correct.
    outDir -- directory of 
    codeDir -- directory of code repo
    method -- evaluation method
    """
    
    import sqlite3
    import os

    # Range evaluation database.
    conn = sqlite3.connect(eval_db)
    cursor = conn.cursor()
    os.putenv('SPATIALITE_SECURITY', 'relaxed')
    conn.enable_load_extension(True)
    cursor.execute('SELECT load_extension("mod_spatialite")')

    cursor.executescript("""ATTACH DATABASE '{0}/evaluations.sqlite' AS params;""".format(codeDir))
        
    sql2="""
    /*#############################################################################
                                 Assess Agreement
     ############################################################################*/

    /*#########################  Which HUCs contain an occurrence?
     #############################################################*/
    /*  Intersect occurrence circles with hucs */
    CREATE TABLE green AS
                  SELECT shucs.HUC12RNG, ox.occ_id,
                  CastToMultiPolygon(Intersection(shucs.geom_102008,
                                                  ox.circle_albers)) AS geom_102008
                  FROM shucs, evaluation_occurrences AS ox
                  WHERE Intersects(shucs.geom_102008, ox.circle_albers);

    SELECT RecoverGeometryColumn('green', 'geom_102008', 102008, 'MULTIPOLYGON',
                                 'XY');

    /* In light of the error tolerance for the species, which occurrences can
       be attributed to a huc?  */
    CREATE TABLE orange AS
      SELECT green.HUC12RNG, green.occ_id,
             100 * (Area(green.geom_102008) / Area(ox.circle_albers))
                AS proportion_circle
      FROM green
           LEFT JOIN evaluation_occurrences AS ox
           ON green.occ_id = ox.occ_id
      WHERE proportion_circle BETWEEN (100 - (SELECT error_tolerance
                                              FROM params.evaluations
                                              WHERE evaluation_id = '{0}'
                                              AND species_id = '{1}'))
                              AND 100;

    /*  How many occurrences in each huc that had an occurrence? */
    ALTER TABLE sp_range ADD COLUMN eval_cnt INTEGER;

    UPDATE sp_range
    SET eval_cnt = (SELECT COUNT(occ_id)
                          FROM orange
                          WHERE HUC12RNG = sp_range.strHUC12RNG
                          GROUP BY HUC12RNG);


    /*  Find hucs that contained gbif occurrences, but were not in gaprange and
    insert them into sp_range as new records.  Record the occurrence count */
    INSERT INTO sp_range (strHUC12RNG, eval_cnt)
                SELECT orange.HUC12RNG, COUNT(occ_id)
                FROM orange LEFT JOIN sp_range ON sp_range.strHUC12RNG = orange.HUC12RNG
                WHERE sp_range.strHUC12RNG IS NULL
                GROUP BY orange.HUC12RNG;


    /*############################  Does HUC contain an occurrence?
    #############################################################*/
    ALTER TABLE sp_range ADD COLUMN eval INTEGER;

    /*  Record in sp_range that gap and gbif agreed on species presence, in light
    of the min_count for the species. */
    UPDATE sp_range
    SET eval = 1
    WHERE eval_cnt >= (SELECT min_count
                            FROM params.evaluations
                            WHERE evaluation_id = '{0}'
                            AND species_id = '{1}');


    /*  For new records, put zeros in GAP range attribute fields  */
    UPDATE sp_range
    SET intGAPOrigin = 0,
        intGAPPresence = 0,
        intGAPReproduction = 0,
        intGAPSeason = 0,
        eval = 0
    WHERE eval_cnt >= 0 AND intGAPOrigin IS NULL;


    /*###########################################  Validation column
    #############################################################*/
    /*  Populate a validation column.  If an evaluation supports the GAP ranges
    then it is validated */
    ALTER TABLE sp_range ADD COLUMN validated_presence INTEGER NOT NULL DEFAULT 0;

    UPDATE sp_range
    SET validated_presence = 1
    WHERE eval = 1;


    /*#############################################################################
                                   Export Maps
     ############################################################################*/
    /*  Create a version of sp_range with geometry  */
    CREATE TABLE new_range AS
                  SELECT sp_range.*, Transform(shucs.geom_102008, 4326) AS geom_4326
                  FROM sp_range LEFT JOIN shucs ON sp_range.strHUC12RNG = shucs.HUC12RNG;

    SELECT RecoverGeometryColumn('new_range', 'geom_4326', 4326, 'POLYGON', 'XY');

    SELECT ExportSHP('new_range', 'geom_4326', '{2}{1}_CONUS_Range_2001v1_eval',
                     'utf-8');

    /* Make a shapefile of evaluation results */
    CREATE TABLE eval AS
                  SELECT strHUC12RNG, eval, geom_4326
                  FROM new_range
                  WHERE eval >= 0;

    SELECT RecoverGeometryColumn('eval', 'geom_4326', 4326, 'POLYGON', 'XY');

    SELECT ExportSHP('eval', 'geom_4326', '{2}{1}_eval', 'utf-8');


    /*#############################################################################
                                 Clean Up
    #############################################################################*/
    /* sp_range is no longer needed, use new_range instead */
    DROP TABLE sp_range;
    DROP TABLE green;
    DROP TABLE orange;
    """.format(eval_id, gap_id, outDir)
    
    try:
        cursor.executescript(sql2)
    except Exception as e:
        print(e)
    
    conn.commit()
    conn.close()