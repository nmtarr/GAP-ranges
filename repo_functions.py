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

def make_evaluation_db(gap_id, outDir, shucLoc, inDir):
    """
    Builds an sqlite database in which to store range evaluation information.  
    shucloc needs to be eventually be replaced wtih ScienceBase download of shucs.
    
    Arguments:
    gap_id -- gap species code. For example, 'bAMROx'
    outDir -- project's output directory
    shucLoc -- path to GAP's 12 digit hucs shapefile
    inDir -- project's input directory    
    """
    import sqlite3
    import pandas as pd
    import os

    # Delete db if it exists
    eval_db = outDir + gap_id + '_range.sqlite' # Name of range evaluation database.
    if os.path.exists(eval_db):
        os.remove(eval_db)

    # Create or connect to the database
    conn = sqlite3.connect(eval_db)
    os.putenv('SPATIALITE_SECURITY', 'relaxed')
    conn.enable_load_extension(True)
    conn.execute('SELECT load_extension("mod_spatialite")')

    sql="""
    SELECT InitSpatialMetadata(1);

    /* Add Albers_Conic_Equal_Area 102008 to the spatial sys ref tables */
    SELECT InitSpatialMetaData();
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
                 UNIT["Meter",1],AUTHORITY["EPSG","102008"]]');


    /* Add the hucs shapefile to the db. */
    SELECT ImportSHP('{0}', 'shucs', 'utf-8', 102008,
                     'geom_102008', 'HUC12RNG', 'POLYGON');
    """.format(shucLoc)
    conn.executescript(sql)

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