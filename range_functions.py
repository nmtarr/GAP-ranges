RangeCodesDict2001 = {"Presence": {1: "Known/extant",
                                   2: "Possibly present",
                                   3: "Potential for presence",
                                   4: "Extirpated/historical presence",
                                   5: "Extirpated purposely (applies to introduced species only)",
                                   6: "Occurs on indicated island chain",
                                   7: "Unknown"},
                "Origin": {1: "Native", 2: "Introduced", 3: "Either introducted or native",
                           4: "Reintroduced", 5: "Either introduced or reintroduced",
                           6: "Vagrant", 7: "Unknown"},
                "Reproduction": {1: "Breeding", 2: "Nonbreeding",
                                 3: "Both breeding and nonbreeding", 7: "Unknown"},
                 "Season": {1: "Year-round", 2: "Migratory", 3: "Winter", 4: "Summer",
                            5: "Passage migrant or wanderer", 6: "Seasonal permanence uncertain",
                            7: "Unknown", 8: "Vagrant"}}

RangeCodesDict2020 = {"Presence": {1: "Documented presence",
                                   2: "Documented historically presence",
                                   3: "Predicted presence",
                                   4: "Predicted extirpated/historical presence",
                                   5: "Predicted extirpated purposely (applies to introduced species only)",
                                   6: "Predicted occurs on indicated island chain",
                                   7: "Unknown"}}
def NB_get_filter_sets(occ_dbs):
    '''
    For the notebook.  Pulls names of filter sets used in the acquisition of
    occurrence records.
    '''
    import sqlite3
    ids = set([])
    r_s = set([])
    f_s = set([])
    for db in occ_dbs:
        connection = sqlite3.connect(db)
        req_id = connection.execute("""SELECT DISTINCT request_id
                                       FROM occurrences;""").fetchall()[0]
        filt_id = connection.execute("""SELECT DISTINCT filter_id
                                        FROM occurrences;""").fetchall()[0]
        r_s = r_s | set(req_id)
        f_s = f_s | set(filt_id)
        ids = ids | set(req_id) | set(filt_id)
        del connection
    filters_request = list(r_s)
    filters_post = list(f_s)
    ids = tuple(ids)
    filter_sets = ids[0]
    for i in ids[1:]:
        filter_sets = filter_sets + ', ' + i
    return (filter_sets, filters_request, filters_post)

def NB_insert_records(years, months, occ_dbs, eval_db):
    '''
    For the notebook.  Gets records from occurrence dbs and puts
    them into the evaluation db.
    '''
    for occ_db in occ_dbs:
        print(occ_db)

        # Connect to the evaluation occurrence records database
        cursor, evconn = functions.spatialite(eval_db)

        # Attach occurrence database
        cursor.execute("ATTACH DATABASE ? AS occs;", (occ_db,))

        # Create table of occurrences that fit within evaluation parameters  --  IF EXISTS JUST APPEND
        if occ_db == occ_dbs[0]:
            cursor.execute("""CREATE TABLE evaluation_occurrences AS
                           SELECT * FROM occs.occurrences
                           WHERE STRFTIME('%Y', OccurrenceDate) IN {0}
                           AND STRFTIME('%m', OccurrenceDate) IN {1};""".format(years, months))
        else:
            cursor.execute("""INSERT INTO evaluation_occurrences
                              SELECT * FROM occs.occurrences
                              WHERE STRFTIME('%Y', OccurrenceDate) IN {0}
                              AND STRFTIME('%m', OccurrenceDate) IN {1};""".format(years, months))

    # Export occurrence circles as a shapefile (all seasons)
    cursor.execute("""SELECT RecoverGeometryColumn('evaluation_occurrences', 'polygon_4326',
                      4326, 'POLYGON', 'XY');""")
    sql = """SELECT ExportSHP('evaluation_occurrences', 'polygon_4326', ?, 'utf-8');"""
    subs = outDir + summary_name + "_circles"
    cursor.execute(sql, (subs,))
    '''
    # Export occurrence 'points' as a shapefile (all seasons)
    cursor.execute("""SELECT RecoverGeometryColumn('evaluation_occurrences', 'geom_xy4326',
                      4326, 'POINT', 'XY');""")
    subs = outDir + summary_name + "_points"
    cursor.execute("""SELECT ExportSHP('evaluation_occurrences', 'geom_xy4326', ?, 'utf-8');""", (subs,))
    '''
    # Close db
    evconn.commit()
    evconn.close()

def getRecordDetails(key):
    """
    Returns a dictionary holding all GBIF details about the record.

    Example: details = getRecordDetails(key = 1265907957)
    """
    from pygbif import occurrences
    details = occurrences.get(key = key)
    return details

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

def spatialite(db):
    """
    Creates a connection and cursor for sqlite db and enables
    spatialite extension and shapefile functions.

    (db) --> cursor, connection

    Arguments:
    db -- path to the db you want to create or connect to.
    """
    import os
    import sqlite3
    import platform
    # Environment variables need to be handled
    if platform.system() == 'Windows':
        os.environ['PATH'] = os.environ['PATH'] + ';' + 'C:/Spatialite'
        os.environ['SPATIALITE_SECURITY'] = 'relaxed'# DOES THIS NEED TO BE RUN BEFORE EVERY CONNECTION????? ?NOT WORKING  ???????????

    if platform.system() == 'Darwin':  # DOES THIS NEED TO BE RUN BEFORE EVERY CONNECTION?????????????????
        #os.putenv('SPATIALITE_SECURITY', 'relaxed')
        os.environ['SPATIALITE_SECURITY'] = 'relaxed'
    connection = sqlite3.connect(db)
    cursor = connection.cursor()
    os.putenv('SPATIALITE_SECURITY', 'relaxed')
    connection.enable_load_extension(True)
    cursor.execute('SELECT load_extension("mod_spatialite");')
    return cursor, connection

def MapShapefilePolygons(map_these, title):
    """
    Displays shapefiles on a simple CONUS basemap.  Maps are plotted in the order
    provided so put the top map last in the listself.  You can specify a column
    to map as well as custom colors for it.  This function may not be very robust
    to other applications.

    NOTE: The shapefiles have to be in WGS84 CRS.

    (list, str) -> displays maps, returns matplotlib.pyplot figure

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

def make_evaluation_db(eval_db, gap_id, inDir, outDir, shucLoc):
    """
    Builds an sqlite database in which to store range evaluation information.
    shucloc needs to be eventually be replaced with ScienceBase download of shucs.

    Tables created:
    range_2001v1 -- the range data downloaded from ScienceBase.
    shucs -- 12 digit gap hucs coverage.
    presence_2020v1 -- where data on predicted and documented presence is stored.

    Arguments:
    eval_db -- name of database to create for evaluation.
    gap_id -- gap species code. For example, 'bAMROx'
    shucLoc -- path to GAP's 12 digit hucs shapefile
    inDir -- project's input directory
    outDir -- output directory for this repo
    """
    import sqlite3
    import pandas as pd
    import os

    # Delete db if it exists
    if os.path.exists(eval_db):
        os.remove(eval_db)

    # Create the database
    cursorQ, conn = spatialite(eval_db)

    cursorQ.execute('SELECT InitSpatialMetadata(1);')

    ####################### ADD (s)HUCS
    cursorQ.execute("""SELECT ImportSHP(?, 'shucs', 'utf-8', 5070, 'geom_5070',
                                        'HUC12RNG', 'POLYGON');""", (shucLoc,))

    ###################### ADD 2001v1 RANGE
    csvfile = inDir + gap_id + "_CONUS_RANGE_2001v1.csv"
    sp_range = pd.read_csv(csvfile, dtype={'strHUC12RNG':str})
    sp_range.to_sql('range_2001v1', conn, if_exists='replace', index=False)
    conn.commit() # Commit and close here, reopen connection or else code throws errors.
    conn.close()

    cursorQ, conn = spatialite(eval_db)

    # Rename columns and drop some too.
    sql1 = """
    ALTER TABLE range_2001v1 RENAME TO garb;

    CREATE TABLE range_2001v1 AS SELECT strHUC12RNG,
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
    cursorQ.executescript(sql1)
    # Table to use for evaluations, renamed from 'presence' 14April2020.
    sql2 = """
    CREATE TABLE presence_2001v1 AS SELECT range_2001v1.strHUC12RNG, shucs.geom_5070
                             FROM range_2001v1 LEFT JOIN shucs
                                               ON range_2001v1.strHUC12RNG = shucs.HUC12RNG;

    /* Transform to 4326 for displaying purposes*/
    ALTER TABLE presence_2001v1 ADD COLUMN geom_4326 INTEGER;

    UPDATE presence_2001v1 SET geom_4326 = Transform(geom_5070, 4326);

    SELECT RecoverGeometryColumn('presence_2001v1', 'geom_4326', 4326, 'POLYGON', 'XY');

    SELECT ExportSHP('presence_2001v1', 'geom_4326', '{0}{1}_presence2001_4326', 'utf-8');
    """.format(outDir, gap_id)
    cursorQ.executescript(sql2)

    # Create a table to store presence information for range compilations.
    sql3 = """
    CREATE TABLE presence AS SELECT range_2001v1.strHUC12RNG,
                                    range_2001v1.intGAPPresence AS predicted_presence,
                                    shucs.geom_5070
                             FROM range_2001v1 LEFT JOIN shucs
                                               ON range_2001v1.strHUC12RNG = shucs.HUC12RNG;

    SELECT RecoverGeometryColumn('presence', 'geom_5070', 5070, 'POLYGON',
                                 'XY');

    /* Transform to 4326 for displaying purposes*/
    ALTER TABLE presence ADD COLUMN geom_4326 INTEGER;

    UPDATE presence SET geom_4326 = Transform(geom_5070, 4326);

    SELECT RecoverGeometryColumn('presence', 'geom_4326', 4326, 'POLYGON',
                                 'XY');

    SELECT ExportSHP('presence', 'geom_4326', '{0}{1}_presence_4326', 'utf-8');

    """.format(outDir, gap_id)
    try:
        cursorQ.executescript(sql3)
    except Exception as e:
        print(e)
    conn.commit()
    conn.close()
    del cursorQ

def compile_GAP_presence(eval_id, gap_id, eval_db, cutoff_year, parameters_db,
                         outDir, codeDir):
    """
    Uses occurrence data collected with the wildlife-wrangler repo
    to build an updated GAP range map for a species.  The previous GAP range
    is used along with recent and historic occurrence records acquired with
    the wildlife-wrangler.

    The results of this code are a new column in the GAP range table (in the db
    created for the task) and a range shapefile.

    Parameters:
    eval_id -- name/code for the update (e.g., 2020v1)
    gap_id -- gap species code.
    eval_db -- path to the evaluation database.  It should have been created with
                make_evaluation_db() so the schema is correct.
    cutoff_year -- year before which records are considered 'historical'.  Occurrence
                records from or more recent than the cutoff year will be
                considered 'recent'.
    parameters_db -- database with information on range update and evaluation
                criteria.
    outDir -- directory of
    codeDir -- directory of code repo
    """
    import sqlite3
    import os
    from datetime import datetime
    time0 = datetime.now()
    # Open evaluation db and attach the database with range processing parameters.
    cursor, conn = spatialite(eval_db)
    cursor.executescript("""ATTACH DATABASE '{0}'
                            AS params;""".format(parameters_db))

    ##############################################  Add some columns to presence
    ############################################################################
    sql="""
    ALTER TABLE presence ADD COLUMN documented_historical INT;
    ALTER TABLE presence ADD COLUMN documented_recent INT;
    ALTER TABLE presence ADD COLUMN age_of_last INT;
    ALTER TABLE presence ADD COLUMN presence_2020v1 INT;
    """
    try:
        cursor.executescript(sql)
        print("Added columns: " + str(datetime.now() - time0))
    except Exception as e:
        print(e)
        print("Some columns not added")

    ######################################### Which HUCs were recently occupied?
    ############################################################################
    """
    Get a table with occurrences from the right time period with the names of
    hucs that they intersect (proportion in polygon assessement comes later).
    intersected_recent -- occurrences of suitable age and the hucs they intersect at all.
             Records are fragments of circles after intersection with hucs.
    This ultimately populates the documented_recent column.
    """
    # First filter out records with unnacceptable dates to reduce workload
    # RECENT
    time1 = datetime.now()
    sql="""
    CREATE TABLE recent_records AS
                            SELECT *
                            FROM evaluation_occurrences
                            WHERE occurrenceDate {0}
    """.format('>=' + str(cutoff_year))
    try:
        cursor.executescript(sql)
        print("Isolated recent records: " + str(datetime.now()-time1))
    except Exception as e:
        print("!!! FAILED to filter for recent records")
        print(e)

    # HISTORIC
    time1 = datetime.now()
    sql="""
    CREATE TABLE historical_records AS
                            SELECT *
                            FROM evaluation_occurrences
                            WHERE occurrenceDate {0}
    """.format('<=' + str(cutoff_year))
    try:
        cursor.executescript(sql)
        print("Isolated historical records: " + str(datetime.now()-time1))
    except Exception as e:
        print("!!! FAILED to filter for historical records: " + str(datetime.now()-time1))
        print(e)


    # Intersect occurrence circles with hucs.
    # intersected_historical -- table with rows for intersected circles and hucs
    # HISTORICAL
    time1 = datetime.now()
    sql="""
    CREATE TABLE intersected_historical AS
                  SELECT shucs.HUC12RNG, ox.occ_id, ox.occurrenceDate, ox.weight,
                  CastToMultiPolygon(Intersection(shucs.geom_5070,
                                                  ox.polygon_5070)) AS geom_5070
                  FROM shucs, historical_records AS ox
                  WHERE Intersects(shucs.geom_5070, ox.polygon_5070);

    SELECT RecoverGeometryColumn('intersected_historical', 'geom_5070', 5070,
                                 'MULTIPOLYGON', 'XY');"""
    try:
        cursor.executescript(sql)
        print("Found hucs that intersect a historical occurrence: " + str(datetime.now()-time1))
    except Exception as e:
        print("!! FAILED to find hucs that intersect a recent occurrence: " + str(datetime.now()-time1))
        print(e)

    # RECENT
    time1 = datetime.now()
    sql="""
    CREATE TABLE intersected_recent AS
                 SELECT shucs.HUC12RNG, ox.occ_id, ox.occurrenceDate, ox.weight,
                 CastToMultiPolygon(Intersection(shucs.geom_5070,
                                                 ox.polygon_5070)) AS geom_5070
                 FROM shucs, recent_records AS ox
                 WHERE Intersects(shucs.geom_5070, ox.polygon_5070);

    SELECT RecoverGeometryColumn('intersected_recent', 'geom_5070', 5070,
                                 'MULTIPOLYGON', 'XY');"""
    try:
        cursor.executescript(sql)
        print("Found hucs that intersect a recent occurrence: " + str(datetime.now()-time1))
    except Exception as e:
        print("!! FAILED to find hucs that intersect a recent occurrence: " + str(datetime.now()-time1))
        print(e)

    # Filter out circle fragments that aren't big enough (% of total circle)
    """
    Use the error tolerance for the species to select those occurrences that
    can be attributed to a HUC.
    big_nuff_recent -- records from table intersected_recent that have
            enough overlap to attribute to a huc.
    big_nuff_historical -- records from table intersected_historical that have
            enough overlap to attribute to a huc.
    """
    time1 = datetime.now()
    sql="""
    CREATE TABLE big_nuff_recent AS
      SELECT intersected_recent.HUC12RNG,
             intersected_recent.occ_id,
             intersected_recent.occurrenceDate,
             intersected_recent.weight,
             100 * (Area(intersected_recent.geom_5070) / Area(ox.polygon_5070))
                AS proportion_circle
      FROM intersected_recent
           LEFT JOIN evaluation_occurrences AS ox
           ON intersected_recent.occ_id = ox.occ_id
      WHERE proportion_circle BETWEEN (100 - (SELECT error_tolerance
                                              FROM params.evaluations
                                              WHERE evaluation_id = '{0}'
                                              AND species_id = '{1}'))
                              AND 100;

    CREATE TABLE big_nuff_historical AS
      SELECT intersected_historical.HUC12RNG,
             intersected_historical.occ_id,
             intersected_historical.occurrenceDate,
             intersected_historical.weight,
             100 * (Area(intersected_historical.geom_5070) / Area(ox.polygon_5070))
                AS proportion_circle
      FROM intersected_historical
           LEFT JOIN evaluation_occurrences AS ox
           ON intersected_historical.occ_id = ox.occ_id
      WHERE proportion_circle BETWEEN (100 - (SELECT error_tolerance
                                              FROM params.evaluations
                                              WHERE evaluation_id = '{0}'
                                              AND species_id = '{1}'))
                              AND 100;
    """.format(eval_id, gap_id)
    try:
        cursor.executescript(sql)
        print('Determined which records overlap enough: ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)

    ################################ Add summed weight column
    # Column to make note of hucs in presence that have enough evidence
    time1 = datetime.now()
    sql="""
    ALTER TABLE presence ADD COLUMN recent_weight INT;

    UPDATE presence
    SET recent_weight = (SELECT SUM(weight)
                         FROM big_nuff_recent
                         WHERE HUC12RNG = presence.strHUC12RNG
                         GROUP BY HUC12RNG);

    ALTER TABLE presence ADD COLUMN historical_weight INT;

    UPDATE presence
    SET historical_weight = (SELECT SUM(weight)
                             FROM big_nuff_historical
                             WHERE HUC12RNG = presence.strHUC12RNG
                             GROUP BY HUC12RNG);"""
    try:
        cursor.executescript(sql)
        print('Calculated total weight of evidence for each huc : ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)


    # Find hucs that contained gbif occurrences, but were not in gaprange and
    # insert them into sp_range as new records.
    time1 = datetime.now()
    sql="""
    INSERT INTO presence (strHUC12RNG, recent_weight)
                SELECT big_nuff_recent.HUC12RNG, SUM(big_nuff_recent.weight)
                FROM big_nuff_recent LEFT JOIN presence
                                        ON presence.strHUC12RNG = big_nuff_recent.HUC12RNG
                WHERE presence.strHUC12RNG IS NULL
                GROUP BY big_nuff_recent.HUC12RNG;

    INSERT INTO presence (strHUC12RNG, historical_weight)
                SELECT big_nuff_historical.HUC12RNG, SUM(big_nuff_historical.weight)
                FROM big_nuff_historical LEFT JOIN presence
                                            ON presence.strHUC12RNG = big_nuff_historical.HUC12RNG
                WHERE presence.strHUC12RNG IS NULL
                GROUP BY big_nuff_historical.HUC12RNG;"""
    try:
        cursor.executescript(sql)
        print('Added rows for hucs with enough weight but not in GAP range : ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)

    ############################  Record which hucs have sufficient evidence
    ########################################################################
    time1 = datetime.now()
    sql="""/* Mark records/hucs that have sufficient evidence */
    UPDATE presence
    SET documented_recent = 1
    WHERE recent_weight >= 10;

    UPDATE presence
    SET documented_historical = 1
    WHERE historical_weight >= 10;
    """
    try:
        cursor.executescript(sql)
        print('Filled out documented presence columns : ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)

    ##########################################  Fill out new presence column
    ########################################################################
    time1 = datetime.now()
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
        print('Determined 2020v1 range presence value : ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)


    #####################################  Calculate years since last record
    ########################################################################
    time1 = datetime.now()
    sql="""
    /* Combine big nuff tables into one */
    CREATE TABLE all_big_nuff AS SELECT * FROM big_nuff_recent;

    INSERT INTO all_big_nuff SELECT * FROM big_nuff_historical;

    /* Calculate years since record in a new column */
    ALTER TABLE all_big_nuff ADD COLUMN years_since INT;

    UPDATE all_big_nuff
    SET years_since = strftime('%Y', 'now') - strftime('%Y', occurrenceDate);

    /* Choose first in a group by HUC12RNG */
    UPDATE presence
    SET age_of_last = (SELECT MIN(years_since)
    				  FROM all_big_nuff
    				  WHERE HUC12RNG = presence.strHUC12RNG
    				  GROUP BY HUC12RNG);

    /* Update layer statistics or else not all columns will show up in QGIS */
    SELECT UpdateLayerStatistics('presence');
    """
    try:
        cursor.executescript(sql)
        print('Determined age of last occurrence : ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)

    #####################################  Export shapefile for notebook (4326)
    ########################################################################
    time1 = datetime.now()
    sql="""
    SELECT ExportSHP('presence', 'geom_4326', '{0}{1}2020v1_4326', 'utf-8');
    """.format(outDir, gap_id)
    try:
        cursor.executescript(sql)
        print('Exported shapefile : ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)

    conn.commit()
    conn.close()

def cleanup_eval_db(eval_db):
    '''
    Drob excess tables and columns to reduce file size.
    '''
    from datetime import datetime
    time1 = datetime.now()
    cursor, conn = spatialite(eval_db)
    sql="""
    DROP TABLE all_big_nuff;
    DROP TABLE big_nuff_historical;
    DROP TABLE big_nuff_recent;
    DROP TABLE historical_records;
    DROP TABLE recent_records;
    DROP TABLE intersected_historical;
    DROP TABLE intersected_recent;
    DROP TABLE shucs;
    DROP TABLE presence_2001v1;
    DROP TABLE range_2001v1;

    /* Get rid of the geom_4326 column */
    CREATE TABLE IF NOT EXISTS new_pres AS
                SELECT strHUC12RNG, predicted_presence, documented_historical,
                       documented_recent, age_of_last, presence_2020v1,
                       geom_5070);

    DROP TABLE presence;

    ALTER TABLE new_pres RENAME TO presence;

    SELECT RecoverGeometryColumn('presence', 'geom_5070', 5070, 'MULTIPOLYGON',
                                 'XY');
    """.format(outDir, gap_id)
    try:
        cursor.executescript(sql)
        print('Deleted excess tables and columns : ' + str(datetime.now() - time1))
    except Exception as e:
        print(e)

    conn.commit()
    conn.close()



def evaluate_GAP_range(eval_id, gap_id, eval_db, parameters_db, outDir, codeDir):
    """
    Uses occurrence data collected with the wildlife-wrangler repo
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
    parameters_db -- database with information on range update and evaluation
                criteria.
    outDir -- directory of
    codeDir -- directory of code repo
    """
    import sqlite3
    import os

    cursor, conn = spatialite(parameters_db)
    method = cursor.execute("""SELECT method
                               FROM evaluations
                               WHERE evaluation_id = ?;""",
                               (eval_id,)).fetchone()[0]
    conn.close()
    del cursor

    # Range evaluation database.
    cursor, conn = spatialite(eval_db)
    cursor.executescript("""ATTACH DATABASE '{0}'
                            AS params;""".format(parameters_db))

    sql2="""
    /*#############################################################################
                                 Assess Agreement
     ############################################################################*/

    /*#########################  Which HUCs contain an occurrence?
     #############################################################*/
    /*  Intersect occurrence circles with hucs  */
    CREATE TABLE intersected_recent AS
                  SELECT shucs.HUC12RNG, ox.occ_id,
                  CastToMultiPolygon(Intersection(shucs.geom_5070,
                                                  ox.polygon_5070)) AS geom_5070
                  FROM shucs, evaluation_occurrences AS ox
                  WHERE Intersects(shucs.geom_5070, ox.polygon_5070);

    SELECT RecoverGeometryColumn('intersected_recent', 'geom_5070', 5070, 'MULTIPOLYGON',
                                 'XY');

    /* In light of the error tolerance for the species, which occurrences can
       be attributed to a huc?  */
    CREATE TABLE big_nuff_recent AS
      SELECT intersected_recent.HUC12RNG, intersected_recent.occ_id,
             100 * (Area(intersected_recent.geom_5070) / Area(ox.polygon_5070))
                AS proportion_circle
      FROM intersected_recent
           LEFT JOIN evaluation_occurrences AS ox
           ON intersected_recent.occ_id = ox.occ_id
      WHERE proportion_circle BETWEEN (100 - (SELECT error_tolerance
                                              FROM params.evaluations
                                              WHERE evaluation_id = '{0}'
                                              AND species_id = '{1}'))
                              AND 100;

    /*  How many occurrences in each huc that had an occurrence? */
    ALTER TABLE sp_range ADD COLUMN weight_sum INT;

    UPDATE sp_range
    SET weight_sum = (SELECT SUM(weight)
                          FROM big_nuff_recent
                          WHERE HUC12RNG = sp_range.strHUC12RNG
                          GROUP BY HUC12RNG);


    /*  Find hucs that contained gbif occurrences, but were not in gaprange and
    insert them into sp_range as new records.  Record the occurrence count */
    INSERT INTO sp_range (strHUC12RNG, weight_sum)
                SELECT big_nuff_recent.HUC12RNG, SUM(weight)
                FROM big_nuff_recent LEFT JOIN sp_range ON sp_range.strHUC12RNG = big_nuff_recent.HUC12RNG
                WHERE sp_range.strHUC12RNG IS NULL
                GROUP BY big_nuff_recent.HUC12RNG;


    /*############################  Does HUC contain enough weight?
    #############################################################*/
    ALTER TABLE sp_range ADD COLUMN eval INT;

    /*  Record in sp_range that gap and gbif agreed on species presence, in light
    of the minimum weight of 10 */
    UPDATE sp_range
    SET eval = 1
    WHERE weight_sum >= 10;


    /*  For new records, put zeros in GAP range attribute fields  */
    UPDATE sp_range
    SET intGAPOrigin = 0,
        intGAPPresence = 0,
        intGAPReproduction = 0,
        intGAPSeason = 0,
        eval = 0
    WHERE weight_sum >= 0 AND intGAPOrigin IS NULL;


    /*###########################################  Validation column
    #############################################################*/
    /*  Populate a validation column.  If an evaluation supports the GAP ranges
    then it is validated */
    ALTER TABLE sp_range ADD COLUMN validated_presence INT NOT NULL DEFAULT 0;

    UPDATE sp_range
    SET validated_presence = 1
    WHERE eval = 1;


    /*#############################################################################
                                   Export Maps
     ############################################################################*/
    /*  Create a version of sp_range with geometry  */
    CREATE TABLE new_range AS
                  SELECT sp_range.*, shucs.geom_5070
                  FROM sp_range LEFT JOIN shucs ON sp_range.strHUC12RNG = shucs.HUC12RNG;

    ALTER TABLE new_range ADD COLUMN geom_4326 INTEGER;

    SELECT RecoverGeometryColumn('new_range', 'geom_5070', 5070, 'MULTIPOLYGON', 'XY');

    UPDATE new_range SET geom_4326 = Transform(geom_5070, 4326);

    SELECT RecoverGeometryColumn('new_range', 'geom_4326', 4326, 'POLYGON', 'XY');

    SELECT ExportSHP('new_range', 'geom_4326', '{2}{1}_CONUS_Range_2020v1',
                     'utf-8');

    /* Make a shapefile of evaluation results */
    CREATE TABLE eval AS
                  SELECT strHUC12RNG, eval, geom_4326
                  FROM new_range
                  WHERE eval >= 0;

    SELECT RecoverGeometryColumn('eval', 'geom_4326', 4326, 'MULTIPOLYGON', 'XY');

    SELECT ExportSHP('eval', 'geom_4326', '{2}{1}_eval', 'utf-8');


    /*#############################################################################
                                 Clean Up
    #############################################################################*/
    /*  */
    DROP TABLE intersected_recent;
    DROP TABLE big_nuff_recent;
    """.format(eval_id, gap_id, outDir)

    try:
        cursor.executescript(sql2)
    except Exception as e:
        print(e)

    conn.commit()
    conn.close()
