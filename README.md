# USGS Gap Analysis Project Range Map Compiler and Evaluation
Compiles data for GAP range maps.  Also contains code to determine where range maps agree with occurrence records from GBIF?

## Purpose
The Gap Analysis Project developed range maps for 1,590 terrestrial vertebrate species by attributing a 12 digit hydrologic unit code (HUC) vector data layer with each species' status regarding known presence, seasonal presence, use for reproduction, and origin (i.e., is it native?).  

The abundance of wildlife occurrence datasets that are currently accessible represent an opportunity to validate some aspects of the GAP range data and incorporate occurrence records into range maps.  However, this task is more complex than it may seem at first consideration given errors and uncertainties in occurrence data and the lack of absence records.  This repository is a draft framework for partially validating GAP range maps with occurrence data that is widely available through API's.

## Framework
The wildlife-wrangler code creates databases of species occurrence records that passed through user-defined and documented criteria.  Code in this repository connects to such databases and uses the records to evaluate GAP's 12 digit HUC-based range maps or compile an updated range map.  Details of unique sets of filtering criteria are stored in the wildlie-wrangler.sqlite database in wildlife-wrangler and details of range evaluation and compilation parameters are stored within this repo in evaluations.sqlite.  However, both repos (wildlife-wrangler and GAP-ranges) merely include templates for those databases.  Users must download and populate their own copies.

## Objectives and Criteria
This framework is designed to meet several important criteria in order to provide summaries that can be interpreted at face value with high confidence (i.e. with minimized human effort).

* Open source -- processes are coded in Python 3 and SQL and use sqlite3, which comes with Python 3, for spatial queries.

* Automation -- the volume of data and species involved necessitates the processes be automated. Automation also reduces subjectivity in decision making, enables thorough documentation, and ensures repeatability.

* High confidence -- data and filters should be used (in the wildlife-wrangler) that enable high confidence in results.

* Detailed parameterization -- range evaluations and compilations can be parameterized on a per-species and per-event basis. Rules do not have to be applied generally across large numbers of species or evaluations.

* Transparency through documentation -- decisions about how to conduct evaluations and compilations are documented in the evalautions.sqlite database.  The inputs for the evaluations are sqlite databases of occurrence records from the wildlife-wrangler code.

* Misidentifications and low-quality records -- even professionals are not perfect; so citizen scientists surely mistakenly identify species.  Presence-only data do not directly record absence, so false-positives are the issue here.  They can expand and distort range delineations and falsely validate GAP range maps.  A simple way to account for them is to apply weights to the individual occurrence records and set a minimum for the summed weight for a target region (i.e., a HUC) before the species is determined to be present there.  See the notebook "Method for attributing species to subregions."

* Acknowledgement of locational uncertainty -- although records are recorded as x,y coordinates, imperfect coordinate precisions, movements by observers, and detection distances greater than 0 require that records be treated as circles with centers at the x,y coordinate and radius equal to the detection distance plus the coordinate uncertainty.  Buffering points accounts for this but creates an issue regarding the overlap of occurrence circles with HUC boundaries; when a circle is not completely contained by a HUC, which HUC should it be attributed to?  There may be different methods for handling this but one answer is that the analyst has to decide and that decision is a matter of probability.  There is a 100% chance that the species occurred somewhere within the buffer point circle, so the probability that it was in a particular HUC equals the proportion of the circle that falls in that HUC (in the absense of additionaly information).  Therefore, setting an a priori tolerance for error is required.  If you set your tolerance to 10%, then the occurrence record will only be attributed to a HUC if over 90% of the circle occurs within it.  

## Inputs
Occurrence data is pulled from occurrence record databases that were created with the wildlife-wrangler.  Range evaluation and compilation criteria are stored in "evaulations.sqlite".  Additionally, the GAP 12 digit HUC ancillary layer is needed, and although it is available on ScienceBase.gov as a geodatabase, a different format is needed.  Hopefully a shapefile version can be uploaded there eventually.

GBIF is currently the only dataset currently used but others can/will be added later including eBird.

## Outputs
On a per-species basis
* A database including a table with presence information for HUCs for which some information was available.  Columns include 2001 presence, 2020 presence, and years since a record.
* A database of GAP range evaluation information from which a range evaluation shapefile can be created.
* A csv file of updated range data with columns for evaluation and validation information as well as rows for HUCs with occurrences that were omitted by GAP.

## Constraints
None at this time

## Dependencies
Python 3 and numerous packages including sqlite3 with the spatialite extension.  An environment can be created from the ENVIRONMENT.yml file included in this repository.  This code relies upon the wildlife-wrangler code (github.com/nmtarr/wildlife-wrangler).  

## Code
All code is included in this repository.  Runtimes of discrete tasks made grouping code into separate scripts preferable.  A demonstration and explanation of the scripts' general features are included in the TEMPLATE.ipynb.

## Recent Changes (May 7, 2020)
* Addition of a range compilation function and examples of skunks for IALE-NA 2020 annual meeting.  That is archived in the IALE2020 branch.

## Coming Soon
* Assessment of ranges for years 2005, 2010, and 2015 in addition to 2001 and 2020.
* Further capabilities to document.
