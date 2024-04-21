import sys
from pathlib import Path
import numpy as np

from .NumpyRadolanReader import NumpyRadolanReader

default_nodata_value = -1.0


class ASCIIGridWriter:
    """ASCIIGridWriter

    Creates a ESRI ASCII GRID (to convert this to GeoTIFF afterwards)
    from original binary RADOLAN file

    Created on 06.12.2020
    @author: Weatherman"""

    def __init__(self, np_2Ddata, precision, asc_filename_path, nodata_value=default_nodata_value):
        """
        :param np_2Ddata:
        :param precision:
        :param asc_filename_path:
        :param nodata_value: possibility to specify another missing value,
                            e.g. for dBZ products (e.g. -50.0; -32.5 = neg. maximum)
        """
        print(self)
        
        self._np_2Ddata = np_2Ddata
        self._asc_filename_path = asc_filename_path
        self._prec = precision    # precision: 1.0, 0.1, 0.01

        # catch 'None':
        if nodata_value is None:
            nodata_value = default_nodata_value

        self._nodata_value = nodata_value

        if nodata_value != default_nodata_value:
            self.out(f"nodata_value: {nodata_value}")

    def __str__(self):
        return self.__class__.__name__

    def out(self, s, ok=True):
        if ok:
            print(f"{self}: {s}")
        else:
            print(f"{self}: {s}", file=sys.stderr)
    
    def write(self):
        """
        Kapselt die verschiedenen internen Methoden (ganze RADOLAN-
        Datenverarbeitung als Schnittstelle nach außen.
        """
        
        nrows, ncols = self._np_2Ddata.shape
        
        d_projected_meters = {
            # key: row, value: tuple of projected meters: x0, y0
            1500: (-673462, -5008645),    # central europe composite, 1500x1400
            1200: (-543197, -4822589),    # WN, HG, 1200x1100 *)
            1100: (-443462, -4758645),    # extended national composite / RADKLIM: 1100x900
             900: (-523462, -4658645)     # national composite: 900x900
        }
        # *) taken y0 from HG format description and minus 1200 kilometers.
        # They specify the _upper_ left corner there.

        try:
            llcorner = d_projected_meters[nrows]
        except KeyError:
            raise NotImplementedError
        
        l_gis_header_template = []
        l_gis_header_template.append(f"ncols     {ncols}")
        l_gis_header_template.append(f"nrows     {nrows}")
        l_gis_header_template.append(f"xllcorner {llcorner[0]}")
        l_gis_header_template.append(f"yllcorner {llcorner[1]}")
        l_gis_header_template.append("cellsize  1000")
        l_gis_header_template.append(f"nodata_value {self._nodata_value}")

        gis_header = "\n".join(l_gis_header_template)

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
        np_data[np.isnan(np_data)] = self._nodata_value    # set np.nan to ASCII value
        
        # np.flipud(): Flip array in the up/down direction.
        np.savetxt(self._asc_filename_path, np.flipud(np_data), fmt=fmt,
                   delimiter=' ', newline='\n', header=gis_header, comments='')  # footer=''
        
        self.out(f"write(): -> {self._asc_filename_path}")
        
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
        

def test_hg():
    print("*** Test HG ***\n")

    hg_path = Path("/run/media/loki/ungesichert/Testdaten/HG")

    for hg in hg_path.glob("HG*_???"):
        _to_asc(hg)

def test_wn():
    print("*** Test WN ***\n")
    wn_path = Path("/run/media/loki/ungesichert/Testdaten/WN")
    wn1 = wn_path / "20221224-2200/WN2212242200_000"
    wn2 = wn_path / "20221226-1300/WN2212261300_000"

    for wn in (wn1, wn2):
        _to_asc(wn, -50.0)

def _to_asc(bin, nodata_value=None):
    nrr = NumpyRadolanReader(bin)  # FileNotFoundError
    nrr.read()

    asc_file = Path(bin.parent, bin.name + ".asc")

    ascii_writer = ASCIIGridWriter(nrr.data, nrr.precision, asc_file, nodata_value)
    ascii_writer.write()

if __name__ == "__main__":
    """ Test ASCII convert """

    #test_hg()
    test_wn()
