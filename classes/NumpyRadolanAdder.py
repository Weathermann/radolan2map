'''
Created on 27.11.2020

@author: Weatherman
'''

import sys
from pathlib import Path
from glob import glob
from copy import copy
from datetime import datetime, timedelta
import numpy as np
import warnings
import re

from .NumpyRadolanReader import NumpyRadolanReader    # Input
from .ASCIIGridWriter    import ASCIIGridWriter       # Output



def test_sum2D_with_nan():
    print("### test_sum2D_with_nan() ###\n")
    
    # Creates a 2D array with uninitialized values
    a = np.ndarray((2, 4))
    # Datentyp ist Default: 'float64'
    a.fill(7) # Fill it in with a constant value 7
    # auch: B.fill(numpy.nan)   # ! nur float-Array
    a[1][0] = np.nan
    a[1][1] = np.nan
    print("a =\n", a)
    
    b = np.ndarray((2, 4))
    b.fill(1.)
    b[1][1] = np.nan
    print("b =\n", b)
    
    """
    Since the inputs are 2D arrays, you can stack them along the third axis with
    np.dstack and then use np.nansum which would ensure NaNs are ignored, unless
    there are NaNs in both input arrays, in which case output would also have NaN.
    -> The behavior that NaN is returned when both inputs are NaN
    changed for NumPy version >1.9.0. In the newer versions, zero is returned!
    """
    c = np.nansum(np.dstack((a, b)), 2)
    
    print("c =\n", c)


def test_sum_same_radolan_file():
    print("### test_sum_same_radolan_file() ###\n")
    
    test_data_dir = "/run/media/loki/ungesichert/Testdaten/RADOLAN_bin"
    
    rw = Path(test_data_dir) / "bin/raa01-rw_10000-1109041250-dwd---bin.gz"
    
    radolan_file = rw
    
    row = 450
    
    nrr = NumpyRadolanReader(radolan_file)    # FileNotFoundError
    nrr.read()
    #nrr.print_data()
    f1 = nrr.data
    f2 = copy(f1)
    
    print(f1[row])
    print()
    
    """
    Since the inputs are 2D arrays, you can stack them along the third axis with
    np.dstack and then use np.nansum which would ensure NaNs are ignored, unless
    there are NaNs in both input arrays, in which case output would also have NaN.
    -> The behavior that NaN is returned when both inputs are NaN
    changed for NumPy version >1.9.0. In the newer versions, zero is returned!
    """
    fsum = np.nansum(np.dstack((f1, f2)), 2)
    
    print(fsum[row])
    



class NumpyRadolanAdder:
    '''
    classdocs
    '''
    
    def __init__(self, dt_beg, dt_end, data_path, prod_id, asc_filename_path):
        '''
        Constructor
        '''
        
        self.out("dt_beg={}, dt_end={}, prod_id='{}'".format(dt_beg, dt_end, prod_id))
        
        # In:
        self._dt_beg    = dt_beg
        self._dt_end    = dt_end
        self._data_path = data_path
        self._prod_id   = prod_id.lower()    # 'SF' -> 'sf'
        self._asc_filename_path = asc_filename_path
        
        self._first_run = True
        
        # determined:
        self._interval_minutes = 0    # of sum
        
        # Out:
        self._sum_field    = None
        self._nodata_field = None
        
    
    def __str__(self):
        return self.__class__.__name__
    
    def out(self, s, ok=True):
        ''' Ausgabemethode '''
        
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)
    
    
    
    def run(self):
        self.out("run()")
        
        # RADOLAN: raa01-rw_10000-1708020250-dwd---bin
        # RADKLIM: raa01-yw2017.002_10000-1006010650-dwd---bin
        # ...bin, ...bin.gz ?
        general_radolan_file_pattern = "raa01-{}*_10000-{{}}-dwd---bin*".format(self._prod_id)
        
        pattern_all_files_same_type = general_radolan_file_pattern.format('*')
        concrete_radolan_file_pattern = str( Path(self._data_path) / pattern_all_files_same_type )
        print("  determine files...", end=" ")
        l_files_all_same_type = glob(concrete_radolan_file_pattern)
        print("{} files of '{}' type found".format(len(l_files_all_same_type), self._prod_id.upper()))
        
        if not l_files_all_same_type:
            raise FileNotFoundError("no RADOLAN files for adding found!")
        
        # simply take first file to determine properties one time:
        radolan_file = l_files_all_same_type[0]
        time_res_min, prec = self._read_first_file_init(radolan_file)
        
        
        """
        Following complicated way because we don't know, if user adds standard
        RADOLAN data or RADKLIM data or wether the files are gzip compressed.
        The file patterns are slightly different.
        So we create a concrete and surely existing file pattern here.
        """
        # raa01-xx_10000-{}-dwd---bin[.gz]    # insert '{}' for datetime
        general_radolan_file_pattern = re.sub(r'(\d){10}', '{}', radolan_file)
        general_radolan_file_pattern_with_path = str( Path(self._data_path) / general_radolan_file_pattern )
        # -> so now, we need only to substitute the placeholder {} for datetime.
        
        # datetime.timedelta([days[, seconds[, microseconds[, milliseconds[, minutes[, hours[, weeks]]]]]]])
        td_min = timedelta(minutes=time_res_min)
        
        dt = self._dt_beg
        number_of_added_files = 0
        
        while dt <= self._dt_end:
            fn_path = general_radolan_file_pattern_with_path.format( dt.strftime("%y%m%d%H%M") )
            
            if fn_path in l_files_all_same_type:
                self._add(fn_path)
                number_of_added_files += 1
            else:
                self.out("expected file '{}' doesn't exist".format(concrete_radolan_file_pattern), False)
            
            dt += td_min
        # while
        
        #print(self._sum_field[0])
        #print(self._nodata_field[0])
        
        self.out("{} files added".format(number_of_added_files))
        
        # Imprint NaN values that were NaN during the entire run:
        nan_positions = np.where(np.isnan(self._nodata_field))    # find the remaining NaNs
        self._sum_field[nan_positions] = np.nan
        
        ascii_writer = ASCIIGridWriter(self._sum_field, prec, self._asc_filename_path)
        ascii_writer.write()
    
    
    def _read_first_file_init(self, radolan_file):
        self.out("init with first file")
        
        nrr = NumpyRadolanReader(radolan_file)    # FileNotFoundError
        nrr._read_radolan_composite(loaddata=False)    # optimize, no reading of data part neccessary
        
        # Return a new array of given shape and type, filled with fill_value.
        self._nodata_field = np.full(nrr.shape, np.nan)    # all with NaN
        
        time_res_min = nrr.interval
        print("  'time_res' determined: {} minutes".format(time_res_min))
        
        return time_res_min, nrr.precision
        
        
    
    def _add(self, radolan_file):
        #self.out("_add('{}')".format(radolan_file))
        
        nrr = NumpyRadolanReader(radolan_file)    # FileNotFoundError
        nrr.read()
        cur_data = nrr.data
        
        self._interval_minutes += nrr.interval
        
        # every occurence of a pixel (for every looped file) switches a 'nan' to a 'True':
        # np.where return indices where the conditions are true
        indices_non_nan = np.where(~np.isnan(cur_data))
        # switch non nan positions to True. For every loop.
        self._nodata_field[indices_non_nan] = True
        
        if self._first_run:
            self._sum_field = cur_data    # Init
            self._first_run = False
            return
        
        """
        Since the inputs are 2D arrays, you can stack them along the third axis with
        np.dstack and then use np.nansum which would ensure NaNs are ignored, unless
        there are NaNs in both input arrays, in which case output would also have NaN.
        -> The behavior that NaN is returned when both inputs are NaN
        changed for NumPy version >1.9.0. In the newer versions, zero is returned!
        """
        self._sum_field = np.nansum(np.dstack((self._sum_field, cur_data)), 2)
        
    
    
    def get_statistics(self):
        dim = "rows={}, cols={}".format(*self._sum_field.shape)
        _max = np.nanmax(self._sum_field)    # Maximum of the flattened array, ignoring Nan
        _min = np.nanmin(self._sum_field)    # Minimum of the flattened array, ignoring Nan
        total = self._sum_field.size
        valid = np.count_nonzero(~np.isnan(self._sum_field))    # ~ inverts the boolean matrix returned from np.isnan
        nonvalid = np.count_nonzero(np.isnan(self._sum_field))
        
        return dim, _max, _min, self.mean, total, valid, nonvalid
    
    @property
    def mean(self):
        """ nanmean: The arithmetic mean is the sum of the non-NaN elements along the axis
        divided by the number of non-NaN elements.
        When the array has nothing but nan values, it raises a warning:
        /usr/lib64/python3.4/site-packages/numpy/lib/nanfunctions.py:675: RuntimeWarning: Mean of empty slice
        warnings.warn("Mean of empty slice", RuntimeWarning)
        """
        
        # necessary to catch the warning like an exception:
        # To handle warnings as errors simply use this:
        warnings.filterwarnings('error')
        
        # In order to be able to react to this state, the warning is intercepted:
        try:
            return np.nanmean(self._sum_field)
        
        except Warning:
            self.out("Warning catched: return np.nan", False)
            return np.nan
    
    @property
    def interval_minutes(self):
        return self._interval_minutes
    
    
#################################################################


def test_nan():
    '''
    Tests, if NaN's of last added file don't overwrite valid values of the preceding file
    Does result preserve the values of 'f1'?
    '''
    
    test_dir = "/run/media/loki/ungesichert/Testdaten/QGIS/radolan2map/nan-test"
    asc_filename_path = Path(test_dir) / "nan_test.asc"
    
    f1 = Path(test_dir) / "raa01-sf_10000-1807060550-dwd---bin"    # more   data in the north
    f2 = Path(test_dir) / "raa01-sf_10000-1501020550-dwd---bin"    # lesser data in the north
    
    
    adder = NumpyRadolanAdder(None, None, test_dir, 'SF', asc_filename_path)
    # call internal methods directly:
    adder._read_first_file_init(f1)    # init, no adding
    
    adder._add(f1)
    adder._add(f2)
    
    sum_field = adder._sum_field    # fetch reference
    
    # Imprint NaN values that were NaN during the entire run:
    nan_positions = np.where(np.isnan(adder._nodata_field))    # find the remaining NaNs
    sum_field[nan_positions] = np.nan
    
    ascii_writer = ASCIIGridWriter(sum_field, 0.1, asc_filename_path)
    ascii_writer.write()
    
    

if __name__ == '__main__':
    
    #test_sum2D_with_nan()
    #test_sum_same_radolan_file()
    #test_nan(); sys.exit()
    
    
    data_path = "/run/media/loki/ungesichert/Testdaten/RADOLAN_bin/viele/sf"
    prod_id   = 'SF'
    asc_filename_path = "/home/loki/radolan2map/tmp/SF_201501010550-201501070550.asc"
    
    dt_beg = datetime(2015, 1, 1,  5, 50)
    dt_end = datetime(2015, 1, 7,  5, 50)
    
    adder = NumpyRadolanAdder(dt_beg, dt_end, data_path, prod_id, asc_filename_path)
    adder.run()
    
    