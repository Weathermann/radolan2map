#!/usr/bin/python3
"""
Converts a REGNIE file to a raster file (geotiff)

This script can handle both daily and monthly REGNIE files

Monthly REGNIE files contain values in the unit mm and are converted to Int32 rasters with a NoData value of -999
Daily REGNIE files contain values in the unit 1/10 mm, which are first converted to mm and then converted to Float64 rasters with a default NoData value

REGNIE description: https://www.dwd.de/DE/leistungen/regnie/regnie.html

REGNIE files are freely available from the DWD open data platform:
https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/regnie/
https://opendata.dwd.de/climate_environment/CDC/grids_germany/monthly/regnie/

@author: Felix Froehlich
"""
import os, sys
import argparse
import re

import numpy as np
from osgeo import gdal
from osgeo import osr

def regnie2raster(file_regnie: str, file_raster: str) -> None:
    """
    Converts a REGNIE file to a raster file (geotiff)

    :param file_regnie: input REGNIE file
    :param file_regnie: output REGNIE file
    """
    # get array values from regnie file
    array = regnie2array(file_regnie)
    
    # define pixel size and origin
    # from https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/regnie/REGNIE_Beschreibung_20201109.pdf
    # (also applies to monthly regnie files)
    x_delta = 1.0 / 60.0
    y_delta = 1.0 / 120.0
    x_min = 6.0 - (10.0 * x_delta)
    y_max = (55.0 + 10.0 * y_delta)
    origin = (x_min - x_delta / 2, y_max + y_delta / 2) # include half cell offset

    # save as raster
    array2raster(file_raster, origin, x_delta, y_delta, array)
    
def regnie2array(file_regnie: str) -> np.array:
    """
    Reads a REGNIE file as a numpy array
    
    The data type of the returned array is integer for monthly values and float for daily values
    REGNIE error values ("-999") are preserved as -999 for monthly values and replaced with np.nan for daily values
    Daily REGNIE values are converted from 1/10 mm to mm
    
    :param file_regnie: path to the REGNIE file
    
    :return: a two-dimensional numpy array
    """
    # determine REGNIE datatype
    datatype = regnie_datatype(file_regnie)

    with open(file_regnie, "r") as f:
        rows = []
        for i, line in enumerate(f, start=1):
            if i > 971:
                # in daily datasets, the last line contains other stuff we don't need
                break
            line = line.strip()
            # split line into strings of 4 characters each
            strings = []
            for j in range(len(line) // 4):
                strings.append(line[j*4:(j*4)+4])
                
            # convert strings to values depending on datatype
            if datatype == "monthly":
                values = [int(s) for s in strings]
            elif datatype == "daily":
                values = [float(s) if s != "-999" else np.nan for s in strings]
                values = [v / 10.0 for v in values]
            else:
                raise NotImplementedError(f"REGNIE datatype {datatype} is not yet implemented!")
                
            rows.append(values)

    array = np.array(rows)
    
    return array
    
def regnie_datatype(file_regnie: str) -> str:
    """
    Determines the data type of a REGNIE file from its filename
    
    Examples:
     RASA2110 - monthly values
     ra210627 - daily values
    
    :param file_regnie: REGNIE file
    :return: either "monthly" or "daily"
    """
    filename = os.path.basename(file_regnie)
    if re.fullmatch(r"RASA\d{4}", filename, re.I):
        return "monthly"
    elif re.fullmatch(r"ra\d{6}", filename, re.I):
        return "daily"
    else:
        raise Exception(f"Unable to determine REGNIE data type from filename {filename}!")

def array2raster(outfile: str, rasterOrigin: tuple, pixelWidth: int, pixelHeight: int, array: np.array) -> None:
    """
    writes a numpy array to a raster file (geotiff)
    adapted from https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html#create-raster-from-array
    
    :param outfile: output raster file
    :param rasterOrigin: tuple (x, y) of the top left coordinates of the raster
    :param pixelWidth: pixel width
    :param pixelHeight: pixel height
    :param array: two-dimensional numpy array with cell values
    """

    cols = array.shape[1]
    rows = array.shape[0]
    originX = rasterOrigin[0]
    originY = rasterOrigin[1]

    # set pixel data type depending on array dtype
    # available pixel data types: https://naturalatlas.github.io/node-gdal/classes/Constants%20(GDT).html
    # TODO: add more types
    if array.dtype == np.dtype(np.int32):
        typ = gdal.GDT_Int32
    else:
        typ = gdal.GDT_Float64

    driver = gdal.GetDriverByName('GTiff')

    outRaster = driver.Create(outfile, cols, rows, 1, typ)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, -pixelHeight))

    outband = outRaster.GetRasterBand(1)
    if array.dtype == np.dtype(np.int32):
        # set noData value for integer rasters, for float rasters the input array is expected to have NaN values for NoData
        outband.SetNoDataValue(-999)
    outband.WriteArray(array)

    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())

    outband.FlushCache()

if __name__ == "__main__":

    # commandline interface

    try:
        parser = argparse.ArgumentParser(
            description="""
Converts a REGNIE file to a raster file (geotiff)

This script can handle both daily and monthly REGNIE files

Monthly REGNIE files contain values in the unit mm and are converted to Int32 rasters with a NoData value of -999
Daily REGNIE files contain values in the unit 1/10 mm, which are first converted to mm and then converted to Float64 rasters with a default NoData value

REGNIE description: https://www.dwd.de/DE/leistungen/regnie/regnie.html

REGNIE files are freely available from the DWD open data platform:
https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/regnie/
https://opendata.dwd.de/climate_environment/CDC/grids_germany/monthly/regnie/
"""
        )
        
        parser.add_argument("regnie_file", type=str, help="input REGNIE file")
        parser.add_argument("output_file", type=str, help="output raster file (tif)")
        
        args = parser.parse_args()
        
        regnie2raster(args.regnie_file, args.output_file)
        
        print("Conversion successful!")

    except Exception as e:
        
        print(f"ERROR: {e}")
        
