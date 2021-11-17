# radolan2map

**QGIS plugin for DWD rasterized precipitation datasets like RADOLAN/RADKLIM and REGNIE**  
This project is a QGIS plugin that brings precipitation data from German Meteorological Service (DWD, https://www.dwd.de) - radar data in RADOLAN/RADKLIM binary format in any grid dimension as well as REGNIE - on a map. You also can **add** up RADOLAN data!  
Applications: hydrometeorological and agricultural analyses.

### Features
load the following data types:
- load/display any binary file in RADOLAN / RADKLIM format (incl. gz-compression)
- radolan summation: you can add up RADOLAN data!
- rudimentary REGNIE support

additional functions for RADOLAN:
- bring it to standard projection [ETRS89 / LAEA Europe](https://epsg.io/3035)
- optional cut to german border (or any other shape file)
- status of DWD Radar Network included (see [Wiki](https://gitlab.com/Weatherman_/radolan2map/wikis/home))
  

### Installation, Usage
=> [Wiki](https://gitlab.com/Weatherman_/radolan2map/wikis/home)
  

### Data info
* RADOLAN overview: [https://dwd.de/RADOLAN](https://dwd.de/RADOLAN)
* data download: RADOLAN (recent) and RADKLIM radar climatology dataset:
  [DWD open climate data](https://opendata.dwd.de/climate_environment/CDC/grids_germany/hourly/radolan/)

There are hourly (RH, RW) or daily (SF) datasets.  
A RADOLAN-RW-testfile (gzipped binary) is included in directory `example/sample_file/`.
  

### Platform info
Plugin was successfully tested with QGIS
*  3.10 *A Coruña* on Linux openSUSE 15.1 and Windows 10
*  3.16 *Hannover* on Linux openSUSE 15.1

If you experience any problems when starting the plugin, please make sure that  
you have a **current version of QGIS and Python installed** on your system.


### QGIS
*  [https://qgis.org](https://qgis.org)
*  [`radolan2map`](http://plugins.qgis.org/plugins/radolan2map/) at qgis.org

### Feel invited...
to give me feedback about usability and  
help improving this plugin to promote open source (GIS)software and data!

