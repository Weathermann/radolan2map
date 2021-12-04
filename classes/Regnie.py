#!/usr/bin/python3
"""
Class for reading REGNIE files

Can handle daily, monthly and multiannual REGNIE files

REGNIE description: https://www.dwd.de/DE/leistungen/regnie/regnie.html

REGNIE files are freely available from the DWD open data platform:
https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/regnie/
https://opendata.dwd.de/climate_environment/CDC/grids_germany/monthly/regnie/
https://opendata.dwd.de/climate_environment/CDC/grids_germany/multi_annual/regnie/

@author: Felix Froehlich

partially based on Regnie2CSV.py by Mario Hafer, Deutscher Wetterdienst (DWD)
"""
import os
import re
import gzip

import numpy as np

# REGNIE extent:
Y_MAX = 971
X_MAX = 611

class Regnie:

    def __init__(self, file_regnie: str):
        """
        Instantiates a new Regnie class instance representing a REGNIE file.
        The file is read immediately.

        :param file_regnie: path to the REGNIE file (can be gz compressed)
        """
        if not os.path.exists(file_regnie):
            raise FileNotFoundError(f"File not found: {file_regnie}")
            
        self._filepath = file_regnie
        self._datatype = self._get_datatype()
        self._data = None

        self._read_file()

    def _read_file(self):
        """
        Reads the REGNIE file and stores the values in the `data` property
        """
        if self._filepath.endswith(".gz"):
            file = gzip.open(self._filepath, "rt")
        else:
            file = open(self._filepath, "r")

        rows = []
        for i, line in enumerate(file, start=1):
            if i > Y_MAX:
                # in daily datasets, the last line contains other stuff we don't need
                break
            line = line.strip()
            # split line into strings of 4 characters each
            strings = []
            for j in range(len(line) // 4):
                strings.append(line[j*4:(j*4)+4])
                
            # convert strings to values depending on datatype
            if self.datatype in ["monthly", "multiannual"]:
                values = [int(s) for s in strings]
            elif self.datatype == "daily":
                values = [float(s) if s != "-999" else np.nan for s in strings]
                values = [v / 10.0 for v in values]
                
            rows.append(values)

        file.close()

        self._data = np.array(rows)

    def _get_datatype(self) -> str:
        """
        Determines the data type of a REGNIE file from its filename
        
        Examples:
         ra210627 - daily values
         RASA2110 - monthly values
         RAS9120.JAH - multiannual values
        
        :param file_regnie: REGNIE file
        :return: "daily", "monthly" or "multiannual"
        """
        filename = os.path.basename(self._filepath)
        if re.fullmatch(r"ra\d{6}(\.gz)?", filename, re.I):
            return "daily"
        elif re.fullmatch(r"RASA\d{4}(\.gz)?", filename, re.I):
            return "monthly"
        elif re.fullmatch(r"RAS\d{4}\.[a-z]+(\.gz)?", filename, re.I):
            return "multiannual"
        else:
            raise Exception(f"Unable to determine REGNIE data type from filename {filename}!")

    def _pixel_to_latlon(self, x: int, y: int) -> tuple:
        """ 
        Converts a REGNIE x,y pixel coordinate to a lat,lon coordinate

        :param x: x coordinate
        :param y: y coordinate
        :return: (lat, lon)
        """
        x_delta = 1.0 /  60.0
        y_delta = 1.0 / 120.0
        
        x_min =  6.0 - 10.0 * x_delta
        y_max = 55.0 + 10.0 * y_delta

        lon = x_min + (x - 1) * x_delta
        lat = y_max - (y - 1) * y_delta
        
        return lat, lon
    
    @property
    def data(self) -> np.array:
        """
        Returns the values contained in the REGNIE file as a numpy array

        The data type of the array is integer for monthly and multiannual values and float for daily values
        REGNIE error values ("-999") are preserved as -999 for monthly and multiannual values and replaced with np.nan for daily values
        Daily REGNIE values are converted from 1/10 mm to mm
        
        :return: a two-dimensional numpy array
        """
        return self._data
            
    @property
    def datatype(self) -> str:
        """
        Returns the data type of the REGNIE file
        
        :return: either "monthly" or "daily"
        """
        return self._datatype

    @property
    def statistics(self) -> dict:
        """
        Returns statistics from the REGNIE data

        :return: dictionary of statistical values
        """
        # extract only valid cells
        if self.datatype == "daily":
            valid_data = np.extract(~np.isnan(self.data), self.data)
        elif self.datatype in ["monthly", "multiannual"]:
            valid_data = np.extract(self.data != -999, self.data)

        stats = {
            "total_pixels": self.data.size,
            "valid_pixels": valid_data.size,
            "non_valid_pixels": self.data.size - valid_data.size,
            "max": np.max(valid_data),
            "min": np.min(valid_data),
            "mean": np.mean(valid_data)
        }

        return stats
