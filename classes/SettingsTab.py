import os
from pathlib import Path

from qgis.core           import QgsProject
from qgis.PyQt.QtWidgets import QFileDialog

# own classes:
from .ActionTabBase import ActionTabBase         # base class



class SettingsTab(ActionTabBase):
    """
    SettingsTab

    Separate __actions__ of setting operations from the other components

    Created on 20.12.2020
    @author: Weatherman
    """
    
    
    def __init__(self, iface, model, dock):
        super().__init__(iface, model, dock)
        
        self.dock.btn_select_storage_dir.clicked.connect(self._select_storage_dir)
        self.dock.btn_save.clicked.connect(self._write_new_storage_location)

        """
        fill projections
        Qt-element is connected with the projection list, via same index
        """
        
        for number, proj_desc in model.dict_projections.items():
            if number > 999:    # 4 digits expected
                entry = proj_desc
            else: # !: list type expected: desc, proj4-string
                assert type(proj_desc) is list
                entry, _ = proj_desc

            self.dock.cbbox_projections.addItem(entry)
        # for



    """
    Actions
    """
    
    def _select_storage_dir(self):
        dock = self.dock    # shorten
        
        start_dir = dock.textfield_path.text()
        # We assume a set up file here:
        if not start_dir:
            start_dir = str(Path.home())
        
        # parent, caption, directory, file_filter
        selected_dir = QFileDialog.getExistingDirectory(dock, 'Select RADOLAN/RADKLIM directory', start_dir,
                        # these additional parameters are used, because QFileDialog otherwise doesn't start with the given path:
                        QFileDialog.DontUseNativeDialog)
        
        if not selected_dir:
            return    # preserve evtl. filled line
        
        # NOT 'radolan2map/radolan2map'!
        const_last_part = 'radolan2map'
        if not selected_dir.endswith(const_last_part):
            complete_path = Path(selected_dir) / const_last_part
        else:
            complete_path = selected_dir

        # Set:
        self.storage_dir = complete_path
        
        # after folder selection enable save button:
        dock.btn_save.setEnabled(True)
    
    
    
    def update_projection_based_on_current_project(self):
        """
        - Determines projection (EPSG code) of current project
        - insert it in the list of projections
        - and choose it. """
        
        self.out("update_projection_based_on_current_project()")
        
        if not QgsProject.instance().fileName():    # if project loaded:
            return

        epsg_code = self._iface.mapCanvas().mapSettings().destinationCrs().authid()
        # Problem occured on Windows 10 with QGIS 3.10: empty 'epsg_code'.
        # Maybe with the application of "setDestinationCrs()" in 'create_default_project()' the problem isn't existent anymore.
        if not epsg_code:
            self.out("project CRS couldn't be determined; this is a unknown problem on Windows - not critical",
                     False)
            return

        def add_projection(projection_description, epsg_code):
            """ add projection to ComboBox and a list with epsg codes,
            which corresponds each other. """
            self.dock.cbbox_projections.addItem(projection_description)
            self._model.projections.append(epsg_code)

        # add only, if this projection doesn't exist:
        if not epsg_code in self._model.projections:
            projection_description = f"Project: {epsg_code}"
            add_projection(projection_description, epsg_code)
            # projection appended last, select last entry:
            index = len(self._model.projections) - 1    # -1 as last index doesn't work!
            self.dock.cbbox_projections.setCurrentIndex(index)

    
    def _write_new_storage_location(self):
        """ triggered by save button """
        
        path_to_save = self.storage_dir    # this dir probably doesn't exist, so we can't check it, we need the parent
        parent_dir = path_to_save.resolve().parent
        
        # protection: check if writetable:
        if not os.access(parent_dir, os.W_OK):
            l_msg = []
            l_msg.append(f'Directory "{parent_dir}" is not writable!')
            # User hint for Windows:
            if str(parent_dir).startswith('C:'):
                l_msg.append("(as a user, you probably do not have write permissions directly on C:)")
            l_msg.append('\nPlease choose another one.')
            msg = '\n'.join(l_msg)
            super()._show_critical_message_box(msg, 'Write permission error')
            return
        
        data_root_def_file = self._model.data_root_def_file
        
        with data_root_def_file.open('w') as f:
            f.write(str(path_to_save))
        
        self.out("_write_new_storage_location()")
        print(f"  saved path '{path_to_save}' to file '{data_root_def_file}'")

        dock = self.dock    # shorten
        dock.btn_save.setEnabled(False)    # show user, that action was performed
        # update new data path:
        self._model.data_root = Path(path_to_save)
        
        dock.tabWidget.setTabEnabled(dock.TAB_RADOLAN_LOADER, True)
        dock.tabWidget.setTabEnabled(dock.TAB_RADOLAN_ADDER, True)
        dock.tabWidget.setTabEnabled(dock.TAB_REGNIE, True)
    
    # ..........................................................
    
    @property
    def storage_dir(self):
        return Path(self.dock.textfield_path.text())
    @storage_dir.setter
    def storage_dir(self, d):
        self.dock.textfield_path.setText(str(d))
    
    