import sys
from pathlib import Path
import time

from qgis.core           import QgsProject, QgsPrintLayout, QgsReadWriteContext
from qgis.PyQt.QtWidgets import QMessageBox
# For the QGIS printing template:
from qgis.PyQt.QtXml     import QDomDocument


class ActionTabBase:
    """
    ActionTabBase

    Base class of all specialized tab classes

    ActionTab classes act as it's own controllers

    Created on 19.12.2020
    @author: Weatherman
    """
    
    
    def __init__(self, iface, model, dock):
        print(self)
        
        self._iface = iface
        self._model = model
        self.dock   = dock

    
    def __str__(self):
        return self.__class__.__name__

    def out(self, s, ok=True):
        if ok:
            print(f"{self}: {s}")
        else:
            print(f"{self}: {s}", file=sys.stderr)
        

    def _show_critical_message_box(self, msg, caption='Exception catched'):
        self.out(msg, False)
        QMessageBox.critical(self._iface.mainWindow(), caption, msg)
    

    def _enable_and_show_statistics_tab(self):
        self.dock.tabWidget.setTabEnabled(self.dock.TAB_STATISTICS, True)
        self.dock.tabWidget.setCurrentIndex(self.dock.TAB_STATISTICS)    # show statistics tab

    
    def _check_create_project(self):
        """
        If no project file not loaded when running plugin
        """
        project = QgsProject.instance()
        project_fn = project.fileName()
        # for inspection of the project file, to determine, if it is a real file:
        # QGIS 3.22: seems to be always 'True' for exists() (?)
        #print(f"### project={project}, Path={project_fn}, exists={Path(project_fn).exists()}")

        # prepare project
        # QGIS 3.22: seems to be always 'True' for exists() (?), so check for content too:
        if project_fn and Path(project_fn).exists():
            return
        
        self.out("### no project open -> create a new one ###")
        project = self._model.create_default_project()
        
        yyyymmddHHMM_with_ext = time.strftime("%Y%m%d_%H%M") + '.qgs'
        new_file = self._model.data_root / yyyymmddHHMM_with_ext
        self.out(f"write: {new_file}")
        project.write(str(new_file))

    
    def _finish(self):
        """ prints a unified message at end of operation """
        self.out("*** Whole process finished! ***")
    
    
    def _load_print_layout(self, layer_name, prod_id, dt=None):
        window_title = "Print"    # will be checked with a found composer title
        
        """
        Avoid creating a new PrintComposer again and again here.
        Otherwise more and more composers will be added to the list - even with the same name.
        """
        
        project = QgsProject.instance()
        # From it, you can get the current layoutManager instance and deduce the layouts
        layout_manager = project.layoutManager()
        
        layout = layout_manager.layoutByName(window_title)
        
        if not layout:
            self.out("no composer found; creating one...")
            
            # Load the template into the composer
            # QGIS 2:
            #active_composer = self.iface.createNewComposer(window_title)    #createNewComposer()
            #active_composer = QgsComposition(QgsProject.instance())
            
            #layout = QgsLayout(project)
            layout = QgsPrintLayout(project)
            layout.initializeDefaults()    # initializes default settings for blank print layout canvas

            q_xmldoc = self._create_qdocument_from_print_template_content()
            
            # load layout from template and add to Layout Manager
            #layout.composition().loadFromTemplate(q_xmldoc)    # QGIS 2
            layout.loadFromTemplate(q_xmldoc, QgsReadWriteContext())
            layout.setName(window_title)
            
            layout_manager.addLayout(layout)

            # Update Logo:
            
            #logo_item = layout.getComposerItemById('logo')    # QGIS 2
            logo_item = layout.itemById('logo')
            logo_image = self._model.logo_path
            self.out(f"Logo: {logo_image}")
            if logo_image.exists():
                logo_item.setPicturePath(str(logo_image))
            else:
                self.out(f"  ERROR: logo '{logo_image}' not found!", False)
        # if
        
        
        """
        Hier versuche ich ein für die Überschrift mit einer ID ('headline') versehenes
        QgsLabel aus dem Template ausfindig zu machen. Ich mache das hier sehr kompliziert,
        es gibt bestimmt einen einfacheren Weg.
        Folgendes hat NICHT funktioniert:
        map_item = active_composer.getComposerItemById('headline')
        print(active_composer.items())
        liefert: [<PyQt4.QtGui.QGraphicsRectItem object at 0x124c60e8>, <qgis._core.QgsComposerLabel object at 0x124c65a8>, ... ]
        """
        
        ''' other possibility:
        for item in list(layout.items()):
            #if type(item) != QgsComposerLabel:
        '''
        
        # QgsComposerLabel:
        composer_label = layout.itemById('headline')    # a QgsComposerLabel was provided with the ID 'headline' in the template
        # -> None if not found
        
        if composer_label:
            title    = self._model.title(prod_id, dt)
            subtitle = ""
            if prod_id != 'RW':
                subtitle = f"\n{prod_id}-Produkt (Basis: RW)"
            
            composer_label.setText(title + subtitle)
        else:
            # A note that the template needs to be revised:
            self.out("no element with id 'headline' found!", False)
        

        legend = layout.itemById('legend')
        
        if not legend:
            self.out("legend couldn't created!", False)
            return

        #
        # Layer für die Legende ausfindig machen
        #
        
        # You would just need to make sure your layer has a name you can distinguish from others. Instead of:
        # Vorherige Version:
        #active_raster_layer = self.iface.activeLayer()
        
        # do:
        l_layer = project.mapLayersByName(layer_name)
        
        if not l_layer:
            self.out(f"legend: no layer found with name '{layer_name}'!", False)
            return
        
        active_raster_layer = l_layer[0]
        
        #print("Legend active_raster_layer id:",   active_raster_layer.id())     # ok
        #print("Legend active_raster_layer name:", active_raster_layer.name())   # ok
        #legend.model().setLayerSet([layer.id() for layer in layers])
        #legend.model().setLayerSet([active_raster_layer.id()])    # bringt nichts
        # DAS ist es! Dies fügt zumindest erstmal das interessierende Rasterlayer hinzu:
        #legend.modelV2().rootGroup().addLayer(active_raster_layer)
        #legend.updateLegend()
        
        #for layout in layout_manager.printLayouts():    # iterate layouts
        
        ''' would be ok, if we want to create a new legend -> then legend appears at the upper left corner
        legend = QgsLayoutItemLegend(layout)
        #legend.setTitle('Legend')
        legend.setAutoUpdateModel(False)
        group = legend.model().rootGroup()
        group.clear()
        group.addLayer(active_raster_layer)
        layout.addItem(legend)
        legend.adjustBoxSize()
        #legend.refresh()    # avoids adding all other layers 
        '''
        
        # uses existing legend object (see above), so we preserve it's layout position:
        legend.setAutoUpdateModel(False)
        group = legend.model().rootGroup()
        group.clear()
        group.addLayer(active_raster_layer)
        legend.adjustBoxSize()
        
        """ By default the newly created composer items have zero position (top left corner of the page) and zero size.
        The position and size are always measured in millimeters.
        # set label 1cm from the top and 2cm from the left of the page
        composerLabel.setItemPosition(20, 10)
        # set both label’s position and size (width 10cm, height 3cm)
        composerLabel.setItemPosition(20, 10, 100, 30)
        A frame is drawn around each item by default. How to remove the frame:
        composerLabel.setFrame(False)
        """
        #print(active_composer.rect().width(), active_composer.rect().height())                   # 1054 911
        #print(self.iface.mapCanvas().size().width(), self.iface.mapCanvas().size().height())     # 1517 535
        # "Leinwandgröße": habe keine vernünftigen Werte oben ermittelt (vielleicht Pixel; ich brauche mm).
        # selbst, mittels Mauszeiger ermittelt:
        width  = 210
        height = 297
        # Rand neben der Legende (mm):
        dw = 10
        dh = 14
        
        """
        Doesn't work since QGIS 3:
        """
        #self.out("In QGIS 3 the print layout doesn't work anymore. If you can do it ...", False)
        
        # nothing works
        #legendSize = legend.paintAndDetermineSize(None)
        #legend.setItemPosition(width - legendSize.width() - dw,  height - legendSize.height() - dh)
        #legend.setItemPosition(width - legend.width() - dw,  height - legend.height() - dh)

        # Also note that active_composer.composerWindow() has a hide() and show()
        #active_composer.composerWindow().hide()    # works

    
    def _create_qdocument_from_print_template_content(self):
        print_template = self._model.default_print_template
        
        self.out(f"_create_qdocument_from_print_template_content(): {print_template}")
        
        if not print_template:
            raise FileNotFoundError(f"{print_template}")
        
        # Load template
        with print_template.open() as templateFile:
            print_template_content = templateFile.read()
        
        q_xmldoc = QDomDocument()
        # If namespaceProcessing is true, the parser recognizes namespaces in the XML file and sets
        # the prefix name, local name and namespace URI to appropriate values. If namespaceProcessing
        # is false, the parser does no namespace processing when it reads the XML file.
        q_xmldoc.setContent(print_template_content, False)    # , bool namespaceProcessing
        
        return q_xmldoc
    
    