/*
 * MATLAB Compiler: 4.11 (R2009b)
 * Date: Tue May 07 06:40:18 2013
 * Arguments: "-B" "macro_default" "-e" "-W" "WinMain" "-T" "link:exe" "-R"
 * "-logfile" "-o" "FootProcessor" "-R" "footprocessor.log" "-v"
 * "footprocessor.m" "-M" "icon.res" "-a" "logo_fp.png" "-N" "-p" "stats\" 
 */

#include "mclmcrrt.h"

#ifdef __cplusplus
extern "C" {
#endif
const unsigned char __MCC_FootProcessor_session_key[] = {
    '8', 'D', '2', 'B', '3', '4', '7', '3', 'D', '0', '5', '5', '7', 'F', '4',
    '1', '5', '0', '0', 'A', '5', 'C', '2', 'E', 'B', '3', 'D', '3', 'E', '6',
    '0', 'D', '1', 'D', '8', '3', 'E', '8', 'A', 'A', 'B', '2', '1', 'E', 'F',
    'F', '8', '7', '9', '0', '0', 'F', '1', 'E', '4', '7', '8', 'E', '0', '9',
    '7', '5', 'B', '8', 'A', 'E', 'A', 'E', '0', 'C', 'D', '4', '8', '2', '6',
    '2', '5', '8', 'B', '7', 'C', 'E', '6', 'F', 'F', '9', '1', '1', 'A', 'D',
    'F', 'E', '6', '5', 'A', 'B', '6', 'E', 'D', 'C', 'E', '1', 'F', 'B', '9',
    '2', '9', '3', 'D', '0', '8', '5', '4', '1', '9', '3', '4', '7', 'C', '3',
    '9', '3', '4', 'C', 'F', '4', '7', '0', 'C', 'E', 'E', '6', '7', '3', '6',
    '1', '2', '2', 'D', '8', 'A', '6', '7', 'B', 'F', '8', '4', '6', 'D', '8',
    'F', '9', '6', 'B', '9', '5', '4', '8', '5', '2', 'A', 'D', '2', 'B', '5',
    '4', '7', '5', 'B', '6', '5', '2', 'D', '0', '0', '0', '5', 'C', 'E', '1',
    'D', '1', 'C', '4', '6', 'E', '5', 'F', '4', '6', 'A', 'B', 'E', 'D', '8',
    'A', '1', 'D', '3', '4', 'D', 'C', 'D', 'F', '9', 'B', '5', '1', '4', 'F',
    '0', '7', '9', '4', 'F', '6', '5', 'F', 'D', '9', 'E', 'F', 'D', '8', 'F',
    'A', 'B', '4', '9', 'B', '6', '9', 'C', '8', 'C', '3', 'C', '8', 'B', 'E',
    '5', 'C', '4', 'E', '6', '7', '1', 'D', '5', '1', '7', 'C', '5', '5', '5',
    '5', '\0'};

const unsigned char __MCC_FootProcessor_public_key[] = {
    '3', '0', '8', '1', '9', 'D', '3', '0', '0', 'D', '0', '6', '0', '9', '2',
    'A', '8', '6', '4', '8', '8', '6', 'F', '7', '0', 'D', '0', '1', '0', '1',
    '0', '1', '0', '5', '0', '0', '0', '3', '8', '1', '8', 'B', '0', '0', '3',
    '0', '8', '1', '8', '7', '0', '2', '8', '1', '8', '1', '0', '0', 'C', '4',
    '9', 'C', 'A', 'C', '3', '4', 'E', 'D', '1', '3', 'A', '5', '2', '0', '6',
    '5', '8', 'F', '6', 'F', '8', 'E', '0', '1', '3', '8', 'C', '4', '3', '1',
    '5', 'B', '4', '3', '1', '5', '2', '7', '7', 'E', 'D', '3', 'F', '7', 'D',
    'A', 'E', '5', '3', '0', '9', '9', 'D', 'B', '0', '8', 'E', 'E', '5', '8',
    '9', 'F', '8', '0', '4', 'D', '4', 'B', '9', '8', '1', '3', '2', '6', 'A',
    '5', '2', 'C', 'C', 'E', '4', '3', '8', '2', 'E', '9', 'F', '2', 'B', '4',
    'D', '0', '8', '5', 'E', 'B', '9', '5', '0', 'C', '7', 'A', 'B', '1', '2',
    'E', 'D', 'E', '2', 'D', '4', '1', '2', '9', '7', '8', '2', '0', 'E', '6',
    '3', '7', '7', 'A', '5', 'F', 'E', 'B', '5', '6', '8', '9', 'D', '4', 'E',
    '6', '0', '3', '2', 'F', '6', '0', 'C', '4', '3', '0', '7', '4', 'A', '0',
    '4', 'C', '2', '6', 'A', 'B', '7', '2', 'F', '5', '4', 'B', '5', '1', 'B',
    'B', '4', '6', '0', '5', '7', '8', '7', '8', '5', 'B', '1', '9', '9', '0',
    '1', '4', '3', '1', '4', 'A', '6', '5', 'F', '0', '9', '0', 'B', '6', '1',
    'F', 'C', '2', '0', '1', '6', '9', '4', '5', '3', 'B', '5', '8', 'F', 'C',
    '8', 'B', 'A', '4', '3', 'E', '6', '7', '7', '6', 'E', 'B', '7', 'E', 'C',
    'D', '3', '1', '7', '8', 'B', '5', '6', 'A', 'B', '0', 'F', 'A', '0', '6',
    'D', 'D', '6', '4', '9', '6', '7', 'C', 'B', '1', '4', '9', 'E', '5', '0',
    '2', '0', '1', '1', '1', '\0'};

static const char * MCC_FootProcessor_matlabpath_data[] = 
  { "FootProcesso/", "$TOOLBOXDEPLOYDIR/", "$TOOLBOXMATLABDIR/general/",
    "$TOOLBOXMATLABDIR/ops/", "$TOOLBOXMATLABDIR/lang/",
    "$TOOLBOXMATLABDIR/elmat/", "$TOOLBOXMATLABDIR/randfun/",
    "$TOOLBOXMATLABDIR/elfun/", "$TOOLBOXMATLABDIR/specfun/",
    "$TOOLBOXMATLABDIR/matfun/", "$TOOLBOXMATLABDIR/datafun/",
    "$TOOLBOXMATLABDIR/polyfun/", "$TOOLBOXMATLABDIR/funfun/",
    "$TOOLBOXMATLABDIR/sparfun/", "$TOOLBOXMATLABDIR/scribe/",
    "$TOOLBOXMATLABDIR/graph2d/", "$TOOLBOXMATLABDIR/graph3d/",
    "$TOOLBOXMATLABDIR/specgraph/", "$TOOLBOXMATLABDIR/graphics/",
    "$TOOLBOXMATLABDIR/uitools/", "$TOOLBOXMATLABDIR/strfun/",
    "$TOOLBOXMATLABDIR/imagesci/", "$TOOLBOXMATLABDIR/iofun/",
    "$TOOLBOXMATLABDIR/audiovideo/", "$TOOLBOXMATLABDIR/timefun/",
    "$TOOLBOXMATLABDIR/datatypes/", "$TOOLBOXMATLABDIR/verctrl/",
    "$TOOLBOXMATLABDIR/codetools/", "$TOOLBOXMATLABDIR/helptools/",
    "$TOOLBOXMATLABDIR/winfun/", "$TOOLBOXMATLABDIR/winfun/NET/",
    "$TOOLBOXMATLABDIR/demos/", "$TOOLBOXMATLABDIR/timeseries/",
    "$TOOLBOXMATLABDIR/hds/", "$TOOLBOXMATLABDIR/guide/",
    "$TOOLBOXMATLABDIR/plottools/", "toolbox/local/",
    "$TOOLBOXMATLABDIR/datamanager/", "toolbox/compiler/", "toolbox/stats/" };

static const char * MCC_FootProcessor_classpath_data[] = 
  { "" };

static const char * MCC_FootProcessor_libpath_data[] = 
  { "" };

static const char * MCC_FootProcessor_app_opts_data[] = 
  { "" };

static const char * MCC_FootProcessor_run_opts_data[] = 
  { "-logfile", "footprocessor.log" };

static const char * MCC_FootProcessor_warning_state_data[] = 
  { "off:MATLAB:dispatcher:nameConflict" };


mclComponentData __MCC_FootProcessor_component_data = { 

  /* Public key data */
  __MCC_FootProcessor_public_key,

  /* Component name */
  "FootProcessor",

  /* Component Root */
  "",

  /* Application key data */
  __MCC_FootProcessor_session_key,

  /* Component's MATLAB Path */
  MCC_FootProcessor_matlabpath_data,

  /* Number of directories in the MATLAB Path */
  40,

  /* Component's Java class path */
  MCC_FootProcessor_classpath_data,
  /* Number of directories in the Java class path */
  0,

  /* Component's load library path (for extra shared libraries) */
  MCC_FootProcessor_libpath_data,
  /* Number of directories in the load library path */
  0,

  /* MCR instance-specific runtime options */
  MCC_FootProcessor_app_opts_data,
  /* Number of MCR instance-specific runtime options */
  0,

  /* MCR global runtime options */
  MCC_FootProcessor_run_opts_data,
  /* Number of MCR global runtime options */
  2,
  
  /* Component preferences directory */
  "FootProcesso_869C233C23A716762691BE27990F1EBE",

  /* MCR warning status data */
  MCC_FootProcessor_warning_state_data,
  /* Number of MCR warning status modifiers */
  1,

  /* Path to component - evaluated at runtime */
  NULL

};

#ifdef __cplusplus
}
#endif


