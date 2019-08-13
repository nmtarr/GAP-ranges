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
gap_id -- 
summary_name -- 
gbif_req_id --
gbif_filter_id --
outDir -- 
shucLoc -- 
codeDir -- 
"""
import sqlite3
import config
import os

# Create or connect to the range_evaluation database and eval parameters db
conn2 = sqlite3.connect(codeDir + "evaluations.sqlite")
cursor2 = conn2.cursor()

# Range evaluation database.
eval_db = outDir + gap_id + '_range.sqlite'
conn = sqlite3.connect(eval_db)
os.putenv('SPATIALITE_SECURITY', 'relaxed')
conn.enable_load_extension(True)
conn.execute('SELECT load_extension("mod_spatialite")')
cursor = conn.cursor()

# Get evaluation months and years
months = cursor2.execute("SELECT months "
                        "FROM evaluations "
                        "WHERE evaluation_id = '{0}'".format(config.evaluation)).fetchone()[0]
years = cursor2.execute("SELECT years "
                        "FROM evaluations "
                        "WHERE evaluation_id = '{0}'".format(config.evaluation)).fetchone()[0]

sql="""
ATTACH DATABASE '/users/nmtarr/documents/Occurrences/outputs/bwewax0GBIFr14GBIFf4.sqlite'
                AS occs;

ATTACH DATABASE '/users/nmtarr/code/GAP-range-evaluation/evaluations.sqlite'
                AS params;

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
              FROM shucs, occs.occurrences AS ox
              WHERE Intersects(shucs.geom_102008, ox.circle_albers)
                AND Cast(strftime('%m', ox.occurrenceDate) AS INTEGER) IN ({1})
                AND Cast(strftime('%Y', ox.occurrenceDate) AS INTEGER) IN ({2});

SELECT RecoverGeometryColumn('green', 'geom_102008', 102008, 'MULTIPOLYGON',
                             'XY');

/* In light of the error tolerance for the species, which occurrences can
   be attributed to a huc?  */
CREATE TABLE orange AS
  SELECT green.HUC12RNG, green.occ_id,
         100 * (Area(green.geom_102008) / Area(ox.circle_albers))
            AS proportion_circle
  FROM green
       LEFT JOIN occs.occurrences AS ox
       ON green.occ_id = ox.occ_id
  WHERE proportion_circle BETWEEN (100 - (SELECT error_tolerance
                                          FROM params.evaluations
                                          WHERE evaluation_id= 'eval'))
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
                        WHERE evaluation_id = 'eval');


/*  For new records, put zeros in GAP range attribute fields  */
UPDATE sp_range
SET intGAPOrigin = 0,
    intGAPPresence = 0,
    intGAPReproduction = 0,
    intGAPSeason = 0,
    eval = 0
WHERE eval_cnt >= 0 AND intGAPOrigin IS NULL;


/*###########################################  Validaton column
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

SELECT ExportSHP('new_range', 'geom_4326', '{3}{4}_CONUS_Range_2001v1_eval',
                 'utf-8');

/* Make a shapefile of evaluation results */
CREATE TABLE eval AS
              SELECT strHUC12RNG, eval, geom_4326
              FROM new_range
              WHERE eval >= 0;

SELECT RecoverGeometryColumn('eval', 'geom_4326', 4326, 'POLYGON', 'XY');

SELECT ExportSHP('eval', 'geom_4326', '{3}{4}_eval', 'utf-8');


/*#############################################################################
                             Clean Up
#############################################################################*/
/* sp_range is no longer needed, use new_range instead */
DROP TABLE sp_range;
DROP TABLE green;
DROP TABLE orange;
""".format(sp_id, months, years, outDir, gap_id)
try:
    cursor.executescript(sql)
except Exception as e:
    print(e)

conn.close()
conn2.close()
del cursor
del cursor2
