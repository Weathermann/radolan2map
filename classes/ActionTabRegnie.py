"""
ActionTabRegnie

Separate __actions__ of REGNIE operations from the other components

Created on 01.12.2020
@author: Weatherman
"""
from pathlib import Path

from qgis.PyQt.QtWidgets import QFileDialog

# own classes:
from .ActionTabBase  import ActionTabBase         # base class
from .LayerLoader    import LayerLoader
from .Regnie         import Regnie
from . import regnie2raster as r2r

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
                
            # instantiate a Regnie class instance
            rg = Regnie(regnie_file)
            self.out(f"Detected REGNIE datatype: {rg.datatype}")
            
            # convert to raster
            self.out("Starting REGNIE to raster conversion...")
            regnie_raster_file = data_dir / f"{regnie_file.name.replace('.gz', '')}.tif"
            try:
                #TODO: this currently reads the REGNIE file a second time
                r2r.regnie2raster(regnie_file, regnie_raster_file)
            except ModuleNotFoundError as e:
                """ Under Linux a "ModuleNotFoundError: No module named '_gdal'"
                error can occur. """
                msg = f"Exception: {e}:\nPossibly a GDAL installation error on Linux(?)"
                self.out(f"{msg}")
                super()._show_critical_message_box(msg, 'REGNIE raster conversion error')
                return
            except Exception as e:
                msg = f"Exception: {e}"
                self.out(f"{msg}")
                super()._show_critical_message_box(msg, 'REGNIE raster conversion error')
                return
            
            self.out(f"Successfully created REGNIE raster file {regnie_raster_file}!")
            
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
        d_regnie_qml = {
            'daily': "regnie_raster_daily.qml",
            'monthly': "regnie_raster_monthly.qml",
            'multiannual': "regnie_raster_yearly.qml",
        }

        ll = LayerLoader(self._iface)  # 'iface' is from 'radolan2map'

        # load the regnie raster file
        qml_file = self._model.symbology_path / d_regnie_qml[rg.datatype]
        ll.load_raster(regnie_raster_file, qml_file)

        # fill statistics output
        stats = rg.statistics
        dock.text_filename.setText(regnie_file.name.replace(".gz", ""))
        dock.text_shape.setText(f"{rg.data.shape}")
        dock.text_max.setText(f"{stats['max']:.1f}")
        dock.text_min.setText(f"{stats['min']:.1f}")
        dock.text_mean.setText(f"{stats['mean']:.1f}")
        dock.text_total_pixels.setText(f"{stats['total_pixels']}")
        dock.text_valid_pixels.setText(f"{stats['valid_pixels']}")
        dock.text_nonvalid_pixels.setText(f"{stats['non_valid_pixels']}")
        
        super()._enable_and_show_statistics_tab()
        super()._finish()
    
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
    
    
