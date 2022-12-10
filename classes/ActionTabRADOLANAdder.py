'''
ActionTabRADOLANAdder

Separate __actions__ of RADOLAN summation operations from the other components

Created on 02.12.2020
@author: Weatherman
'''

from pathlib import Path
from copy import copy
from datetime import datetime
import re

from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore    import QDateTime

# own classes:
from ActionTabBase      import ActionTabBase         # base class
from NumpyRadolanAdder  import NumpyRadolanAdder
from GDALProcessing     import GDALProcessing
from LayerLoader        import LayerLoader

"""
The format of date and datetime is different from the format of QDate and QDateTime,
you should not use % in the Qt format!
"""
df_dt = '%Y-%m-%d %H:%M'
df_qt = 'yyyy-MM-dd hh:mm'


class ActionTabRADOLANAdder(ActionTabBase):
    """
    classdocs
    """
    
    
    def __init__(self, iface, model, dock):
        """
        Constructor
        """
        
        super().__init__(iface, model, dock)
        
        
        # Listener
        dock.btn_select_dir_adder.clicked.connect(self._select_input_dir)
        dock.btn_scan.clicked.connect(self._scan_for_products)
        dock.btn_run_adder.clicked.connect(self._run)
        dock.btn_set_datetime.clicked.connect(self._set_begin_end_automatically)
        dock.listWidget.itemSelectionChanged.connect(self._listwidget_selection_changed)    # itemClicked.connect
        
        
        # setting date time 
        dt = QDateTime.currentDateTime()
        self.dock.dateTimeEdit_beg.setDateTime(dt)
        self.dock.dateTimeEdit_end.setDateTime(copy(dt))
        
        self._prod_id = None
        self._files = None    # list of scanned RADOLAN files

        # for saving:
        self._begin = None
        self._end   = None
        self._last_dir = None
        
    
    
    
    """
    Actions
    """
    
    
    def _select_input_dir(self):
        text = self.tf_path
        self._last_dir = text if text  else str(Path.home())
        
        # parent, caption, directory, file_filter
        selected_dir = QFileDialog.getExistingDirectory(self.dock, 'Select RADOLAN directory', self._last_dir,
                        # these additional parameters are used, because QFileDialog otherwise doesn't start with the given path:
                        QFileDialog.DontUseNativeDialog)
        
        if not selected_dir:
            return    # preserve possibly filled line
        
        self.tf_path = selected_dir
        
        # automatically scan for products
        self._scan_for_products()
        # but therefore disable the manual scan button:
        self.dock.btn_scan.setEnabled(False)
    
    
    
    def _scan_for_products(self):
        self.out("_scan_for_products()")
        
        # an error could occur or user needs to select an item (found product) first
        self.dock.btn_run_adder.setEnabled(False)
        
        lwidget = self.dock.listWidget    # shorten
        lwidget.clear()
        
        scan_path = Path(self.tf_path)
        print(f"  scan path: '{scan_path}'")

        try:
            files = scan_path.glob('raa01-*---bin*')     # possibly '.gz'
            if not files:
                self.dock.btn_set_datetime.setEnabled(False)
                raise FileNotFoundError("No RADOLAN products found!")
        except Exception as e:
            super()._show_critical_message_box(str(e))
            return

        # set:
        self._files = list(files)    # save list of Posixpath because of generator running o.o.i.
        # sort because order of RADOLAN first and last file for setting datetime:
        self._files.sort()

        self.dock.btn_set_datetime.setEnabled(True)


        # Detect product IDs and count:

        d_id = {}  # dict of product ids
        # raa01-sf_10000-1501070550-dwd---bin -> 'SF'
        for f in self._files:    # of Posixpath
            _id = f.name[6:8].upper()

            if _id[1] == 'X':  # exclude RVP-products (1 Byte) like 'RX', 'WX', 'EX', ...
                print(f"- exclude '{_id}'")
                continue

            try:  # if key exist, increment
                d_id[_id] += 1
            except KeyError:
                d_id[_id] = 1
        # for files

        l_id = []  # list of product ids
        for k, v in d_id.items():
            print(f"{k}: {v}")
            if v > 1:
                l_id.append(k)
        # for
        
        self.out(f"IDs: {l_id}")
        
        for i in l_id:
            lwidget.addItem(i)
        
        # again, because '_listwidget_selection_changed()' enables 'btn_run_adder':
        self.dock.btn_run_adder.setEnabled(False)


    def _set_begin_end_automatically(self):
        if not self._files:
            raise FileNotFoundError("No RADOLAN products in list!")

        first_file = self._files[0].name
        last_file  = self._files[-1].name

        # RADOLAN: ['01', '10000', '1605290050']
        # RADKLIM: ['01', '2017', '002', '10000', '1806010050']
        digits_begin = re.findall(r'\d+', first_file)[-1]
        digits_end   = re.findall(r'\d+', last_file)[-1]

        # save this. These are the settings with which the user executed:
        self._begin = "20" + digits_begin
        self._end   = "20" + digits_end

        df = '%Y%m%d%H%M'
        dt_beg = datetime.strptime(self._begin, df)
        dt_end = datetime.strptime(self._end, df)
        print("Begin:", dt_beg)
        print("End:  ", dt_end)

        self.dock.dateTimeEdit_beg.setDateTime(dt_beg)
        self.dock.dateTimeEdit_end.setDateTime(dt_end)

        self.dock.btn_set_datetime.setEnabled(False)


    
    def _listwidget_selection_changed(self):
        self.dock.btn_run_adder.setEnabled(True)
        
        item = self.dock.listWidget.currentItem().text()
        #print(item)
        
        self._prod_id = item
        
        self.__setup_suitable_datetime_for_selected_product(item)

        
    
    def __setup_suitable_datetime_for_selected_product(self, prod_id):
        # self.dock.dateTimeEdit_beg.dateTime()): PyQt5.QtCore.QDateTime(2020, 12, 3, 20, 40, 56, 553)
        #df = "dd.MM.yyyy HH:mm"
        #print("Beginn:", self.dock.dateTimeEdit_beg.dateTime().toString(df))
        #print("Ende:  ", self.dock.dateTimeEdit_end.dateTime().toString(df))
        #print(prod_id)
        
        # QDateTime -> datetime and smooth date:
        dt_beg = self.dock.dateTimeEdit_beg.dateTime().toPyDateTime()
        
        # assume hourly product:
        set_min = 50
        
        # 5 minute product: 'RZ', 'RY', 'YW', 'EZ', 'EY'
        if prod_id[1] == 'Y'  or  prod_id[1] == 'Z'  or  prod_id == 'YW':
            # simple defaults:
            if dt_beg.minute > 31:
                set_min = 45
            elif dt_beg.minute < 30:
                set_min = 0
            else: # 30
                set_min = dt_beg.minute
        # if
        
        dt_new = dt_beg.replace(minute=set_min, second=0, microsecond=0)
        
        self.begin = dt_new.strftime(df_dt)
        
    
    
    
    def _run(self):
        self.out("_run()")
        
        dock = self.dock    # shorten

        #
        # Checks
        #

        # Checkbox enabled AND mask shape specified?
        mask_file = dock.inputmask.text()
        if dock.check_cut.isChecked():
            # if the use of mask file will be relevant, check it
            if not Path(mask_file).exists():
                super()._show_critical_message_box("The specified mask file doesn't exist!", 'File error')
                return
        else:
            mask_file = None


        dock.btn_run_adder.setEnabled(False)    # disable run button during operation
        
        # QDateTime -> datetime and smooth date:
        dt_beg = dock.dateTimeEdit_beg.dateTime().toPyDateTime()
        dt_end = dock.dateTimeEdit_end.dateTime().toPyDateTime()
        
        # save this. These are the settings with which the user executed:
        self._begin = dt_beg.strftime(df_dt)
        self._end   = dt_end.strftime(df_dt)
        #print("Begin:", dt_beg)
        #print("End:  ", dt_end)
        
        
        # Try to catch every Exception and show it in a graphical window.
        
        df = '%Y%m%d%H%M'
        fn = f"{self._prod_id}_{dt_beg.strftime(df)}-{dt_end.strftime(df)}.asc"
        asc_filename_path = self._model.temp_dir / fn
        
        
        try:
            # no cleaning temp, so we can check the temp result after running:
            self._model.create_storage_folder_structure(temp_dir=True)
            
            adder = NumpyRadolanAdder(dt_beg, dt_end, self.tf_path, self._prod_id, asc_filename_path)
            adder.run()
            
        except Exception as e:
            super()._show_critical_message_box(str(e))
            return
        
        
        
        """
        From here is related to GIS layer loading
        """
        
        # at GDAL processing a lot of strange errors are possible - with projection parameters and GDAL versions...
        try:
            tif_file = self.__convert_asc_tif(asc_filename_path, mask_file)
        except Exception as e:
            super()._show_critical_message_box(str(e), 'GDAL processing error')
            return
        
        
        """
        If no project file not loaded when running plugin
        """
        
        super()._check_create_project()

        # Set symbology from QML file:
        # 1) as given parameter by user or
        # 2) automatically by program
        qml_file = None
        # self defined symbology:
        if dock.check_symb.isChecked():
            qml_file = dock.inputqml.text()
            # if the use of a user defined qml file will be relevant, check it
            if not Path(qml_file).exists():
                super()._show_critical_message_box("The specified QML file doesn't exist!", 'File error')
                return
        # determine QML file automatically:
        else:
            interval_minutes = adder.interval_minutes    # 'interval_minutes' for assigning a color map
            # Determine prepared QML-File delivered with the plugin:
            qml_file = self._model.qml_file(interval_minutes)    # <dest_prod_id>.qml or 'None'


        ll = LayerLoader(self._iface)    # 'iface' is from 'radolan2map'

        if dock.check_excl_zeroes.isChecked():
            ll.no_zeros = True  # Set 0 values to NODATA (= transparent)

        ll.load_raster(tif_file, qml_file, temporal=False)

        
        dock.btn_run_adder.setEnabled(True)    # re-activate
        
        
        dim, _max, _min, mean, total, valid, nonvalid = adder.get_statistics()
        
        s_max = str(_max)
        # if part after point is too long:
        l_max = s_max.split('.')
        if len(l_max[1]) > 2:
            s_max = f"{_max:.1f}"
        
        dock.text_filename.setText(asc_filename_path.stem)
        dock.text_shape.setText(dim)
        dock.text_max.setText(s_max)
        dock.text_min.setText(str(_min))
        dock.text_mean.setText(f"{mean:.1f}")
        dock.text_total_pixels.setText(str(total))
        dock.text_valid_pixels.setText(str(valid))
        dock.text_nonvalid_pixels.setText(str(nonvalid))
        
        super()._enable_and_show_statistics_tab()
        super()._finish()
        
        
        super()._load_print_layout(ll.layer_name, prod_id='Sum')    # dt=None

    
    
    def __convert_asc_tif(self, asc_filename_path, mask_file=None):
        """
        raise Exception
        At GDAL processing a lot of strange errors are possible - with projection parameters and GDAL versions...
        """
        
        model = self._model    # shorten
        
        
        model.set_data_dir("sum")
        model.create_storage_folder_structure()
        
        tif_bn = asc_filename_path.name.replace('.asc', '.tif')    # tif basename
        tif_filename_path = model.data_dir / tif_bn
        

        gdal_processing = GDALProcessing(model, asc_filename_path, tif_filename_path)
        #gdal_processing.produce_warped_tif_using_script()
        
        
        #l_elems = self.dock.cbbox_projections.currentText().split()    # EPSG:3035 ETRS89 / LAEA Europe
        #epsg_code = l_elems[0]
        #if epsg_code == '-':    # RADOLAN
        #    epsg_code = model.projection_radolan    # complete RADOLAN projection parameters
        prj_src = model.projection_radolan
        """ Finding the content of current item in combo box:
        Laborious over index, because otherwise the value of combo box would
        EPSG 3035: ETRS89 / LAEA Europe instead of
        EPSG:3035 """
        index = self.dock.cbbox_projections.currentIndex()
        prj_dest = model.projections[index]
        #prj_dest_test = self.dock.cbbox_projections.currentText()
        #self.out("projection (currentText): {}".format(prj_dest_test))
        
        gdal_processing.produce_warped_tif_by_python_gdal(prj_src, prj_dest, shapefile=mask_file)    # Exception
        
        return gdal_processing.tif_file
    
    
    # ......................................................................
    
    @property
    def tf_path(self):
        return self.dock.tf_path_adder.text()
    @tf_path.setter
    def tf_path(self, path):
        self.dock.tf_path_adder.setText(path)
        # after folder selection enable scan button:
        self.dock.btn_scan.setEnabled(True)
        self._last_dir = path
        
    
    @property
    def begin(self):
        return self._begin
    @begin.setter
    def begin(self, beg):
        self._begin = beg
        dt = QDateTime.fromString(beg, df_qt)
        self.dock.dateTimeEdit_beg.setDateTime(dt)
    
    @property
    def end(self):
        return self._end
    @end.setter
    def end(self, end):
        self._end = end
        dt = QDateTime.fromString(end, df_qt)
        self.dock.dateTimeEdit_end.setDateTime(dt)
    
    @property
    def last_dir(self):
        return self._last_dir
    
    