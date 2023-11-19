from pathlib import Path

from qgis.core           import Qgis, QgsProject, QgsPrintLayout, QgsReadWriteContext, QgsLayerDefinition
from qgis.PyQt.QtCore    import QSettings
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QAction

# own classes:
from .ActionTabBase      import ActionTabBase         # base class
from .NumpyRadolanReader import NumpyRadolanReader    # Input: read RADOLAN binary file
from .ASCIIGridWriter    import ASCIIGridWriter       # Output 1: write ESRI ASCII Grid
from .GDALProcessing     import GDALProcessing        # Output 2: write GeoTIFF
#from .Model import test_product_get_id    # import a function
from .LayerLoader        import LayerLoader



class ActionTabRADOLANLoader(ActionTabBase):
    """
    ActionTabRADOLANLoader

    Separate __actions__ of RADOLAN binary loading operations from the other components

    Created on 13.12.2020
    @author: Weatherman
    """
    
    
    def __init__(self, iface, model, dock):
        
        super().__init__(iface, model, dock)

        """
        set connections
        """
        
        # Button for loading a prepared template project:
        dock.btn_load_project.clicked.connect(self._ask_user_load_template_project)
        # use button for easy test of PrintLayout:
        #dock.btn_load_project.clicked.connect(self._load_print_layout )    # !: function without ()
        dock.btn_load_radars.clicked.connect(self._load_radarnetwork_layer)
        dock.filedialog_input.clicked.connect(self._select_input_file)
        dock.filedialog_mask.clicked.connect(self._select_mask)
        dock.filedialog_qml.clicked.connect(self._select_symbology)
        # connect accept and cancel:
        #dock.button_box.accepted.connect(self._run)
        # For Apply-Button you'll need to connect the clicked signal manually in your widget:
        #apply_btn = dock.button_box.button(QDialogButtonBox.Apply)
        #apply_btn.clicked.connect(self._run)
        dock.btn_action.clicked.connect(self._run)
        

        combo = dock.cbbox_radolan    # shorten
        
        # read previously used files and prefill combo box for the user:
        history_file = model.history_file
        if history_file.exists():
            self.out(f"reading 'history file' {history_file}")
            with history_file.open() as hf:
                model.list_of_used_files = hf.read().splitlines()    # lines without '\n'
                # hint: 'list_of_used_files' will be used further
            # fill:
            combo.addItem('')    # first a empty item (no valid selection)
            for file in model.list_of_used_files:    # first items in the file also positioned first in list
                combo.addItem(file)
        # history file
        
        # Register event handler only here, so it is not triggered at filling above:
        combo.currentIndexChanged.connect(self._combo_selection_change)
        

        # set up later
        self.mask_file = model.default_border_shape    # default: "DEU_adm0"
        self._qml_file = None
        
    
    
    
    def _ask_user_load_template_project(self):
        reply = QMessageBox.question(self._iface.mainWindow(), 'Continue?',
                 'Do you want to load template project?', QMessageBox.Yes, QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        
        """
        Related to Windows / QGIS 3.10
        Phenomenon: after loading the template project,
        QGIS map canvas 'jumps outside' the layer extents, even though the template project
        was saved with map centered to Germany.
        So one idea was to center on the german border shapefile after that (code below) but
        this hasn't worked.
        With the modification of the QSettings below the behaviour is OK now.
        """
        
        '''
        if platform.system() == 'Windows':
            # necessary?
            canvas = self._iface.mapCanvas()
            canvas.mapSettings().setDestinationCrs(QgsCoordinateReferenceSystem(3035))
            
            # Center on German border shape:
            vlayer_de_border = QgsVectorLayer(self._model.default_border_shape, 'de_border', 'ogr')
            #print("isValid:", vlayer_de_border.isValid())
            extent = vlayer_de_border.extent()
            canvas.setExtent(extent)
            canvas.refresh()
        '''
        
        """
        The following was related to CRS prompting, when loading a new layer,
        but it seems to fix the problem described above:
        "... Alternatively, you can also set up QGIS so that newly added layers use
        - the project's CRS
        - or a default CRS (in Settings/Options/CRS/Crs for new layers)
        
        You can also set those properties via the pyQGIS API
        QSettings().setValue('/Projections/defaultBehavior', 'useProject')  # Use project's crs
        or
        QSettings().setValue('/Projections/defaultBehavior', 'useGlobal')  # Use default crs
        QSettings().setValue('Projections/layerDefaultCrs', 'EPSG:4326')
        
        Note that the default value for '/Projections/defaultBehavior' is 'prompt' "
        
        https://gis.stackexchange.com/questions/288400/creating-a-memory-layer-without-the-crs-dialog-in-pyqgis-3/313872
        https://gis.stackexchange.com/questions/27745/how-can-i-specify-the-crs-of-a-raster-layer-in-pyqgis/27765#27765
        
        How does this work?
        An attempt to explain: by setting up in that way, that new layers follow the project crs,
        layers like german borders in WGS automatically follow the project crs (EPSG:3035) which
        is coded in the project template file on the one hand and additionally set up with crs externally.
        """
        settings = QSettings()
        #saved_setting = settings.value("/Projections/defaultBehavior")
        settings.setValue("/Projections/defaultBehavior", 'useProject')    # use project's crs
        
        
        self._model.create_default_project()
        
        # Show hint:
        msg = "Please save project immediately with a new name,\nnot to overwrite the template!"
        QMessageBox.warning(self._iface.mainWindow(), 'Save as new project', msg)
        
        # trigger the Project Save As menu button.
        self._iface.mainWindow().findChild( QAction, 'mActionSaveProjectAs' ).trigger()

    
    def _load_radarnetwork_layer(self):
        """ load DWDs radar network consisting of two layers (points and buffer)
        by QgsLayerDefinition file """

        layergroup_name = "RadarNetwork"

        root = QgsProject.instance().layerTreeRoot()
        
        """
        Check/uncheck radar network group layer if existing
        """
        
        # find group layers:
        '''
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == layergroup_name:
                self.out("LayerGroup '{}' already exists.".format(layergroup_name), False)
                return
        ''' # is OK, it works
        # simpler method:
        group = root.findGroup(layergroup_name)
        if group:
            #self.out("LayerGroup '{}' already exists.".format(layergroup_name), False)
            state = group.isVisible()
            group.setItemVisibilityChecked(not state)
            return
        
        
        """
        Create radar network group layer
        """
        
        layer_def_file = self._model.plugin_dir / "example/shapes/RadarNetwork/dwd_radarnetwork.qlr"
        
        if not layer_def_file.exists():
            self.out(f"layer definition file '{layer_def_file}' doesn't exist.", False)
            return
        
        """ OK for buffer layer only:
        shp = self._model.plugin_dir / "example/shapes/RadarNetwork/radarbuffer_150km.gpkg"
        vlayer_radar = QgsVectorLayer(str(shp), 'radar_buffer', 'ogr')
        #print("isValid:", vlayer_radar.isValid())
        #crs_radolan = QgsCoordinateReferenceSystem()
        #crs_radolan.createFromProj4(self._model.projection_radolan)
        #vlayer_radar.setCrs(crs_radolan)
        QgsProject.instance().addMapLayer(vlayer_radar)
        """
        
        #group = root.addGroup("RadarNetwork")    # ok, appended
        group = root.insertGroup(0, layergroup_name)    # first position
        self.out(f"loading layer definition file '{layer_def_file}'")
        QgsLayerDefinition().loadLayerDefinition(str(layer_def_file), QgsProject.instance(), group)
        

    def _select_input_file(self):
        combo = self.dock.cbbox_radolan    # shorten
        
        # Determine start directory:
        text = combo.currentText()
        if text:
            start_dir = str( Path(text).parent )
        else:
            start_dir = str(Path.home())
        
        """
        raa01-rw_10000-1708020250-dwd---bin
        raa01-rw_10000-1708020250-dwd---bin.gz
        adjust.pix """
        # You can also add other filter. You need to separate them with a double ;; like so:
        # "Images (*.png *.xpm .jpg);;Text files (.txt);;XML files (*.xml)"
        l_common_ext = "*bin* *.pix *_??? *_???.bz2"
        file_filter = f"RADOLAN binary format ({l_common_ext});;Unknown product format (*)"
        
        input_file = self._show_open_file_dialog("Input binary RADOLAN file", start_dir, file_filter)
        
        if not input_file:
            return    # preserve evtl. filled line
        
        # Set:
        
        #self.dock.inputpath.setText(input_file)
        
        """ Set selection to first (just inserted) position.
        This triggers the change event listener which is then executed twice.
        So we block the emitting of a signal during index change: """
        combo.blockSignals(True)
        combo.insertItem(0, input_file)    #combo.addItem(input_file)    # addItem simplest method
        combo.blockSignals(False)
        combo.setCurrentIndex(0)    # trigger if there is a real selection change (more than one element)
        
        # If one element now, the event listener was not triggered,
        # because there is no selection change. We trigger manually:
        if combo.count() == 1:
            self._combo_selection_change()
        

    def _combo_selection_change(self):
        #file = self.dock.inputpath.text()
        file = self.dock.cbbox_radolan.currentText()
        self.out(f"selection changed: '{file}'")
        
        #
        # Check input file:
        #
        
        action_btn = self.dock.btn_action    # shorten
        
        if not file:
            print("  empty entry ignored")
            action_btn.setEnabled(False)
            return
        
        if not Path(file).exists():
            super()._show_critical_message_box("The specified file doesn't exist!", 'File error')
            try:
                self._model.list_of_used_files.remove(file)
            except ValueError:
                self.out("catched ValueError", False)
                pass

            self.out(f"file '{file}' removed from list")
            action_btn.setEnabled(False)
            return
        
        # so far OK, enable action
        
        # Test product, if it is a 'X'-product (RX, WX, EX) with values coded as RVP6-units:
        try:
            nrr = NumpyRadolanReader(file)  # FileNotFoundError
        except (FileNotFoundError, IOError):
            raise

        nrr._read_radolan_composite(loaddata=False)    # only read the metadata
        prod_id = nrr.prod_id
        
        is_rx = True if prod_id[1] == 'X'  else False
        """ Further string tests on product id don't make sense,
        because IDs like 'W1'-'W4', 'D2'-'D3', 'S2'-'S3' are possible. """
        
        if is_rx:
            self.out(f"*X product detected - '{self.dock.check_rvp6tomm.objectName()}' checkbox enabled")
        self.dock.check_rvp6tomm.setVisible(is_rx)
        
        # Print info found in def-file about the product:
        prod_desc = self._model.product_description(prod_id)
        self.out(f'product {prod_id}: "{prod_desc}"')
        
        #self.dock.btn_show_list.setVisible(True)
        # after selection of RADOLAN file enable action button:
        action_btn.setEnabled(True)
        

    def _select_mask(self):
        # Determine start directory:
        text = self.dock.inputmask.text()
        if text:
            start_dir = Path(text).parent
        else:
            start_dir = Path.home()

        # parent, caption, directory, file_filter
        inputmaskshp = self._show_open_file_dialog("Select mask (optional)",
                            str(start_dir), "Shape file (*.shp)")
        if not inputmaskshp:
            return    # don't delete possibly loaded path
        
        self.mask_file = inputmaskshp
    

    def _select_symbology(self):
        file_filter = "QGIS symbology files (*.qml*)"
        
        qml_file = self._show_open_file_dialog("Apply symbology (optional)",
                   str(self._model.symbology_path), file_filter)
        if not qml_file:
            return    # keep path anyway
        
        self.qml_file = qml_file
        

    def _show_open_file_dialog(self, title, path, file_filter):
        selection, _ = QFileDialog.getOpenFileName(self.dock, title, path, file_filter,
        # these additional parameters are used, because QFileDialog otherwise doesn't start with the given path:
            None, QFileDialog.DontUseNativeDialog)
        return selection    # can be None
    

    def _run(self):
        """
        Run method that performs all the real work.
        """
        
        model = self._model    # shorten

        radolan_file = self.dock.cbbox_radolan.currentText()
        
        # File exists (checked before) - so it can be already stored for later suggestion for the user:

        # Try to remove _this_ file (if contains), so it can be new positioned at the top:
        try:
            model.list_of_used_files.remove(radolan_file)
        except ValueError:
            pass
        
        model.list_of_used_files.insert(0, radolan_file)
        

        clip_to_mask = False
        
        # Checkbox enabled AND mask shape specified?
        if self.dock.check_cut.isChecked()  and  self.mask_file:
            clip_to_mask = True
            #sep = '\\' if platform.system() == 'Windows'  else '/'
            #shapefile = shapefile.replace(sep, os.sep)
            
            # if the use of mask file will be relevant, check it
            if not Path(self.mask_file).exists():
                super()._show_critical_message_box("The specified mask file doesn't exist!", 'File error')
                return

        # + + + + + + + + + + + + + + + +
        
        # evtl. Exception (from NumpyRadolanReader)
        try:
            nrr, asc_filename_path = self.__read_radolan_create_ascii_file(radolan_file)
        except Exception as e:    # catch everything
            super()._show_critical_message_box(str(e), 'Problem reading RADOLAN bin file occured')
            return
        
        # + + + + + + + + + + + + + + + +

        # bring some order in possible radar data types (finished .tif will be saved there):
        if nrr.is_radklim:
            subdir_name = 'radklim'
        elif nrr.is_polara:
            subdir_name = 'polara'
        else:
            subdir_name = 'radolan'
        
        model.set_data_dir(subdir_name)
        model.create_storage_folder_structure()    # no cleaning temp, so we can check the temp result after running
        
        # define name of (clipped) TIFF file (based on .asc filename):
        tif_extension = '_clipped.tif' if clip_to_mask  else '.tif'
        tif_bn = asc_filename_path.name.replace(".asc", tif_extension)    # tif basename

        full_tif_filename = model.data_dir / tif_bn


        # Clip to the given mask (optional):
        shape_file = self.mask_file
        if not clip_to_mask:
            shape_file = None

        prj_src = self._model.projection_polara_wgs if nrr.is_polara else self._model.projection_radolan

        # at GDAL processing a lot of strange errors are possible - with projection parameters and GDAL versions...
        try:
            self.__create_tif_file(asc_filename_path, full_tif_filename, prj_src, shape_file)
        except Exception as e:
            super()._show_critical_message_box(str(e), 'GDAL processing error')
            return
        
        """
        From here is related to GIS layer loading
        """
        
        """
        If no project file not loaded when running plugin
        """
        
        super()._check_create_project()
        
        # Set symbology from QML file:
        # 1) as given parameter by user or
        # 2) automatically by program
        qml_file = None
        
        # self defined symbology:
        if self.dock.check_symb.isChecked():
            qml_file = self.qml_file
            if not qml_file:    # empty field (string)?
                self.out("QML field = emtpy - choose one automatically", False)
        
        # Determine prepared QML file delivered with the plugin:
        if not qml_file:
            # check now, if special product - product in RVP6 units:
            if nrr.prod_id[1] == 'X'  and  not nrr.rx_in_mm:    # if values still in RVP6 units
                interval = -1
            else:
                interval = nrr.interval    # default
            # if else

            prod_id = nrr.prod_id if nrr.is_polara else None  # use special QML for "HG"/"WN" composite

            qml_file = model.qml_file(interval, prod_id)
        # if not qml
        
        
        ll = LayerLoader(self._iface)    # 'iface' is from 'radolan2map'
        
        if self.dock.check_excl_zeroes.isChecked():
            ll.no_zeros = True    # Set 0 values to NODATA (= transparent)
        
        ll.load_raster(full_tif_filename, qml_file, temporal=True)
        
        
        #self.dock.button_box.button(QDialogButtonBox.Apply).setEnabled(False)
        #self.dock.btn_action.setEnabled(False)    # action was performed
        # -> better not, when user modify some options and wants to perform the same work again...
        
        # Close dock and perform work:
        #self.dock.close()
        # !!! Close dock at the end, otherwise the isVisible() method on elements will return
        # False because the visibility of the parent element is also relevant !!!
        
        super()._finish()
        
        super()._load_print_layout(ll.layer_name, nrr.prod_id, nrr.datetime)
        
        
    
    
    def __read_radolan_create_ascii_file(self, radolan_file):
        """ raise Exception """
        
        self.out(f"__read_radolan_create_ascii_file('{radolan_file}')")
        
        
        self._model.create_storage_folder_structure(use_temp_dir=True)    # only create tmp_dir
        
        #exclude_zeroes = self.dock.check_excl_zeroes.isChecked()
        #self._ascii_converter = RadolanBin2AsciiConverter(input_file, model.temp_dir, exclude_zeroes)
        # -> now better with layer renderer - conserves 0 values
        
        # init. reader:
        nrr = NumpyRadolanReader(radolan_file)    # FileNotFoundError
        #nrr.exclude_zeroes = exclude_zeroes
        
        # RX to mm?
        if self.dock.check_rvp6tomm.isVisible()  and  self.dock.check_rvp6tomm.isChecked():
            nrr.rx_in_mm = True
        
        """
        Read bin file
        """
        nrr.read()    # Exception
        
        
        """
        set info
        """
        filename, dim, _max, _min, mean, total, valid, nonvalid = nrr.get_statistics()
        s_max = str(_max)
        if _max is not None:  # 'HG'-product
            # if part after point is too long:
            l_max = s_max.split('.')
            if len(l_max[1]) > 2:
                s_max = f"{_max:.2f}"
        if mean is not None:  # 'HG'-product
            mean = f"{mean:.2f}"

        self.dock.text_filename.setText(filename)
        self.dock.text_shape.setText(dim)
        self.dock.text_max.setText(s_max)
        self.dock.text_min.setText(str(_min))
        self.dock.text_mean.setText(mean)
        self.dock.text_total_pixels.setText(str(total))
        self.dock.text_valid_pixels.setText(str(valid))
        self.dock.text_nonvalid_pixels.setText(str(nonvalid))
        
        super()._enable_and_show_statistics_tab()
        

        """
        create ASCII file
        """
        asc_file_bn = nrr.simple_name + ".asc"
        asc_filename_path = self._model.temp_dir / asc_file_bn    # produced in temp. dir

        # needed for adjusted NODATA value (-1 isn't suitable for negative dBZ):
        nodata_value = -50.0 if nrr.is_dbz else None

        ascii_writer = ASCIIGridWriter(nrr.data, nrr.precision, asc_filename_path, nodata_value)
        ascii_writer.write()

        return nrr, asc_filename_path
    

    def __create_tif_file(self, asc_file, tif_file, prj_src, shape_file=None):
        """ Parameters for 'GDALProcessing'
        raise Exception """

        index = self.dock.cbbox_projections.currentIndex()
        prj_dest = self._model.projections[index]
        
        gdal_processing = GDALProcessing(self._model, asc_file, tif_file)
        #gdal_processing.produce_warped_tif_using_script()
        
        # at GDAL processing a lot of strange errors are possible - with projection parameters and GDAL versions...
        gdal_processing.produce_warped_tif_by_python_gdal(prj_src, prj_dest, shape_file)
        

    # .........................................................

    @property
    def mask_file(self):
        return self._mask_file
    @mask_file.setter
    def mask_file(self, f):
        self._mask_file = f
        self.dock.inputmask.setText(f)
    
    @property
    def qml_file(self):
        return self._qml_file
    @qml_file.setter
    def qml_file(self, f):
        self._qml_file = f
        self.dock.inputqml.setText(f)
