# -*- coding: utf-8 -*-
"""
DockWidget
-----------------
begin: 2016-08-26
last:  2019-11
"""

from pathlib import Path
import sys
from datetime import datetime

from qgis.PyQt           import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore    import pyqtSignal
#from qgis.PyQt.QtWidgets import QFileDialog
# QWidget, QListWidget, QGridLayout, QPushButton

# not in 'classes', but directly in plugin folder:
plugin_dir = Path(__file__).resolve().parent.parent

image_dir = plugin_dir / 'img'

"""
Widget with the plugin functionality (DockWidget):
"""
WIDGET_FORM_CLASS, _ = uic.loadUiType(plugin_dir / 'dock_widget.ui')


def get_icon(img_basename):
    ''' simplifies creating a QIcon '''
    img_full_path = image_dir / img_basename
    return QtGui.QIcon(str(img_full_path))

def get_image(img_basename):
    ''' simplifies creating a Image '''
    img_full_path = image_dir / img_basename
    return QtGui.QPixmap(str(img_full_path))



class DockWidget(QtWidgets.QDockWidget, WIDGET_FORM_CLASS):
    
    # Indices of tabs: so that someone can easily change the order of the tabs
    TAB_RADOLAN_LOADER = 0
    TAB_RADOLAN_ADDER  = 1
    TAB_REGNIE         = 2
    TAB_STATISTICS     = 3
    TAB_SETTINGS       = 4
    TAB_ABOUT          = 5
    
    closingPlugin = pyqtSignal()
    
    
    def __init__(self, parent=None):
        """ Constructor. """
        super(DockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.setFloating(False)    # prevent losing the widget
        # -> doesn't seem to have an effect -> deselected this property in the .ui-file
        # seems that is impossible to set this as initial property in QT Creator.
        """ If you want to prevent the user from moving it to a floating window
        you need to set the "features" of the widget. In the example below,
        the widget is movable and closable, but not floatable: """
        #self.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetMovable)
        
        
        self.btn_close.clicked.connect(self.close)    # global close button
        self.btn_close.setIcon(get_icon('close.png'))
        
        
        self._tab_index = 0
        self.tabWidget.currentChanged.connect(self._tab_changed)
        
        
        ############################
        # Tab "RADOLAN single mode"
        ############################
        
        folder_icon = get_icon('folder.png')
        
        self.tabWidget.setTabIcon(DockWidget.TAB_RADOLAN_LOADER, get_icon('execute.png'))
        # set toolbar button icons:
        self.btn_load_project.setIcon(get_icon('new.png'))
        self.btn_load_radars.setIcon(get_icon('radar.png'))
        
        self.filedialog_input.setIcon(folder_icon)
        self.filedialog_mask.setIcon(folder_icon)
        self.filedialog_qml.setIcon(folder_icon)
        
        self.widget_symb.setVisible(False)
        # Only enabled for RX products (check at every load):
        self.check_rvp6tomm.setVisible(False)
        
        # connect functions:
        #self.btn_info.clicked.connect(self.open_about_dialog)
        # passing parameters to connected method only possible with keyword 'lambda':
        self.check_cut.stateChanged.connect(lambda: self._checkbox_state_changed(self.check_cut))
        self.check_symb.stateChanged.connect(lambda: self._checkbox_state_changed(self.check_symb))
        self.check_rvp6tomm.stateChanged.connect(lambda: self._checkbox_state_changed(self.check_rvp6tomm))
        
        #if not self.dock.inputpath.text():
        #    #self.dock.button_box.button(QDialogButtonBox.Cancel).setEnabled(True)
        #    self.dock.button_box.button(QDialogButtonBox.Apply).setEnabled(False)
        #    #self.out("OK button disabled -> please load a RADOLAN binary file first!")
        self.btn_action.setIcon(get_icon('execute.png'))
        self.btn_action.setEnabled(False)    # initially disabled, need to load RADOLAN file
        
        # trigger deactivating clipping:
        self.check_cut.setChecked(False)
        self._checkbox_state_changed(self.check_cut)
        
        
        ############################
        # Tab Statistics
        ############################
        tab_no = DockWidget.TAB_STATISTICS
        self.tabWidget.setTabEnabled(tab_no, False)    # second tab "statistics"
        self.tabWidget.setTabIcon(tab_no, get_icon('stats.png'))
        
        
        ############################
        # Tab TIF storage
        ############################
        
        self.tabWidget.setTabIcon(DockWidget.TAB_SETTINGS, get_icon('execute.png'))
        self.btn_select_storage_dir.setIcon(folder_icon)
        self.btn_save.setIcon(get_icon('save.png'))
        # save button is disabled by default
        self.btn_save.setEnabled(False)
        
        #self.setWindowIcon(get_icon('folder.png'))
        
        
        ############################
        # Tab REGNIE
        ############################
        
        self.tabWidget.setTabIcon(DockWidget.TAB_REGNIE, get_icon('regnie.png'))
        self.btn_select_regnie.setIcon(folder_icon)
        self.btn_load_regnie.setIcon(get_icon('regnie.png'))
        
        
        ############################
        # Tab "RADOLANAdder"
        ############################
        
        self.tabWidget.setTabIcon(DockWidget.TAB_RADOLAN_ADDER, get_icon('stack.png'))
        self.btn_select_dir_adder.setIcon(folder_icon)
        self.btn_scan.setIcon(get_icon('search.png'))
        self.btn_run_adder.setIcon(get_icon('execute.png'))
        
        
        
        ############################
        # Tab "about"
        ############################
        
        self.tabWidget.setTabIcon(DockWidget.TAB_ABOUT, get_icon('info.png'))
        
        # insert images:
        dt_today = datetime.today()
        # Christmas period?
        if dt_today.month == 12  and  dt_today.day >= 20  and  dt_today.day <= 31:
            # set QMovie as label:
            movie = QtGui.QMovie(str(image_dir / 'weihnachten.gif'))
            # set 'ScaledContents' in QtDesigner to False or self.label_logo.setScaledContents(False)
            self.label_logo.setMovie(movie)
            movie.start()
        else:
            self.label_logo.setPixmap(get_image('plugin_logo.png'))
        
        
        self.label_img_info.setPixmap(get_image('sw_info.png'))
        self.label_img_download.setPixmap(get_image('sw_download.png'))
        
        # fill text fields with metadata:
        self._fill_fields()
        
        ############################
        
        
        #self.list_widget = FileList()
        
    
    
    def __str__(self):
        return self.__class__.__name__
    
    def out(self, s, ok=True):
        if ok:
            print(f"{self}: {s}")
        else:
            print(f"{self}: {s}", file=sys.stderr)
    
    
    
    def _checkbox_state_changed(self, checkbox):
        name = checkbox.objectName()
        b = checkbox.isChecked()
        
        # Diag:
        #self.out("_checkbox_state_changed() from '{}': {}".format(name, b))
        
        if name == 'check_cut':
            self.inputmask.setEnabled(b)
            self.filedialog_mask.setEnabled(b)
        elif name == 'check_symb':
            self.widget_symb.setVisible(b)
    
    
    def _tab_changed(self):
        index = self.tabWidget.currentIndex()
        
        # save index only, if it is a relevant function tab:
        if index != DockWidget.TAB_STATISTICS  and  index != DockWidget.TAB_ABOUT:
            self._tab_index = index
            #msg = "Tab index changed! Save current tab index: {}".format(index)
            #self.out(msg)
        
    
    '''
    def _show_list(self):
        if self.list_widget.isVisible():
            self.list_widget.close()
        else:
            self.list_widget.show()
    '''
    
    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    
    
    def _fill_fields(self):
        metadata_file = plugin_dir / 'metadata.txt'
        
        version       = "?"
        issue_tracker = "?"
        mail_link     = "?"
        
        self.out("reading '{}'".format(metadata_file))
        
        with metadata_file.open() as f:
            for line in f:
                """ filter lines from metadata file:
                version=0.6
                email=radolan2map@e.mail.de
                tracker=https://gitlab.com/Weatherman_/radolan2map/issues
                """
                
                if line.startswith('version'):
                    version = self.__get_value(line)
                elif line.startswith('email'):
                    mailadress = self.__get_value(line)
                    mail_link = f'<a href="mailto:{mailadress}">{mailadress}</a>'
                elif line.startswith('tracker'):
                    issue_link = self.__get_value(line)
                    issue_tracker = f'<a href="{issue_link}">{issue_link}</a>'
            # for
        # with
        
        self.text_version.setText(version)
        self.text_issue.setText(issue_tracker)
        self.text_mailaddress.setText(mail_link)
        
    def __get_value(self, line):
        return line.strip().split('=')[1]    # version=0.6
    
    
    
    @property
    def tab_index(self):
        return self._tab_index
    @tab_index.setter
    def tab_index(self, i):
        self.tabWidget.setCurrentIndex(i)


'''
class FileList(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Select a file')
        
        self.listWidget = QListWidget()
        self.listWidget.clicked.connect(self.clicked)
        
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        
        layout = QGridLayout()
        layout.addWidget(self.listWidget)
        layout.addWidget(self.btn_close)
        
        self.setLayout(layout)
        
    def __str__(self):
        return self.__class__.__name__
    
    def out(self, s, ok=True):
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)
    
    def clicked(self):
        item = self.listWidget.currentItem()
        print(item.text())
    
    def add_items(self, l_items):
        self.out("load {} files".format(len(l_items)))
        self.listWidget.clear()
        self.listWidget.addItems(l_items)
'''


"""
if __name__ == "__main__":
    
    dlg = AboutDialog()
    dlg.show()
"""
