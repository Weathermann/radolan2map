import os
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt

from qgis.core import (
    Qgis,
    QgsProject,
    QgsLayerTreeLayer,
    QgsRasterTransparency,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsDateTimeRange,
    QgsRasterLayerTemporalProperties,
)
import processing


class LayerLoader:
    """
    LayerLoader

    Loads creates and load a QgsRaster- or QgsVectorLayer

    Created on 07.12.2020
    @authors: Weatherman, Tobias Rosskopf
    """
    
    def __init__(self, iface):
        print(self)

        self._iface = iface

        # set or determined later:
        self._no_zeros = False  # set zeros invisible
        self._layer_name = None
        self._temporal = None

    def __str__(self):
        return self.__class__.__name__

    def out(self, s, ok=True):
        if ok:
            print(f"{self}: {s}")
        else:
            print(f"{self}: {s}", file=sys.stderr)

    def _show_message(self, qgis_state, layer_name, duration=0):
        """ Where the integer 0 indicates a no timeout (i.e. no duration). """

        if qgis_state == Qgis.Success:
            title = "Success"
            msg = f'Layer "{layer_name}" loaded!'
        else:
            title = "Error"
            msg = f'Layer "{layer_name}" failed to load!'
            self.out(msg, False)
        
        self._iface.messageBar().pushMessage(title, msg, level=qgis_state, duration=duration)

    def create_and_load_layer_group(self, layergroup_name, list_of_files_and_qml):
        self._temporal = True

        qgis_groups = QgsProject.instance().layerTreeRoot()
        if qgis_groups.findGroup(layergroup_name):
            self.out(f'adding layers to existing layer group "{layergroup_name}"')
        else:
            self.out(f'create layer group "{layergroup_name}"')
            # obtain the layer tree of the top-level group in the project
            root = self._iface.layerTreeCanvasBridge().rootGroup()
            root.addGroup(layergroup_name)

        # root = QgsProject.instance().layerTreeRoot()  # another possibility,
        # but first group layers disappear in the second run(?)
        tree = self._iface.layerTreeCanvasBridge().rootGroup()
        layer_group = tree.findGroup(layergroup_name)
        layer_group.setExpanded(False)  # collapse group after filling

        # for performance reason disable output for many files:
        saved_stdout = sys.stdout
        saved_stderr = sys.stderr
        self.out("disable output for performance reasons, loading layers...")
        f_devnull = open(os.devnull, 'w')
        sys.stdout = f_devnull
        sys.stderr = sys.stdout  # redirect both

        for tif_file, qml_file in list_of_files_and_qml:
            bn = Path(tif_file).name
            raster_layer = QgsRasterLayer(str(tif_file), bn)

            if not raster_layer.isValid():
                self._show_message(Qgis.Critical, bn)
                continue

            raster_layer.setName(Path(tif_file).stem)
            self._insert_layer(raster_layer, qml_file, 0, layer_group)
        # for

        f_devnull.close()
        sys.stderr = saved_stderr
        sys.stdout = saved_stdout
        self.out("output channels restored")

        # TODO: collapse color definition
        #for layer in layer_group.findLayers():
        #    #print(layer.name())
        #    # filtering only raster layers
        #    if layer.type() == QgsMapLayerType.RasterLayer:  # RasterLayer?
        #        LayerNode = root.findLayer(layer.id())
        #        LayerNode.setExpanded(False)  # hiding the bands etc.

        self._show_message(Qgis.Success, layer_name=f"Group {layergroup_name}", duration=5)

    def load_raster(self, tif_file, qml_file=None, temporal=True):

        self._temporal = temporal

        bn = Path(tif_file).name

        raster_layer = QgsRasterLayer(str(tif_file), bn)

        # this too? Lead to layer loaded twice.
        # QgsMapLayerRegistry.instance().addMapLayer(raster_layer)

        if not raster_layer.isValid():
            self._show_message(Qgis.Critical, bn)
            return

        """
        The new raster layer is ok and we will continue to work with it in the following
        """

        """
        --- Clean: If necessary remove existing layer ---

        If a raster layer with the above name already exists, it will be removed beforehand.
        The "legend" apparently has nothing to do with the composer legend!
        """

        # for layer in self._iface.legendInterface().layers():    # QGIS 2
        # for layer in self._iface.layerTreeView().selectedLayers():

        """ the complicated way:
        project = QgsProject.instance()
        raster_layers = [rl for rl in project.mapLayers().values() if rl.type() == 1]
        self.out("current project: {} raster layers found.".format(len(raster_layers)))

        for layer in raster_layers:
            #if layer.type() == QgsMapLayer.RasterLayer  and  layer.name() == radolan_layer_name:
            if layer.name() == layer_name:
                self.out('RasterLayer with existing name "{}" found.'.format(layer.name()))
                ''' Ausgabe
                1 Raster
                0 DEU_adm0
                '''
                # print(layerType, layer.name())

                print("  removing layer \"{}\"".format(layer.name()))
                project.removeMapLayer( layer.id() )
        """

        layer_name = Path(tif_file).stem
        self._layer_name = layer_name
        raster_layer.setName(layer_name)

        self._remove_layer_with_same_name(layer_name)

        #
        # Load result raster
        #

        # previous version without insert at specific position (was also ok):
        # self._iface.addRasterLayer(raster_to_load, path.basename(raster_to_load) )

        # Einfaches result_layer.setLayerName('Raster') bringt leider nichts.
        # Unser Rasterlayer kann zuverlässig so bestimmt werden (kann gleich noch einmal gebraucht werden):
        # raster_layer = self._iface.activeLayer()

        self._insert_layer(raster_layer, qml_file, 3)

    def load_vector(self, csv_file, qml_file=None):
        # uri = "file:///{}?encoding=UTF-8&delimiter=,&xField=LON&yField=LAT&crs=EPSG:4326".format(regnie_csv_file)
        # -> was working, simpler variant:
        # uri = "{}{}?delimiter=,&xField=LON&yField=LAT".format('file:///', regnie_csv_file)
        # but not on Windows - needs crs specified:

        uri = f"file:///{csv_file}?delimiter=,&xField=LON&yField=LAT&crs=EPSG:4326"
        self.out(f"uri: {uri}")

        # Make a vector layer:
        csv_layer = QgsVectorLayer(uri, csv_file.name, "delimitedtext")

        if not csv_layer.isValid():
            self._show_message(Qgis.Critical, csv_file.name)
            return

        layer_name = Path(csv_file).stem
        self._layer_name = layer_name
        csv_layer.setName(layer_name)
        self._remove_layer_with_same_name(layer_name)
        self._insert_layer(csv_layer, qml_file, 5)

    def _remove_layer_with_same_name(self, layer_name):
        layers = QgsProject.instance().mapLayersByName(layer_name)

        for layer in layers:
            self.out(f'Layer with existing name "{layer.name()}" found - removing.')
            QgsProject.instance().removeMapLayer(layer.id())
    
    def _insert_layer(self, layer, qml_file, duration, layer_group=None):

        # Build pyramids
        self.out("Building pyramids ...")
        layer = self._build_pyramids(layer)

        # Style layer with qml file
        if qml_file:
            self._set_qml(layer, qml_file)

        # Set opacity - also for black white (without QML):
        # Sets the opacity for the layer, where opacity is a value
        # between 0 (totally transparent) and 1.0 (fully opaque).
        opa = 0.6  # 0.6 = 40% transparency

        if isinstance(layer, QgsRasterLayer):
            layer.renderer().setOpacity(opa)
        else:
            # layer.setLayerTransparency(40)    # %    this method seems only be available for vector layer
            layer.setOpacity(opa)

        # Set zero values to transparent
        if self._no_zeros:
            self._set_zeroes_invisible(layer)

        # Set temporal settings for layer (since QGIS 3.14)
        if self._temporal and Qgis.QGIS_VERSION_INT >= 31400:
            self.out("Setting temporal settings ...")
            self._set_time_range(layer)

        # Insert layer at a certain position

        # Add the layer to the QGIS Map Layer Registry (the second argument must be set to False
        # to specify a custom position:
        QgsProject.instance().addMapLayer(layer, False)  # first add the layer without showing it

        # Obtain the layer tree of the top-level group in the project.
        # if-else: root or layer group?
        if layer_group:
            root = layer_group
        else:
            root = self._iface.layerTreeCanvasBridge().rootGroup()

        # The position is a number starting from 0, with -1 an alias for the end.
        # index 0: uppermost, index 1: second position under the vector layer group:
        index = -1 if layer_group else 1
        root.insertChildNode(index, QgsLayerTreeLayer(layer))

        if not layer_group:
            # mark the new layer and zoom to it's extent:
            self._iface.setActiveLayer(layer)
            self._iface.zoomToActiveLayer()
            self._show_message(Qgis.Success, layer.name(), duration)

    def _set_zeroes_invisible(self, layer):
        self.out("setting zeroes to 100% transparency")
        """
        # Set 0 values to NODATA (= transparent):
        provider = active_raster_layer.dataProvider()
        provider.setNoDataValue(1, 0)    # first one is referred to band number
        # -> is working
        """
        # better, conserves 0 value:
        tr = QgsRasterTransparency()
        tr.initializeTransparentPixelList(0)
        layer.renderer().setRasterTransparency(tr)

    def _set_qml(self, layer, qml_file):
        """
        @param layer: QgsRasterLayer
        """
        
        self.out(f"using QML file '{qml_file}'")
        
        #if layer.geometryType() == QGis.Point:
        layer.loadNamedStyle(str(qml_file))    # str() if Path
        
        #if hasattr(raster_layer, "setCacheImage"):    # OK, 09.12.2020

        try:
            layer.setCacheImage(None)
        except AttributeError:
            pass

        layer.triggerRepaint()  # muss aufgerufen werden, Layer bleibt sonst schwarzweiß
        # Das ist für die QML-Farbskala im Layerfenster:
        # self._iface.legendInterface().refreshLayerSymbology(active_raster_layer)    # QGIS 2
        self._iface.layerTreeView().refreshLayerSymbology(layer.id())

    def _set_time_range(self, layer: QgsRasterLayer) -> None:
        """
        Sets temporal settings for layer, especially start time and end time (since QGIS 3.14).

        Args:
            layer (QgsRasterLayer): Raster layer for which to set temporal settings
        """
        time_delta = self._extract_time_delta_from_layer_name(layer.name())
        timestamp_end = self._extract_timestamp_from_layername(layer.name())
        timestamp_start = timestamp_end - time_delta
        self.out(f"Time range from {timestamp_start:%d.%m.%Y %H:%M} to {timestamp_end:%d.%m.%Y %H:%M}.")

        dt_range = QgsDateTimeRange(timestamp_start, timestamp_end)
        begin = dt_range.begin()
        begin.setTimeSpec(Qt.TimeSpec.UTC)
        end = dt_range.end()
        end.setTimeSpec(Qt.TimeSpec.UTC)
        dt_range = QgsDateTimeRange(begin, end)
        self.out(dt_range)

        temp_props = layer.temporalProperties()
        temp_props.setMode(QgsRasterLayerTemporalProperties.ModeFixedTemporalRange)
        #temp_props.setFixedTemporalRange(QgsDateTimeRange(timestamp_start, timestamp_end))
        temp_props.setFixedTemporalRange(dt_range)
        temp_props.setIsActive(True)

    def _extract_time_delta_from_layer_name(self, layername: str) -> timedelta:
        """
        Extracts the time delta from the layer name based on RADOLAN products.

        Args:
            layername (str): Name of the RADOLAN raster layer (ex. RW_20180131-0950)

        Returns:
            timedelta: Time delta object
        """
        PRODUCT_DICT = {
            "RY": 5,
            "RW": 60,
            "SF": 1440,
        }
        product_name = layername.split("_")[0]


        # TODO: better pass var "INT" from RADOLAN header instead to define again(?)
        try:
            time_delta = PRODUCT_DICT[product_name]
        # if product not defined, eg. "HG"product:
        except KeyError:
            time_delta = 5

        # time delta minus 1 minute to avoid overlapping of layers
        # TODO: still overlapps with next layer, but why?
        return timedelta(minutes=time_delta-1)

    def _extract_timestamp_from_layername(self, layername: str) -> datetime:
        """
        Extracts the timestamp from the layername with regular expressions.

        Args:
            layername (str): Name of the RADOLAN raster layer (ex. RW_20180131-0950)

        Returns:
            datetime: Datetime object
        """
        groups = re.findall(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})", layername)
        groups = map(int, groups[0])

        return datetime(*groups)

    def _build_pyramids(self, layer: QgsRasterLayer) -> QgsRasterLayer:
        """
        Builds pyramids (overviews) for raster layer.

        Args:
            layer (QgsRasterLayer): Raster layer for which to build pyramids

        Returns:
            QgsRasterLayer: Raster layer with pyramids
        """

        parameters = {
            "INPUT": layer,
            "LEVELS": "2 4 8 16",
            "CLEAN": False,
            "RESAMPLING": 0,
            "FORMAT": 0,
            "OUTPUT": layer,
        }
        result = processing.run("gdal:overviews", parameters)

        return QgsRasterLayer(result["OUTPUT"], layer.name())

    # ..................................................

    @property
    def no_zeros(self):
        return self._no_zeros

    @no_zeros.setter
    def no_zeros(self, b):
        self._no_zeros = b

    @property
    def layer_name(self):
        return self._layer_name
