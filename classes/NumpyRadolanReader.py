#!/usr/bin/python3
import sys
from pathlib import Path
import datetime as dt
import numpy as np
import warnings
import gzip
import bz2


class NumpyRadolanReader:
    """
    Klasse: NumpyRadolanReader

    Liest ein RADOLAN-File unter Verwendung der NumPy-Bibliothek ein.

    Es wurde weitgehend der Code aus der Datei 'radolan.py' der "wradlib"
    übernommen. Die Datei befindet sich auf
    https://github.com/wradlib/wradlib/tree/master/wradlib/io
    (evtl. Änderungen abgleichen).

    Created on 10.08.2018
    @author: Weatherman
    """


    def __init__(self, fn):
        """
        Constructor
        """
        
        self.out(f"<- '{fn}'")
        
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
        # FileNotFoundError, IOError

        # Properties
        self._dbz_product = False    # e.g. WN
        
    
    def __str__(self):
        return self.__class__.__name__
    
    def out(self, s, ok=True):
        """ Ausgabemethode """
        
        if ok:
            print(f"{self}: {s}")
        else:
            print(f"{self}: {s}", file=sys.stderr)
    

    
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
        elif fname.endswith('.bz2'):
            if fname.endswith('.tar.bz2'):  # 'WN' is packed in this way (2022)
                raise IOError("cannot process tar files directly, please unpack first!")
            f = bz2.open(fname, 'rb')
        else:
            f = open(fname, 'rb')    # 'rb' wichtig für ETX-Char in Header-Funktion
        
        # rewind file
        #f.seek(0, 0)
        
        return f
    
    
    def read(self):
        """ RADOLAN-File lesen """
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

        prod_id = attrs['producttype']
        
        all_pixels = attrs['nrow'] * attrs['ncol']
        
        # read the actual data
        indat = self._read_radolan_binary_array(attrs['datasize'])
        clu_mask = None

        if prod_id in ('RX', 'EX', 'WX'):
            # convert to 8bit integer
            arr = np.frombuffer(indat, np.uint8).astype(np.uint8)
            # numpy.where(condition[, x, y])
            # Return elements, either from x or y, depending on condition.
            #nodata = np.where(arr == 250, self._missing, arr)
            nodata   = np.where(arr == 250)[0]
            clu_mask = np.where(arr == 249)[0]

        # 4 byte product - convert to 32-bit integers
        elif prod_id == 'HG':
            #arr = np.frombuffer(indat, np.uint32).astype(np.uint32)  # uint32: Unsigned integer (0 to 4294967295)
            arr = np.frombuffer(indat, np.uint32)  # reicht
            """
            kein Bit gesetzt: No-Echo:   0000 0000 | 0000 0000 | 0000 0000 | 0000 0000    =          0
            Bit  1: Nicht klassifiziert: 0000 0000 | 0000 0000 | 0000 0000 | 0000 0001    =          1 (2^1-1)
            Bit  4: Sprühregen:          0000 0000 | 0000 0000 | 0000 0000 | 0000 1000    =          8 (2^4-1)
            Bit  5: Regen:               0000 0000 | 0000 0000 | 0000 0000 | 0001 0000    =         16 (2^5-1)
            Bit  7: Schnee:              0000 0000 | 0000 0000 | 0000 0000 | 0100 0000    =         64 (2^7-1)
            Bit 5 + 7: Schneeregen:      0000 0000 | 0000 0000 | 0000 0000 | 0101 0000    =         80 (2^5-1 + 2^7-1)
            Bit 13: Graupel:             0000 0000 | 0000 0000 | 0001 0000 | 0000 0000    =       4096 (2^13-1)
            Bit 14: Hagel:               0000 0000 | 0000 0000 | 0010 0000 | 0000 0000    =       8192 (2^14-1)
            Bit 25: Kein Niederschlag:   0000 0001 | 0000 0000 | 0000 0000 | 0000 0000    =   16777216 (2^25-1)
            Bit 32: No-Data:             1000 0000 | 0000 0000 | 0000 0000 | 0000 0000    = 2147483648 (2^32-1)
            """
            nodata = np.where(arr == 2147483648)[0]    # Bit 32: No-Data -> wird später zu NaN, kein Int-Wert mehr

        # 2 byte product (RADOLAN) - convert to 16-bit integers
        else:
            arr = np.frombuffer(indat, np.uint16).astype(np.uint16)  # uint16: Unsigned integer (0 to 65535)
            # evaluate bits 13, 14, 15 and 16
            # where: The numpy.where function takes a condition as an argument and
            # returns >>the indices<< where that condition is true.
            if prod_id != 'WN':
                secondary = np.where(arr & 0x1000)[0]    # Bit 13
                attrs['secondary'] = secondary
                clu_mask = np.where(arr & 0x8000)[0]  # Bit 16
                # Gleiches Vorgehen für Stationsflag- und Clutter-Feld:
                station_flag_field = np.zeros(all_pixels, int)    # empty station flag field
                station_flag_field[secondary] = 1
                self._field_station_flag = station_flag_field.reshape((attrs['nrow'], attrs['ncol']))
            # WN

            nodata = np.where(arr & 0x2000)[0]    # Bit 14, for WN too

            # mask out the last 4 bits
            arr &= mask
            # consider negative flag if product is RD (differences from adjustment)
            if prod_id == 'RD':
                # NOT TESTED, YET
                negative = np.where(arr & 0x4000)[0]  # Bit 15
                arr[negative] = -arr[negative]
        # else
        # End of product type check

        # apply precision factor
        # this promotes arr to float if precision is float
        arr = arr * attrs['precision']

        # set nodata value
        if nodata is not None:
            #arr[nodata] = self._missing
            arr[nodata] = np.nan    # better for mean calculation

        # Value "correction" (simplification) for HG product:
        if prod_id == 'HG':
            """ Ersetzungstabelle (hohe) Integerwerte -> einfachen Hydrometeorklassen-Integern
            Klasse:                Vorschlag (nach Abbildung in HG-Formatbeschreibung)
            -------                ---------
            No-Echo: bleibt bei 0, gilt nicht als Hydrometeorklasse """
            arr[arr == 1] = 2           # Nicht klassifizierbar
            arr[arr == 8] = 3           # Sprühregen
            arr[arr == 16] = 4          # Regen
            arr[arr == 80] = 5          # Schneeregen
            arr[arr == 64] = 6          # Schnee
            arr[arr == 4096] = 7        # Graupel
            arr[arr == 8192] = 8        # Hagel
            # !! Attention: don't overwrite the replaced value '1' above! :-)
            arr[arr == 16777216] = 1    # Kein Niederschlag

        elif prod_id == 'WN':
            self._dbz_product = True
            self._wn_rvp6units_to_dbz(arr)

        if clu_mask is not None:
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
        """ Reads RADOLAN ASCII header and returns it as string

        Returns
        -------
        header : string
        """
        # _fobj: object file handle
        # rewind, just in case...
        self._fobj.seek(0, 0)
        
        ETX = b'\x03'    # Header-Ende: End Of Text
        
        header = ''
        while True:
            mychar = self._fobj.read(1)
            if not mychar:
                raise EOFError('Unexpected EOF detected while reading RADOLAN header')
            if mychar == ETX:
                break
            #header += str(mychar.decode())
            header += mychar.decode()    # 15.03.2019, byte -> string
        return header

    
    def _parse_dwd_composite_header(self):
        """ Parses the ASCII header of a DWD quantitative composite file

        Returns
        -------
        output : dictionary
            of metadata retrieved from file header
        """

        # header: string (ASCII header)
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
                    out["format_version"] = int(header[v[0]:v[1]])    # POLARA/WGS system?
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
                    self.out(f"RADKLIM version '{version}'")
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
                'VR': None    # RADKLIM
                }
        return head

    
    def _read_radolan_binary_array(self, size):
        """Read binary data from file given by filehandle
    
        Parameters
        ----------
        size : int
            number of bytes to read
    
        Returns
        -------
        binarr : string
            array of binary data
        """
        # _fobj: object file handle
        binarr = self._fobj.read(size)
        self._fobj.close()
        
        if len(binarr) != size:
            raise IOError(f'{__name__}: File corruption while reading\n'
                          f'"{self._fobj.name}"!\nCould not read enough data.')
        return binarr
    
    
    def _rvp6_to_mm(self):
        """ Calculate RVP6 units in dBZ """
        
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

    def _wn_rvp6units_to_dbz(self, arr):
        """
        Calculate the RVP6 units in WN product (in tenths) to dBZ values.
        !Assumption: Values are already multiplied with 'precision'!
        """

        self.out("_wn_rvp6units_to_dbz: calculate dBZ from RVP6 units...")

        """
        - Create a function that you want to apply on each element of NumPy Array.
          For example function with name add().
        - Pass this add() function to the vectorize class. It returns a vectorized function.
        - Pass the NumPy Array to the vectorized function.
        - The vectorized function will apply the the earlier assigned function ( add() )
          to each element of the array and returns a NumPy Array containing the result.
        """
        #def to_dbz(val):
        #    if val in (self._missing, 0):
        #        return val
        #    return (val / 2) - 32.5

        # 02 4E hex (or reverse)
        # = 590 decimal
        # * precision=0.1
        # -> 59
        #print(to_dbz(59))    # -3.0 dBZ -> OK

        # Apply add() function to array.
        #rvp6_to_dbz = np.vectorize(to_dbz)
        #return rvp6_to_dbz(arr)
        """
        => This doesn't seem to give correct results
        """

        #for x in np.nditer(arr, op_flags=["readwrite"]):  # OK
        with np.nditer(arr, op_flags=['readwrite']) as it:
            for x in it:
                if x == self._missing:  # or x == 0:
                    continue

                """ dBZ: x = pixel value
                x = x * precision (0.1)
                x[...] = (x / 2) - 32.5
                """
                x[...] = (x / 2) - 32.5

    def print_meta(self):
        """ print the available attributes """
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
        rows, cols = self.data.shape
        dim = f"rows={rows}, cols={cols}"

        _max, _min, mean = None, None, None
        if self.prod_id != "HG":    # for 'HG'-product not useful
            _max = np.nanmax(self._data)    # Maximum of the flattened array, ignoring Nan
            _min = np.nanmin(self._data)    # Minimum of the flattened array, ignoring Nan
            mean = self.mean
        total = self._data.size
        valid = np.count_nonzero(~np.isnan(self._data))    # ~ inverts the boolean matrix returned from np.isnan
        nonvalid = np.count_nonzero(np.isnan(self._data))
        
        return self.simple_name, dim, _max, _min, mean, total, valid, nonvalid
    
    
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
        """ RW, SF, HG, ... """
        return self._meta['producttype']
    
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
    def prediction_time(self):
        try:
            return self._meta['predictiontime']
        except KeyError:    # not set for all products
            return 0    # analysis

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
            self.out(f"Warning aufgefangen (File: '{self._fobj.name}'):", False)
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

        s_date = f"{self._meta['datetime']:%Y%m%d-%H%M}"
        # Add forecast step to date if available:
        # this is to distinguish multiple layers with same datetime but forecast step
        # otherwise overwrites layer:
        if self.has_prediction_time:
            s_date += f"_{self.prediction_time:03}"

        return f"{radklim}{self.prod_id}_{s_date}"
    
    # Booleans
    @property
    def is_polara(self):
        return self._meta['format_version'] >= 5  # see "HG" format description

    @property
    def is_dbz(self):  # needed for adjusted NODATA value (-1 isn't suitable for negative dBZ)
        return self._dbz_product

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

    @property
    def has_prediction_time(self):
        try:
            self._meta['predictiontime']
            return True
        except KeyError:    # Key is not present
            return False




if __name__ == "__main__":
    
    test_data_dir = Path("/run/media/loki/ungesichert/Testdaten/RADOLAN_bin")
    ry = test_data_dir / "bin/raa01-ry_10000-1605291650-dwd---bin"
    rw = test_data_dir / "bin/raa01-rw_10000-1109041250-dwd---bin.gz"    # Test with gzip
    rx = test_data_dir / "bin/raa01-rx_10000-1212181400-dwd---bin"
    rh = test_data_dir / "pix/bestrain.pix"
    rb = test_data_dir / "pix/borama.pix"    # enthält Clutter
    sm = test_data_dir / "bin/raa01-sm_10000-2012230550-dwd---bin"    # test interval_unit
    hg = Path("/run/media/loki/ungesichert/Testdaten/HG/HG2212101900_000")
    wn = Path("/run/media/loki/ungesichert/Testdaten/WN/20221224-2200/WN2212242200_000")
    #wn = Path("/run/media/loki/ungesichert/Testdaten/WN/20221226-1300/WN2212261300_000")

    #radolan_file = ry
    #radolan_file = rw
    #radolan_file = rh
    #radolan_file = rb
    #radolan_file = rx
    #radolan_file = sm
    #radolan_file = hg
    radolan_file = wn


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
