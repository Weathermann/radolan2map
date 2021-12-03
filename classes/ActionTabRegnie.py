"""
ActionTabRegnie

Separate __actions__ of REGNIE operations from the other components

Created on 01.12.2020
@author: Weatherman
"""

import os
from pathlib import Path

from qgis.PyQt.QtWidgets import QFileDialog

# own classes:
from ActionTabBase  import ActionTabBase         # base class
from Regnie2CSV     import Regnie2CSV
from LayerLoader    import LayerLoader
import regnie2raster as r2r



class ActionTabRegnie(ActionTabBase):
    '''
    classdocs
    '''
    
    
    def __init__(self, iface, model, dock):
        '''
        Constructor
        '''
        
        super().__init__(iface, model, dock)
        
        
        self.dock.btn_select_regnie.clicked.connect(self._select_regnie_file)
        self.dock.btn_load_regnie.clicked.connect(self._run)
        
        
    
    
    """
    Actions
    """
    
    def _select_regnie_file(self):
        text = self.regnie_file
        start_dir = Path(text).parent if text  else Path.home()
        
        # after title string: start path, file_filter
        regnie_file, _ = QFileDialog.getOpenFileName(self.dock, "Please select a REGNIE file",
                                                       str(start_dir), None,
        # these additional parameters are used, because QFileDialog otherwise doesn't start with the given path:
                                                       None, QFileDialog.DontUseNativeDialog)
        if not regnie_file:
            return    # keep path anyway
        
        self.regnie_file = regnie_file    # -> enable button
        
    
    
    
    def _run(self):
        self.out("_run()")
        
        # shorten:
        regnie_file = self.regnie_file
        dock = self.dock
        
        # field was leaved empty
        if not regnie_file:
            super()._show_critical_message_box("REGNIE input file wasn't specified!")
            dock.btn_load_regnie.setEnabled(False)
            return
        
        
        regnie_file = Path(regnie_file)
        
        if not regnie_file.exists():
            super()._show_critical_message_box(f"File\n'{regnie_file}'\nnot found!")
            dock.btn_load_regnie.setEnabled(False)
            return
        
        
        self._model.set_data_dir('regnie')
        data_dir = self._model.data_dir
        
        try:  # include everything that can raise exceptions
            try:
                self._model.create_storage_folder_structure()
                self.out(f"create data dir for converted REGNIE: '{data_dir}'")
            except FileExistsError:
                pass
            
            
            regnie_csv_file, char_period_indicator, t_statictics = \
                self.__convert_regnie_raster2csv(regnie_file, data_dir)
            
            '''
            LAT,LON,ID,VAL
            55.058333,8.383333,1,7
            55.058333,8.400000,2,7
            '''

            show_csv = True
            # but CSV is only displayed in case of errors (fallback) because raster format is better
            # but True is better here because of exception handling (set False at one place)
            
            # convert to raster
            # TODO: assumes the file has already been decompressed from gz!

            self.out("Starting REGNIE to raster conversion...")
            regnie_raster_file = data_dir / f"{regnie_file.name}.tif"

            try:
                r2r.regnie2raster(regnie_file, str(regnie_raster_file))
            # Exceptions,
            # but nevertheless load the CSV file:
            except ModuleNotFoundError as e:
                """ Under Linux a "ModuleNotFoundError: No module named '_gdal'"
                error can occur. """
                msg = f"Exception: {e}:\nPossibly a GDAL installation error on Linux(?)"
                regnie_raster_file = "/run/media/loki/ungesichert/Testdaten/REGNIE/raster/RASA1908.tif"    # for testing
                super()._show_critical_message_box(msg, 'REGNIE raster conversion error')
                self.out(f"{msg}\nload REGNIE test raster file: {regnie_raster_file}", False)
            except Exception as e:
                msg = f"Exception: {e}"
                self.out(f"{msg}")
                super()._show_critical_message_box(msg, 'REGNIE raster conversion error')
            else:
                self.out(f"Successfully created REGNIE raster file {regnie_raster_file}!")
                show_csv = False
            
        except Exception as e:
            msg = f"{e}, wrong format!"
            super()._show_critical_message_box(msg, 'Layer loading error')  # disable here, because it was only set a folder
            dock.btn_load_regnie.setEnabled(False)
            # Reset - don't save the wrong data for the next run!:
            #dock.text_regnie.clear()
            #self.regnie_file = str(regnie_file.parent)    # nevertheless save last path for next suggestion
            return
        
        
        """
        Add the layers ...
        """

        # Determine prepared QML-File delivered with the plugin:
        self.out(f"char period indicator = '{char_period_indicator}'")

        d_regnie_qml = {
            'd': ("regnie_raster_daily.qml", 'regnie_daily.qml'),
            'm': ("regnie_raster_monthly.qml", 'regnie_monthly.qml'),
            'y': ("regnie_raster_yearly.qml", 'regnie_yearly.qml'),
        }

        ll = LayerLoader(self._iface)  # 'iface' is from 'radolan2map'

        # load the regnie raster file
        qml_file = self._model.symbology_path / d_regnie_qml[char_period_indicator][0]
        ll.load_raster(regnie_raster_file, qml_file)

        if show_csv:
            # load the CSV file
            qml_file = self._model.symbology_path / d_regnie_qml[char_period_indicator][1]
            ll.load_vector(regnie_csv_file, qml_file)    # incompatible with Path()!

        
        filename, dim, _max, _min, mean, total, valid, non_valid = t_statictics
        filename = filename.replace('.gz', '')    # maybe 'RASA1908.gz'
        
        dock.text_filename.setText(filename)
        dock.text_shape.setText(dim)
        dock.text_max.setText(str(_max))
        dock.text_min.setText(str(_min))
        dock.text_mean.setText(f"{mean:.1f}")
        dock.text_total_pixels.setText(str(total))
        dock.text_valid_pixels.setText(str(valid))
        dock.text_nonvalid_pixels.setText(str(non_valid))
        
        super()._enable_and_show_statistics_tab()
        super()._finish()
    
    
    
    def __convert_regnie_raster2csv(self, regnie_raster_file, data_dir):
        '''
        - separate the usage of the REGNIE-Class
        - Pass exceptions to caller
        
        can raise Exception
        '''
        
        self.out(f"__convert_regnie_raster2csv('{regnie_raster_file}')")
        
        
        regnie_converter = Regnie2CSV(regnie_raster_file)
        """
        There are quite a few missing values in the Regnie grid; it therefore makes sense
        not to write these values out in favor of smaller output files.
        -> about 7.5 MB compared to 13 MB
        """
        regnie_converter.ignore_missings = True
        regnie_converter.convert(out_dir=data_dir)
        
        t_statictics = regnie_converter.get_statistics()
        
        return regnie_converter.csv_pathname, regnie_converter.char_period_indicator, t_statictics
        

    
    # ......................................................................
    
    
    # for saving:
    
    @property
    def regnie_file(self):
        return self.dock.text_regnie.text()
    @regnie_file.setter
    def regnie_file(self, f):
        self.dock.text_regnie.setText(f)
        # after folder selection enable load button:
        self.dock.btn_load_regnie.setEnabled(True)
    
    
