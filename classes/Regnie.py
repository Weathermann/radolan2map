#!/usr/bin/python3
"""
Class for reading REGNIE files

Can handle both daily and monthly REGNIE files

REGNIE description: https://www.dwd.de/DE/leistungen/regnie/regnie.html

REGNIE files are freely available from the DWD open data platform:
https://opendata.dwd.de/climate_environment/CDC/grids_germany/daily/regnie/
https://opendata.dwd.de/climate_environment/CDC/grids_germany/monthly/regnie/

@author: Felix Froehlich
"""
import os, sys
import re

import numpy as np

class Regnie:

    def __init__(self, file_regnie: str):
        """
        Instantiates a new Regnie class instance representing a REGNIE file
        """
        if not os.path.exists(file_regnie):
            raise FileNotFoundError(f"File not found: {file_regnie}")
            
        self._file = file_regnie
        self._datatype = self._get_datatype()
    
    def _get_datatype(self) -> str:
        """
        Determines the data type of a REGNIE file from its filename
        
        Examples:
         RASA2110 - monthly values
         ra210627 - daily values
        
        :param file_regnie: REGNIE file
        :return: either "monthly" or "daily"
        """
        filename = os.path.basename(self._file)
        if re.fullmatch(r"RASA\d{4}", filename, re.I):
            return "monthly"
        elif re.fullmatch(r"ra\d{6}", filename, re.I):
            return "daily"
        else:
            raise Exception(f"Unable to determine REGNIE data type from filename {filename}!")
            
    @property
    def datatype(self):
        """
        Returns the data type of the REGNIE file
        
        :return: either "monthly" or "daily"
        """
        return self._datatype

    def to_array(self) -> np.array:
        """
        Returns the values contained in the REGNIE file as a numpy array
        
        The data type of the returned array is integer for monthly values and float for daily values
        REGNIE error values ("-999") are preserved as -999 for monthly values and replaced with np.nan for daily values
        Daily REGNIE values are converted from 1/10 mm to mm
        
        :return: a two-dimensional numpy array
        """
        with open(self._file, "r") as f:
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
                if self._datatype == "monthly":
                    values = [int(s) for s in strings]
                elif self._datatype == "daily":
                    values = [float(s) if s != "-999" else np.nan for s in strings]
                    values = [v / 10.0 for v in values]
                else:
                    raise NotImplementedError(f"REGNIE datatype {datatype} is not yet implemented!")
                    
                rows.append(values)

        array = np.array(rows)
        
        return array
