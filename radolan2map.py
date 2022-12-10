# -*- coding: utf-8 -*-
"""
RADOLAN to map (radolan2map)

A QGIS plugin to bring a RADOLAN binary file onto a map.


class: radolan2map
Main controller

changed: 2020-12
created: 2019-09
email  : radolan2map@e.mail.de

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from pathlib import Path
import sys
import json

# Import the PyQt and QGIS libraries
# from qgis.core import QgsProject
from qgis.PyQt.QtCore import Qt, QCoreApplication, QSettings, QTranslator, QSize  # , QRect
from qgis.PyQt.QtWidgets import QMessageBox, QDockWidget, QAction
from qgis.PyQt.QtGui import QIcon
# Initialize Qt resources from file resources.py
# from .resources import *
from console import console    # show python console automatically

# Eigene Klassen
# .........................................................
class_path = Path(__file__).parent / 'classes'
sys.path.append(str(class_path))    # directory of further classes
from gui import DockWidget
from Model import Model
from ActionTabRADOLANLoader import ActionTabRADOLANLoader
from ActionTabRADOLANAdder  import ActionTabRADOLANAdder
from ActionTabRegnie        import ActionTabRegnie
from SettingsTab            import SettingsTab
# .........................................................



class Radolan2Map:
    """ QGIS Plugin Implementation. """

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        # Save reference to the QGIS interface
        self.iface = iface


        # initialize plugin directory
        self.plugin_dir = Path(__file__).parent

        # initialize locale
        # Bugfix: on Windows 10 and QGIS 3.6 Noosa occurred a TypeError.
        # The reason could be, that there are no translation files.
        try:
            locale = QSettings().value('locale/userLocale')[0:2]
        except TypeError as e:
            self.out(e, False)    # TypeError: 'QVariant' object is not subscriptable
        else:
            locale_path = self.plugin_dir / 'i18n' / 'Radolan2Map_{}.qm'.format(locale)

            if locale_path.exists():
                self.translator = QTranslator()
                self.translator.load(locale_path)
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&radolan2map')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Radolan2Map')
        self.toolbar.setObjectName(u'Radolan2Map')


        self._model = Model()

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        # Create the dialog (after translation) and keep reference
        self.dock = None

        # Action Tabs (each has it's own logic):
        self._actiontab_radolan = None
        self._actiontab_adder   = None
        self._actiontab_regnie  = None
        self._settings_tab      = None



    def __str__(self):
        return self.__class__.__name__


    def out(self, s, ok=True):
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Radolan2Map', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar. """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action



    def initGui(self):
        """ Create the menu entries and toolbar icons inside the QGIS GUI. """


        """
        note the icon path:
        ':/plugins/my_plugin/icon.png'.
        The colon instructs QGIS to use the compiled resources.py file to locate the icon.
        Open the original resources.qrc file and you'll see the connection.
        """
        #icon_path = ':/plugins/radolan2map/icon.png'
        icon_path = Path(__file__).parent / "img/icon.png"

        if not icon_path.exists():
            self.out("icon '{}' not found!".format(icon_path), False)

        self.add_action(
            str(icon_path),
            text=self.tr(u'radolan2map: load a RADOLAN binary file'),    # tooltip over plugin icon
            callback=self.open_dock,
            parent=self.iface.mainWindow())


    

    def open_dock(self):
        """
        This method will be called when you click the toolbar button or select the plugin menu item.
        """

        # Try to catch every Exception and show it in a graphical window.
        try:


            # Show the output of the plugin:
            #console.show_console()    # works but better:
            pythonConsole = self.iface.mainWindow().findChild( QDockWidget, 'PythonConsole' )
            try:
                if not pythonConsole.isVisible():
                    pythonConsole.setVisible(True)
            except AttributeError:    # can be 'None' above
                console.show_console()
                self.out("PythonConsole Error catched", False)


            self.out("open_dock()")


            # Test for catching a exception and show this to the user by a window:
            #raise RuntimeWarning("manual exception raised")


            # Create the dialog with elements (after translation) and keep reference
            # Only create GUI ONCE in callback, so that it will only load when the plugin is started

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)


            # Close dock via toolbar button:
            if self.dock:
                if self.dock.isVisible():
                    self.dock.close()
                    return
            # if first start
            else:
                """
                Detect first start after installation.
                There seems to be a problem with plugin reloading, so after
                (re)install there occur errors. So we handle this issue manually with
                a one time check file (deleted after the following message).
                """
                if self._model.check_file.exists():
                    msg = "After reinstalling the plugin QGIS should be restarted now,\n"\
                    " otherwise plugin errors are to be expected!"
                    QMessageBox.warning(self.iface.mainWindow(), 'initialize plugin', msg)
                    # Message should only appear one time, so the
                    # check file must be removed now:
                    self._model.check_file.unlink()
                    self.out("check file '{}' removed, message doesn't appear again.".format(self._model.check_file))

                    msg = "It's recommended to exit QGIS now.\n\nExit QGIS?"
                    reply = QMessageBox.question(self.iface.mainWindow(), 'Continue?',
                                                 msg, QMessageBox.Yes, QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        self.iface.actionExit().trigger()
                        return    # maybe unnecessary
                # if
                self._init_dock()

                news_file = self._model.news_file
                try:
                    with news_file.open() as f:
                        l_text = [ f.read() ]
                    if l_text:
                        l_text.append("\nThis info window won't be displayed again!\n")
                        l_text.append("You can view the change history at any time here:")
                        l_text.append("=> https://plugins.qgis.org/plugins/radolan2map/#plugin-versions")
                        text = '\n'.join(l_text)
                        QMessageBox.information(self.iface.mainWindow(), "New changes", text)
                except FileNotFoundError:
                    pass
                else:
                    news_file.unlink()
                    self.out("news file '{}' removed, message doesn't appear again.".format(news_file))
            # else



            self._settings_tab.update_projection_based_on_current_project()


            """
            DockWidget exists but maybe it's invisible
            Bring DockWidget to front (maybe it's minimized elsewhere...)
            """
            width  = self.dock.frameGeometry().width()
            height = self.dock.frameGeometry().height()
            # that's fine - if necessary, get the initialized values from the .ui:
            self.dock.setMinimumSize(QSize(width, height))    # width, height
            # -> prevents a too small Widget


            # show the dockwidget
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.dock.show()
            # Ohne diese Anweisung wurde das Fenster ab QGIS3 im Hintergrund geöffnet.
            #self.dock.setWindowFlags(Qt.WindowStaysOnTopHint)


        except Exception as e:
            l_msg = ["{}\n\n".format(e)]
            l_msg.append("If this error persists - even after restarting QGIS - it may be")
            l_msg.append(" helpful to update your QGIS / Python installation")
            l_msg.append(" and working with a new QGIS user profile.")
            l_msg.append("\nIf nothing helps, please write a bug report.")

            msg = "".join(l_msg)
            self.out(msg, False)
            QMessageBox.critical(self.iface.mainWindow(), 'Exception catched', msg)
            #raise    # for tests, for output of precise line number



    def _init_dock(self):
        '''
        Everything that is necessary for setup up the DockWidget.
        '''

        # Create the dockwidget (after translation) and keep reference
        self.dock = DockWidget()

        # connect to provide cleanup on closing of dockwidget
        self.dock.closingPlugin.connect(self.onClosePlugin)



        """
        resets / defaults
        """
        
        ############################
        # Tab settings
        ############################
        
        # add instances of 'iface', 'Model', 'gui' (dock):
        self._settings_tab = SettingsTab(self.iface, self._model, self.dock)
        
        # Try to setup the data folder, but maybe the def file does not exist yet:
        data_dir_unset = False
        try:
            self._settings_tab.storage_dir = self._model.data_root
            self.out(f"'data dir def file' found:\n  {self._model.data_root_def_file}")
        except FileNotFoundError:
            data_dir_unset = True
            self.out("'data dir def file' not found -> init")
        
        
        self._actiontab_radolan = ActionTabRADOLANLoader(self.iface, self._model, self.dock)
        
        self._actiontab_adder   = ActionTabRADOLANAdder(self.iface, self._model, self.dock)
        
        self._actiontab_regnie  = ActionTabRegnie(self.iface, self._model, self.dock)
        
        
        
        
        tab_index = -1    # unset
        
        """
        If data def file doesn't exist, the action tabs will be disabled
        """
        if data_dir_unset:    # disable tabs:
            self.dock.tabWidget.setTabEnabled(self.dock.TAB_RADOLAN_LOADER, False)
            self.dock.tabWidget.setTabEnabled(self.dock.TAB_RADOLAN_ADDER, False)
            self.dock.tabWidget.setTabEnabled(self.dock.TAB_REGNIE, False)    # disable also tab "REGNIE"
            tab_index = self.dock.TAB_SETTINGS    # tab for define storage folder
        
        
        
        """
        Load settings from file
        """
        
        settings_file = self._model.settings_file
        
        try:
            
            self.out(f"reading settings from '{settings_file}'")
            with open(settings_file) as json_file:
                settings = json.load(json_file)
                
                try:
                    self._actiontab_radolan.mask_file = settings['mask_file']
                except KeyError:
                    pass
                
                try:
                    self._actiontab_radolan.qml_file = settings['qml_file']
                except KeyError:
                    pass
                
                # always available:
                self.dock.check_cut.setChecked(settings['bool_cut'])
                self.dock.check_excl_zeroes.setChecked(settings['bool_excl_zeroes'])
                self.dock.check_symb.setChecked(settings['bool_symb'])
                
                try:
                    self._actiontab_regnie.regnie_file = settings['regnie']
                except KeyError:
                    pass
                
                try:
                    self._actiontab_adder.tf_path = settings['adder_dir']
                except KeyError:
                    pass
                
                try:
                    self._actiontab_adder.begin = settings['begin']
                    self._actiontab_adder.end   = settings['end']
                except KeyError:
                    pass
                
                # show last tab:
                if tab_index < 0:    # change only, if 'tab_index' unset:
                    try:
                        tab_index = settings['tab_index']
                    except KeyError:
                        tab_index = self.dock.tab_index    # use default
            # with
        
        except FileNotFoundError:
            self.out(f"settings file '{settings_file}' doesn't exist yet.")
        
        # tab index somehow set:
        if tab_index > -1:
            self.dock.tab_index = tab_index
            
        
        
    
    def onClosePlugin(self):
        """ Cleanup necessary items here when plugin dockwidget is closed """
        
        # disconnects
        self.dock.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashs
        # when closing the docked window:
        # self.dock = None
    
    
    def unload(self):
        """
        Removes the plugin menu item and icon from QGIS GUI.
        => Executed when exit QGIS - also when plugin never opened!
        """
        
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&radolan2map'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
        
        # Plugin (Dock) never initialized - nothing to do - otherwise access to None-types:
        if not self.dock:
            return
        
        #
        #        Save
        #
        """
        save used files for suggestion to the user at next start
        """
        self._model.write_history_file()
        
        
        """
        save program settings
        """
        # fetch attributes for saving to file now:
        settings = {}
        check_text = self._actiontab_radolan.mask_file
        if check_text:
            settings['mask_file'] = check_text
        check_text = self.dock.inputqml.text()
        if check_text:
            settings['qml_file']  = check_text
        settings['bool_cut']         = self.dock.check_cut.isChecked()
        settings['bool_excl_zeroes'] = self.dock.check_excl_zeroes.isChecked()
        settings['bool_symb']        = self.dock.check_symb.isChecked()
        
        check_text = self._actiontab_regnie.regnie_file
        if check_text:
            settings['regnie'] = check_text
        
        # RADOLAN Adder:
        adder_dir = self._actiontab_adder.last_dir
        if adder_dir:
            settings['adder_dir'] = adder_dir
        
        begin = self._actiontab_adder.begin
        if begin:
            settings['begin'] = begin
        end = self._actiontab_adder.end
        if end:
            settings['end'] = end
        
        # save last tab:
        settings['tab_index'] = self.dock.tab_index
        
        with open(self._model.settings_file, 'w') as json_file:
            json.dump(settings, json_file, indent=4)
    
    
    