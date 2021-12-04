#!/usr/bin/python3

'''
Regnie2CSV
==========
Bereitet eine originale REGNIE-Rasterdatei
zur Verwendung in einem GIS auf.
Erzeugt aus dem originären Raster eine CSV-Datei für den GIS-Input.

Aufruf des Scripts:
-------------------
(python3) Regnie2CSV.py [-a][-j] <Regnie-Rasterfile>
[] = optional
-a: alles, auch Fehlwerte rausschreiben. Führt zu einer großen Ausgabedatei.
-j: eine kleine CSV-Datei schreiben, die nur die Daten und eine ID-Spalte
    enthält. Mittels ID können die Daten mit einem Shapefile kombiniert werden.
-------------------

                        - - -

REGNIE
------
Abspeicherung der Rasterfelder:
zeilenweise von Nord nach Süd und West nach Ost.

Algorithmus:

VON 1 bis (einschl.) 971:
    VON 1 bis (einschl.) 611:
        INTEGER = READ(4 Stellen)

Nichtbesetzte Rasterpunkte sind mit dem Fehlwert -999 besetzt.
Die Dimension der monatlichen und jährlichen Niederschlagshöhen
beträgt mm, die der täglichen mm/10.

Geografischer Bezug:
Die ausgegebenen CSV-Koordinaten beziehen sich auf den Mittelpunkt
der REGNIE-Zelle.

Die Werte der monatlichen und jährlichen Niederschlagshöhen betragen mm,
die der täglichen mm/10.

CSV
---
Nichtbesetzte Rasterpunkte sind mit dem Wert -1 besetzt
(negative Werte treten sonst nicht auf).


erstellt am 29.08.2013, Mario Hafer, Deutscher Wetterdienst (DWD)
update: 17.01.2020
'''

import sys
from pathlib import Path
import gzip
import numpy as np

from Regnie import Regnie


NEWLINE_LEN = 1
"""
Standard 1
Unter Windows erstellte Textfiles (die Rasterdatei) haben idR zwei Zeichen
für einen Zeilenumbruch (\r\n).
Es wurde mit zwei Files getestet, für die allerdings die Linux-Codierung
(1 Zeichen, \n) verwendet wurde.
"""

# REGNIE-Ausdehnung:
Y_MAX = 971
X_MAX = 611



class Regnie2CSV:
    ''' Class '''
    
    
    def __init__(self, regnie_raster_file):
        ''' Constructor '''
        
        self.out("<- '{}'".format(regnie_raster_file))
        
        # Check:
        if not regnie_raster_file:
            raise FileNotFoundError("'regnie_raster_file': empty parameter!")
        
        # string -> Path:
        if isinstance(regnie_raster_file, str):
            regnie_raster_file = Path(regnie_raster_file)
        
        if not regnie_raster_file.exists():
            msg = str(regnie_raster_file)
            if not regnie_raster_file.parent.exists():    # genauerer Hinweis auf das Problem
                msg += ": File-Verzeichnis existiert nicht!"
            raise FileNotFoundError(msg)
        
        # soweit OK, Ausführung beginnen
        
        self._regnie_raster_file = regnie_raster_file
        
        
        # Ermittelt
        
        self._csv_pathname = None
        
        # Programmverhalten
        self._ignore_missings = True      # Kleinere Datei erzeugen, also Fehlwerte überspringen
        # False: alle Werte rausschreiben
        
        """ Integerwerte teilen?
        daily:   ra200107.gz    07.01.2020
        monthly: RASA1912.gz    2019-12
        
        Zehntel nur für Tagesprodukte, daher prüfen, ob 3. Zeichen im Dateinamen
        eine Zahl ist: """
        self._divide = False
        if self._regnie_raster_file.name[2].isdigit():
            self.out("Tagesprodukt erkannt - Werte 1/10")
            self._divide = True
        else:
            self.out("Monats-/Jahresprodukt erkannt")
        
        
        # Vorbereitet zur Koordinatenberechnung - muss nur ein mal berechnet werden:
        self._xdelta_grad = 1.0 /  60.0
        self._ydelta_grad = 1.0 / 120.0
        
        self._prepared_x = ( 6.0 - 10.0 * self._xdelta_grad)
        self._prepared_y = (55.0 + 10.0 * self._ydelta_grad)
        
        
        # Statistics:
        self._max = 0       # the maximum of the field
        self._min = 1000    # the minimum of the field
        self._valid_pixel = 0
        self._non_valid_pixel = 0
        self._total_pixel = 0
        self._mean = None
        
        
    
    def __str__(self):
        return self.__class__.__name__
    
    
    def out(self, s, ok=True):
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)
            
        
    
    def convert(self, join_mode=False, out_dir=None):
        
        self.out("convert(join_mode={}, out_dir='{}')".format(join_mode, out_dir))
        
        
        # Ausgabe-Filenamen erzeugen:
        fn_without_ext = self._regnie_raster_file.stem
        ext = '_join.csv' if join_mode  else '_full.csv'
        new_filename = fn_without_ext + ext
        
        dest_dir = Path(out_dir) if out_dir  else self._regnie_raster_file.parent    # parent = dirname()
        self._csv_pathname = dest_dir / new_filename
        
        
        self._convert_to_csv(join_mode)
        
        
        if not self._csv_pathname.exists():
            self.out("Fehler beim Erstellen der CSV-Datei!", False)
            return
        
        
        self.out("-> {}".format(self._csv_pathname))
        
        self.print_statistics()
        


    
    def _convert_to_csv(self, join_mode):
        """
        join_mode = False (Standard):
        Vollständige CSV-Datei mit Koordinaten, einer ID und den Werten erzeugen
        
        join_mode = True:
        Erstellt eine kleine CSV-Datei, die nur die Daten und eine ID-Spalte
        enthält. Mittels ID können die Daten mit einem Shapefile kombiniert werden.
        """
        csv_missing = -1
        
        rg = Regnie(self._regnie_raster_file)
        array = rg.to_array()
        
        # calculate statistics
        
        # extract only valid cells
        if rg.datatype == "daily":
            arr_valid = np.extract(~np.isnan(array), array)
        elif rg.datatype == "monthly":
            arr_valid = np.extract(array != -999, array)

        self._max = np.max(arr_valid)
        self._min = np.min(arr_valid)
        self._total_pixel = array.size
        self._valid_pixel = arr_valid.size
        self._non_valid_pixel = self._total_pixel - self._valid_pixel
        self._mean = np.mean(arr_valid)

        f_out = self._csv_pathname.open("w")
        
        # Kopfzeile:
        if join_mode:
            print("Erzeuge CSV-Joinfile...")
            f_out.write("ID,VAL\n")
        else:
            f_out.write("LAT,LON,ID,VAL\n")
            
        # iterate over the array and write to CSV
        id = 0
        with np.nditer(array, flags=['multi_index'], order="C") as it:
            for val in it:
                col = it.multi_index[0] + 1
                row = it.multi_index[1] + 1
                id += 1
                
                # handle and convert error values
                if rg.datatype == "daily" and np.isnan(val):
                    val = csv_missing
                elif rg.datatype == "monthly" and val == -999:
                    val = csv_missing
                
                # write csv line
                if join_mode:
                    f_out.write("{},{}\n".format(id, val) )
                else:
                    point = (col, row)
                    lat, lon = self._cartesian_point_to_latlon(point)
                    f_out.write("{:f},{:f},{},{}\n".format(lat, lon, id, val) )
                    
        f_out.close()
    
    def _get_file_object(self):
        if str(self._regnie_raster_file).endswith('.gz'):
            return gzip.open(self._regnie_raster_file)
        
        return open(self._regnie_raster_file)
    
    
    def _cartesian_point_to_latlon(self, cartesian_point_regnie): # y, x
        """ Berechnungsfunktion """
        
        lon = self._prepared_x + (cartesian_point_regnie[1] - 1) * self._xdelta_grad
        lat = self._prepared_y - (cartesian_point_regnie[0] - 1) * self._ydelta_grad
        
        return lat, lon
    
    
    
    def get_statistics(self):
        dim = "rows={}, cols={}".format(Y_MAX, X_MAX)
        return self._regnie_raster_file.name, dim, self._max, self._min, self._mean, \
            self._total_pixel, self._valid_pixel, self._non_valid_pixel
    
    
    def print_statistics(self):
        print("Statistics:")
        print("-----------")
        #filename, dim, _max, _min, mean, total, valid, nonvalid = self.get_statistics()
        filename, dim, _max, _min, mean, total, valid, non_valid = self.get_statistics()
        
        print("File:   ", filename)
        print("Shape:  ", dim)
        print("Maximum:", _max)
        print("Minimum:", _min)
        print("Mean:    {:.1f}".format(mean))
        print("total number of pixels:", total)
        print("Number of valid pixels:", valid)
        print("Number of NaN pixels:  ", non_valid)
    
    
    @property
    def ignore_missings(self):
        return self._ignore_missings
    @ignore_missings.setter
    def ignore_missings(self, b):
        self._ignore_missings = b
        self.out("ignore_missings = {}".format(self._ignore_missings))
        if not b:
            print("  Es wurde angegeben, dass auch nichtbelegte Werte rausgeschrieben werden (Wert -1).")
            print("  Achtung: dies führt zu einer größeren Ausgabedatei.")
    
    @property
    def csv_pathname(self):
        return self._csv_pathname
        
    @property
    def char_period_indicator(self):
        ''' for assigning a suitable QML file '''
        f = self._regnie_raster_file.name    # shorten
        
        # check in this order!
        if f[2].isdigit():
            char = 'd'    # daily, Beispiel: ra200107.gz
        elif f[3].isdigit():    # yearly, RAS6190.JAH, RAS6190.APR.gz
            char = 'y'
        else:
            char = 'm'    # monthly, RASA1908.gz
        
        return char
    
    @property
    def max(self):
        return self._max
    @property
    def min(self):
        return self._min
    @property
    def valid_pixel(self):
        return self._valid_pixel

# ...........................................................



def print_error_exit(msg=None):
    ''' Gibt eine übergebene Meldung aus,
    beschreibt den Aufruf des Programms
    und beendet das Programm. '''
    
    if msg:
        print(msg + "\n")
    
    print("""\
Anwendung des Scripts:
{} [-a][-j] <Regnie-Rasterfile>
[] = optional
-a: alles, auch Fehlwerte rausschreiben. Führt zu einer großen Ausgabedatei.
-j: eine kleine CSV-Datei schreiben, die nur die Daten und eine ID-Spalte enthält.
    Mittels ID-Feld können die Daten mit einem Regnie-Polygon-Shapefile kombiniert werden.
    """.format(Path(__file__).name) )
    sys.exit(1)
    


if __name__ == '__main__':
    """
    Start der Klasse
    """
    
    # Programmverhalten
    ignore_missings = True      # Kleinere Datei erzeugen, also Fehlwerte überspringen
    #ignore_missings = False    # Alle Werte rausschreiben
    """
    Es sind recht viele Fehlwerte in den Regnie-Rastern enthalten; es macht daher
    Sinn, diese Werte zu Gunsten kleinerer Ausgabedateien nicht rauszuschreiben.
    -> etwa 7,5 MB gegenüber 13 MB
    """
    
    
    """
    Argumente:
    argv[0] = Scriptname
    argv[1] = Join-Option oder Regnie-Rasterfile
    argv[2] = nicht belegt oder Regnie-Rasterfile
    """
    if len(sys.argv) < 2:
        print_error_exit()
    
    
    regnie_raster_file = None
    join_mode = False
    
    for arg in sys.argv:
        if arg == "-j":
            join_mode = True
        elif arg == "-a":
            ignore_missings = False
        else:
            regnie_raster_file = Path(arg)
    
    
    
    regnie_converter = Regnie2CSV(regnie_raster_file)    # FileNotFoundException
    regnie_converter.ignore_missings = ignore_missings
    regnie_converter.convert(join_mode)
    
    
    
