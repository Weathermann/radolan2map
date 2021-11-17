'''
ASCIIGridWriter

Creates a ESRI ASCII GRID (to convert this to GeoTIFF afterwards)
from original binary RADOLAN file

Created on 06.12.2020
@author: Weatherman
'''

import sys
import numpy as np

NODATA = -1.0


class ASCIIGridWriter:
    '''
    classdocs
    '''

    
    def __init__(self, np_2Ddata, precision, asc_filename_path):
        '''
        Constructor
        '''
        
        print(self)
        
        self._np_2Ddata = np_2Ddata
        self._asc_filename_path = asc_filename_path
        self._prec = precision    # precision: 1.0, 0.1, 0.01
    
    
    
    def __str__(self):
        return self.__class__.__name__
    
    
    def out(self, s, ok=True):
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)
    
    
    
    
    def write(self):
        """
        Kapselt die verschiedenen internen Methoden (ganze RADOLAN-
        Datenverarbeitung als Schnittstelle nach außen.
        """
        
        nrows, ncols = self._np_2Ddata.shape
        
        d_projected_meters = {
            # key: row, value: tuple of projected meters
            1500: (-673462, -5008645),    # central europe composite, 1500x1400
            1200: (-542962, -3609145),    # WN, 1200x1100
            1100: (-443462, -4758645),    # extended national composite / RADKLIM: 1100x900
             900: (-523462, -4658645)     # national composite: 900x900
        }
        
        try:
            llcorner = d_projected_meters[nrows]
        except KeyError:
            raise NotImplementedError
        
        
        gis_header_template = '''\
ncols     {}
nrows     {}
xllcorner {}
yllcorner {}
cellsize  1000
nodata_value {}'''
        
        # The * before 'tup' tells Python to unpack the tuple into separate arguments,
        # as if you called s.format(tup[0], tup[1], tup[2]) instead.
        #header = gis_header_template.format(*dim, *llcorner, NODATA)
        # -> geht nur Python3
        gis_header = gis_header_template.format(ncols, nrows, llcorner[0], llcorner[1], NODATA)
        
        
        # precision: 1.0, 0.1, 0.01
        if self._prec == 0.1:
            fmt = '%.1f'
        elif self._prec == 0.01:
            fmt = '%.2f'
        else:
            fmt = '%d'    # as integer
        
        
        np_data = np.copy(self._np_2Ddata)    # otherwise values will be changed
        
        #mask = np.isnan(np_data)
        #np_data[mask] = NODATA
        # -> ok
        np_data[np.isnan(np_data)] = NODATA    # set np.nan to ASCII value
        
        # np.flipud(): Flip array in the up/down direction.
        np.savetxt(self._asc_filename_path, np.flipud(np_data), fmt=fmt,
                   delimiter=' ', newline='\n', header=gis_header, comments='') # footer=''
        
        self.out("write(): -> {}".format(self._asc_filename_path))
        
        """
        if np.amax(data_clutter) > 0.0:
            save_file = path.join(self._temp_dir, out_file_bn + "_clutter.asc")
            self._write_ascii_grid(data_clutter, gis_header, save_file)
        
        if np.amax(data_ground) > 0.0:
            save_file = path.join(self._temp_dir, out_file_bn + "_ground.asc")
            self._write_ascii_grid(data_ground, gis_header, save_file)
        
        if np.amax(data_nodata) > 0.0:
            save_file = path.join(self._temp_dir, out_file_bn + "_nodata.asc")
            self._write_ascii_grid(data_nodata, gis_header, save_file)
        """
        
    
    