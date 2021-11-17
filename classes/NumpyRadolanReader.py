#!/usr/bin/python3

'''
Klasse: NumpyRadolanReader

Liest ein RADOLAN-File unter Verwendung der NumPy-Bibliothek ein.

Es wurde weitgehend der Code aus der Datei 'radolan.py' der "wradlib"
übernommen. Die Datei befindet sich auf 
https://github.com/wradlib/wradlib/tree/master/wradlib/io
(evtl. Änderungen abgleichen).

Created on 10.08.2018
@author: Weatherman
'''

from os import path
import sys
import datetime as dt
import numpy as np
import warnings
import gzip


class NumpyRadolanReader:
    '''
    classdocs
    '''


    def __init__(self, fn):
        '''
        Constructor
        '''
        
        self.out("<- '{}'".format(fn))
        
        self._data   = None    # Werte aus dem RADOLAN-Binärteil
        self._meta   = None    # Metadaten aus dem RADOLAN-Header in Form eines Dictionaries
        self._header = None    # der RADOLAN-Header als Ganzes (String)
        
        self._field_station_flag = None    # interpolierte Stationsdaten
        self._field_clutter      = None    # Clutter-Array
        
        #self._missing = -1
        self._missing = np.nan
        
        """
        program behaviour:
        """
        self._zeroes_to_nan = False    # exclude zeroes
        
        self._rx_in_mm = False    # RVP6 -> mm/5min
        
        self._fobj = self._get_radolan_filehandle(str(fn))    # str() if Path
        # FileNotFoundError
        
    
    def __str__(self):
        return self.__class__.__name__
    
    def out(self, s, ok=True):
        ''' Ausgabemethode '''
        
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)
    

    
    def _get_radolan_filehandle(self, fname):
        """Opens radolan file and returns file handle
        Parameters
        ----------
        fname : string
            filename
        Returns
        -------
        f : object
            filehandle
        
        aus:
        https://github.com/wradlib/wradlib/blob/master/wradlib/io/radolan.py
        - modifiziert (05.11.2018).
        """
        
        # open file handle
        if fname.endswith('.gz'):
            f = gzip.open(fname, 'rb')
            #f.read(1)
        else:
            f = open(fname, 'rb')    # 'rb' wichtig für ETX-Char in Header-Funktion
            #f.read(1)
        
        # rewind file
        #f.seek(0, 0)
        
        return f
    
    
    def read(self):
        ''' RADOLAN-File lesen '''
        self.out("read()")
        
        self._data, self._meta = self._read_radolan_composite()
        
        if self._rx_in_mm:
            self._rvp6_to_mm()
        
        
    
    def _read_radolan_composite(self, loaddata=True):
        """Read quantitative radar composite format of the German Weather Service
    
        The quantitative composite format of the DWD (German Weather Service) was
        established in the course of the
        RADOLAN project and includes several file
        types, e.g. RX, RO, RK, RZ, RP, RT, RC, RI, RG, PC, PG and many, many more.
        (see format description on the RADOLAN project homepage :cite:`DWD2009`).
        At the moment, the national RADOLAN composite is a 900 x 900 grid with 1 km
        resolution and in polar-stereographic projection. There are other grid
        resolutions for different composites (eg. PC, PG)
    
        Warning
        -------
        This function already evaluates and applies the so-called
        PR factor which is specified in the header section of the RADOLAN files.
        The raw values in an RY file are in the unit 0.01 mm/5min, while
        read_radolan_composite returns values in mm/5min (i. e. factor 100 higher).
        The factor is also returned as part of attrs dictionary under
        keyword "precision".
    
        Parameters
        ----------
        f : string or file handle
            path to the composite file or file handle
        missing : int
            value assigned to no-data cells
        loaddata : bool
            True | False, If False function returns (None, attrs)
    
        Returns
        -------
        output : tuple
            tuple of two items (data, attrs):
                - data : :func:`numpy:numpy.array` of shape (number of rows,
                  number of columns)
                - attrs : dictionary of metadata information from the file header
    
        Examples
        --------
        See :ref:`/notebooks/radolan/radolan_format.ipynb`.
        """
        
        mask = 0xFFF  # max value integer
    
        # If a file name is supplied, get a file handle
        try:
            self._header = self._read_radolan_header()
        except AttributeError:
            f = get_radolan_filehandle(f)
            self._header = read_radolan_header(f)
        
        attrs = self._parse_dwd_composite_header()
    
        if not loaddata:
            self._fobj.close()
            self._meta = attrs
            return None, attrs
        
        attrs["nodataflag"] = self._missing
        
        if not attrs["radarid"] == "10000":
            warnings.warn("WARNING: You are using function e" +
                          "wradlib.io.read_RADOLAN_composit for a non " +
                          "composite file.\n " +
                          "This might work...but please check the validity " +
                          "of the results")
        
        
        all_pixels = attrs['nrow'] * attrs['ncol']
        
        # read the actual data
        indat = self._read_radolan_binary_array(attrs['datasize'])
        
        if attrs['producttype'] in ('RX', 'EX', 'WX'):
            # convert to 8bit integer
            arr = np.frombuffer(indat, np.uint8).astype(np.uint8)
            # numpy.where(condition[, x, y])
            # Return elements, either from x or y, depending on condition.
            #nodata = np.where(arr == 250, self._missing, arr)
            nodata   = np.where(arr == 250)[0]
            clu_mask = np.where(arr == 249)[0]
            attrs['cluttermask'] = clu_mask
            
            # apply precision factor
            # this promotes arr to float if precision is float
            arr = arr * attrs['precision']
        
        elif attrs['producttype'] in ('PG', 'PC'):
            arr = decode_radolan_runlength_array(indat, attrs)
        else:
            # convert to 16-bit integers
            arr = np.frombuffer(indat, np.uint16).astype(np.uint16)    # uint16: Unsigned integer (0 to 65535)
            # evaluate bits 13, 14, 15 and 16
            # where: The numpy.where function takes a condition as an argument and
            # returns >>the indices<< where that condition is true.
            secondary = np.where(arr & 0x1000)[0]
            attrs['secondary'] = secondary
            nodata   = np.where(arr & 0x2000)[0]
            negative = np.where(arr & 0x4000)[0]
            clu_mask = np.where(arr & 0x8000)[0]
            
            # Gleiches Vorgehen für Stationsflag- und Clutter-Feld:
            
            station_flag_field = np.zeros(all_pixels, int)    # empty station flag field
            station_flag_field[secondary] = 1
            
            # mask out the last 4 bits
            arr &= mask
            # consider negative flag if product is RD (differences from adjustment)
            if attrs['producttype'] == 'RD':
                # NOT TESTED, YET
                arr[negative] = -arr[negative]
            
            # apply precision factor
            # this promotes arr to float if precision is float
            arr = arr * attrs['precision']
            
            self._field_station_flag = station_flag_field.reshape((attrs['nrow'], attrs['ncol']))
        # else
        
        # set nodata value
        #arr[nodata] = self._missing
        arr[nodata] = np.nan    # besser für mean-Berechnung
        
        attrs['cluttermask'] = clu_mask
        #print(clu_mask)    # Struktur (Beispiel, Indizes): [  5877   5878   6778 ... 809824 809825 809828]
        #clutter = np.zeros(all_pixels, bool)    # erstmal 'flattened array'; bool: zeros = False
        clutter = np.zeros(all_pixels, int)    # empty clutter field
        #print(clutter)
        clutter[clu_mask] = 1    # True
        self._field_clutter = clutter.reshape((attrs['nrow'], attrs['ncol']))
        
        # Exclude zeros. Only possible if values are of float type:
        if self._zeroes_to_nan:
            arr[arr==0] = np.nan
        
        # anyway, bring it into right shape
        arr = arr.reshape((attrs['nrow'], attrs['ncol']))
        
        return arr, attrs

    
    
    def _read_radolan_header(self):
        """Reads radolan ASCII header and returns it as string
        
        Parameters
        ----------
        fid : object
            file handle
        
        Returns
        -------
        header : string
        """
        # rewind, just in case...
        self._fobj.seek(0, 0)
        
        ETX = b'\x03'    # Header-Ende: End Of Text
        
        header = ''
        while True:
            mychar = self._fobj.read(1)
            if not mychar:
                raise EOFError('Unexpected EOF detected while reading '
                               'RADOLAN header')
            if mychar == ETX:
                break
            #header += str(mychar.decode())
            header += mychar.decode()    # 15.03.2019, byte -> string
        return header

    
    def _parse_dwd_composite_header(self):
        """Parses the ASCII header of a DWD quantitative composite file
    
        Parameters
        ----------
        header : string
            (ASCII header)
    
        Returns
        -------
        output : dictionary
            of metadata retrieved from file header
        """
        
        header = self._header    # abkürzen
        
        # empty container
        out = {}
        
        # RADOLAN product type def
        out["producttype"] = header[0:2]
        # file time stamp as Python datetime object
        out["datetime"] = dt.datetime.strptime(header[2:8] + header[13:17] + "00",
                                               "%d%H%M%m%y%S")
        # radar location ID (always 10000 for composites)
        out["radarid"] = header[8:13]
    
        # get dict of header token with positions
        head = self._get_radolan_header_token_pos(header)
        # iterate over token and fill output dict accordingly
        # for k, v in head.iteritems():
        for k, v in head.items():
            if v:
                if k == 'BY':
                    out['datasize'] = int(header[v[0]:v[1]]) - len(header) - 1
                if k == 'VS':
                    out["maxrange"] = {0: "100 km and 128 km (mixed)",
                                       1: "100 km",
                                       2: "128 km",
                                       3: "150 km"}.get(int(header[v[0]:v[1]]),
                                                        "100 km")
                if k == 'SW':
                    out["radolanversion"] = header[v[0]:v[1]].strip()
                if k == 'PR':
                    out["precision"] = float('1' + header[v[0]:v[1]].strip())
                if k == 'INT':
                    out["intervalseconds"] = int(header[v[0]:v[1]]) * 60
                if k == 'U':
                    out["interval_unit"] = int(header[v[0]:v[1]])    # 0 (minutes) or 1 (days)
                if k == 'GP':
                    dimstrings = header[v[0]:v[1]].strip().split("x")
                    out["nrow"] = int(dimstrings[0])
                    out["ncol"] = int(dimstrings[1])
                if k == 'VR':
                    version = header[v[0]:v[1]]
                    self.out("RADKLIM version '{}'".format(version))
                    out['VR'] = version
                if k == 'BG':
                    dimstrings = header[v[0]:v[1]]
                    dimstrings = (dimstrings[:int(len(dimstrings) / 2)],
                                  dimstrings[int(len(dimstrings) / 2):])
                    out["nrow"] = int(dimstrings[0])
                    out["ncol"] = int(dimstrings[1])
                if k == 'LV':
                    lv = header[v[0]:v[1]].split()
                    out['nlevel'] = np.int(lv[0])
                    out['level'] = np.array(lv[1:]).astype('float')
                if k == 'MS':
                    locationstring = (header[v[0]:].strip().split("<")[1].
                                      split(">")[0])
                    out["radarlocations"] = locationstring.split(",")
                if k == 'ST':
                    locationstring = (header[v[0]:].strip().split("<")[1].
                                      split(">")[0])
                    out["radardays"] = locationstring.split(",")
                if k == 'CS':
                    out['indicator'] = {0: "near ground level",
                                        1: "maximum",
                                        2: "tops"}.get(int(header[v[0]:v[1]]))
                if k == 'MX':
                    out['imagecount'] = int(header[v[0]:v[1]])
                if k == 'VV':
                    out['predictiontime'] = int(header[v[0]:v[1]])
                if k == 'MF':
                    out['moduleflag'] = int(header[v[0]:v[1]])
                if k == 'QN':
                    out['quantification'] = int(header[v[0]:v[1]])
        return out

    
    
    def _get_radolan_header_token_pos(self, header):
        """Get Token and positions from DWD radolan header
    
        Parameters
        ----------
        header : string
            (ASCII header)
    
        Returns
        -------
        head : dictionary
            with found header tokens and positions
        """
        
        head_dict = self._get_radolan_header_token()
    
        for token in head_dict.keys():
            d = header.rfind(token)
            if d > -1:
                head_dict[token] = d
        head = {}
        
        result_dict = {}
        result_dict.update((k, v) for k, v in head_dict.items() if v is not None)
        for k, v in head_dict.items():
            if v is not None:
                start = v + len(k)
                filt = [x for x in result_dict.values() if x > v]
                if filt:
                    stop = min(filt)
                else:
                    stop = len(header)
                head[k] = (start, stop)
            else:
                head[k] = v
    
        return head
    
    
    def _get_radolan_header_token(self):
        """Return array with known header token of radolan composites
    
        Returns
        -------
        head : dict
            with known header token, value set to None
        """
        head = {'BY': None, 'VS': None, 'SW': None, 'PR': None,
                'INT': None, 'U': None, 'GP': None, 'MS': None, 'LV': None,    # U = Unit
                'CS': None, 'MX': None, 'BG': None, 'ST': None,
                'VV': None, 'MF': None, 'QN': None,
                'U': None, 'VR': None    # RADKLIM
                }
        return head

    
    def _read_radolan_binary_array(self, size):
        """Read binary data from file given by filehandle
    
        Parameters
        ----------
        fid : object
            file handle
        size : int
            number of bytes to read
    
        Returns
        -------
        binarr : string
            array of binary data
        """
        binarr = self._fobj.read(size)
        self._fobj.close()
        
        if len(binarr) != size:
            raise IOError('{0}: File corruption while reading\n"{1}"!\nCould not '
                          'read enough data.'.format(__name__, self._fobj.name))
        return binarr
    
    
    def _rvp6_to_mm(self):
        # Umrechnung von RVP6-Einheiten in dBZ:
        
        self._rx_in_mm = False    # not again
        self._meta['precision'] = 0.01    # overwrite precision - analog RY
        
        """
        1/2: to dBZ
        """
        
        """
        2/2: dBZ -> mm
        Einheit im DX: RVP-6-Unit bzw. 0.01 mm/fünf Minuten
        -> Umrechnung nach dBZ: (RVP-6-Unit/2) - 32.5 = dBZ-Wert
        -> dBZ-Wert = 10 * log (Z)
        -> Umrechnung von der Radarreflektivität Z in die Niederschlagsintensität
        R in mm/h über:
        Z = 256 * R 1.42
        
        Umstellen der Formel nach R:
        Z = aR^b <==> R = (Z/a)^1/b = (10^dBZ/10 /a)^1/b
        
        s. http://radar-info.fzk.de/abc.html -> Reflektivität
        """
        
        """ By default, the nditer treats the input operand as a read-only object.
        To be able to modify the array elements, you must specify either read-write
        or write-only mode using the ‘readwrite’ or ‘writeonly’ per-operand flags. """
        ''' -> Fehler mit älteren NumPy-Versionen?
        with np.nditer(self._data, op_flags=['readwrite']) as it:
            for x in it:
                x[...] = (x / 2) - 32.5
        '''
        
        # Konstanten: vor allem abhängig von der Art des Niederschlags (Tropfenspektrum):
        a = 256
        b = 1.42
        
        for x in np.nditer(self._data, op_flags=['readwrite']):
            if x == self._missing:
                continue
            
            # dBZ:
            #x[...] = (x / 2) - 32.5
            dBZ = (x / 2) - 32.5
            
            # mm:
            Z = 10.0 ** (dBZ/10.0)    # ** = Exponent
            Za = Z / a
            
            mm = Za ** (1/b)
            
            mm5min = mm/12.0    # mm/h -> mm/5 min
            
            x[...] = mm5min
        
    
    
    def print_meta(self):
        ''' print the available attributes '''
        self.out("print_meta():")
        print("Attributes:")
        for key, value in self._meta.items():
            print(key + ':', value)
    
    def print_data(self):
        self.out("print_data():")
        print(self._data)
    
    def print_statistics(self):
        print("Statistics:")
        print("-----------")
        filename, dim, _max, _min, mean, total, valid, nonvalid = self.get_statistics()
        
        print("File:   ", filename)
        print("Shape:  ", dim)
        print("Maximum:", np.nanmax(_max))
        print("Minimum:", np.nanmin(_min))
        print("Mean:   ", mean)
        print("total number of pixels:", total)
        print("Number of valid pixels:", valid)
        print("Number of NaN pixels:  ", nonvalid)
    
    
    def get_statistics(self):
        dim = "rows={}, cols={}".format(*self.data.shape)
        _max = np.nanmax(self._data)    # Maximum of the flattened array, ignoring Nan
        _min = np.nanmin(self._data)    # Minimum of the flattened array, ignoring Nan
        total = self._data.size
        valid = np.count_nonzero(~np.isnan(self._data))    # ~ inverts the boolean matrix returned from np.isnan
        nonvalid = np.count_nonzero(np.isnan(self._data))
        
        return self.simple_name, dim, _max, _min, self.mean, total, valid, nonvalid
    
    
    @property
    def exclude_zeroes(self):
        return self._zeroes_to_nan
    @exclude_zeroes.setter
    def exclude_zeroes(self, b):
        self._zeroes_to_nan = b
        if b:
            self.out("WARN: all zeros will be excluded (set to NaN)!")
    
    @property
    def rx_in_mm(self):
        return self._rx_in_mm
    @rx_in_mm.setter
    def rx_in_mm(self, b):
        self._rx_in_mm = b
        if b:
            self.out("RVP6 units -> mm/5min")
    
    @property
    def prod_id(self):
        return self._meta['producttype']    # RW, SF, ...
    
    @property
    def shape(self):
        return self.meta['nrow'], self.meta['ncol']    # int, int
    @property
    def missing(self):
        return self._missing
    @missing.setter
    def missing(self, val):
        self._missing = val
    
    @property
    def data(self):
        # if RX and requested mm/5min:
        if self._rx_in_mm:
            self._rvp6_to_mm()
        
        return self._data
    
    @property
    def station_flags(self):
        return self._field_station_flag
    
    @property
    def clutter(self):
        return self._field_clutter
    
    @property
    def meta(self):
        return self._meta
    
    @property
    def header(self):
        return self._header
    
    @property
    def datetime(self):
        return self._meta["datetime"]
    
    @property
    def precision(self):
        return self._meta['precision']
    
    @property
    def interval(self):
        unit = self.interval_unit    # 0 (minutes) or 1 (days)
        
        interval = self._meta['intervalseconds'] / 60
        
        if unit == 0:
            return interval    # minutes
        
        # interval = days
        return interval * 1440    # 1440 = all minutes of a day
        
        
    @property
    def interval_unit(self):
        try:
            return self._meta['interval_unit']    # 0 (minutes) or 1 (days)
        except KeyError:    # not set for all products
            return 0    # interval in unit minutes
    
    @property
    def mean(self):
        """ nanmean: The arithmetic mean is the sum of the non-NaN elements along the axis
        divided by the number of non-NaN elements.
        When the array has nothing but nan values, it raises a warning:
        /usr/lib64/python3.4/site-packages/numpy/lib/nanfunctions.py:675: RuntimeWarning: Mean of empty slice
        warnings.warn("Mean of empty slice", RuntimeWarning)
        """
        
        # nötig, um die warning wie eine Exception aufzufangen:
        # To handle warnings as errors simply use this:
        warnings.filterwarnings('error')
        
        # Um auf diesen Zustand reagieren zu können, wird die Warning abgefangen:
        try:
            return np.nanmean(self._data)
        
        except Warning as w:
            self.out("Warning aufgefangen (File: '{}'):".format(self._fobj.name), False)
            print(w, file=sys.stderr)
            self.out("return np.nan", False)
            return np.nan
    
    ''' # manuell verglichen (04.11.2018) - OK
        sum = 0
        valids = 0
        
        # Jedes Element eines Numpy-Arrays durchgehen:
        for val in np.nditer(self._data):
            if np.isnan(val):
                continue
            _sum += val
            valids += 1
        # for
        
        print("sum:",    _sum)
        print("valids:", valids)
        print("mean:",   _sum/valids)
    '''
    
    @property
    def simple_name(self):
        # Beispiel: "RW_20190329-0650", "RADKLIM-RW_20190329-0650"
        radklim = "RADKLIM-" if self.is_radklim  else ""
        return "{}{}_{}".format(radklim, self._meta['producttype'], self._meta['datetime'].strftime('%Y%m%d-%H%M'))
    
    # Booleans
    
    @property
    def has_interpolated_station_data(self):
        return np.any(self._field_station_flag == 1)    # Check, ob irgendeine Stelle im Array 1 ist
    @property
    def has_clutter(self):
        return np.any(self._field_clutter == 1)    # Check, ob irgendeine Stelle im Array 1 ist
    
    @property
    def is_radklim(self):
        try:
            version = self._meta['VR']
        except KeyError:    # Key is not present
            return None
        
        return version
    
    
'''
def test_test_radolan_file():
    print("### test_test_radolan_file() ###")
    
    test_data_dir = "/run/media/loki/ungesichert/Testdaten/RADOLAN_bin/bin"
    radolan_file = path.join(test_data_dir, "raa01-rw_10000-1109041250-dwd---bin.gz")    # Test mit gzip
    
    nrr = NumpyRadolanReader(radolan_file)    # FileNotFoundError
    # -> file handle open
    header = nrr._read_radolan_header()
    nrr._fobj.close()
    
    print(header)
'''



if __name__ == "__main__":
    
    test_data_dir = "/run/media/loki/ungesichert/Testdaten/RADOLAN_bin"
    ry = path.join(test_data_dir, "bin/raa01-ry_10000-1605291650-dwd---bin")
    rw = path.join(test_data_dir, "bin/raa01-rw_10000-1109041250-dwd---bin.gz")    # Test mit gzip
    rx = path.join(test_data_dir, "bin/raa01-rx_10000-1212181400-dwd---bin")
    rh = path.join(test_data_dir, "pix/bestrain.pix")
    rb = path.join(test_data_dir, "pix/borama.pix")    # enthält Clutter
    sm = path.join(test_data_dir, "bin/raa01-sm_10000-2012230550-dwd---bin")    # test interval_unit
    
    #radolan_file = ry
    radolan_file = rw
    #radolan_file = rh
    #radolan_file = rb
    #radolan_file = rx
    #radolan_file = sm
    
    nrr = NumpyRadolanReader(radolan_file)    # FileNotFoundError
    #nrr.rx_in_mm = True    # for RX
    nrr.read()
    
    print()
    
    print(nrr.header)
    print()
    
    nrr.print_meta()
    print()
    
    print("datetime:", nrr.datetime)
    print()
    
    print("interval:", nrr.interval)
    print()
    
    #print("interval_unit:", nrr.interval_unit)
    #print()
    
    nrr.print_data()
    print()
    
    print("Shape:", nrr.data.shape)
    print()
    
    
    #print("Clutter:", nrr.clutter)
    #print(np.any(nrr.clutter == True))    # Check, ob irgendeine Stelle im Clutter-Array True ist
    #print()
    
    nrr.print_statistics()
    print()
    
    