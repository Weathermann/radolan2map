'''
LayerLoader

Loads creates and load a QgsRaster- or QgsVectorLayer

Created on 07.12.2020
@authors: Weatherman, Tobias Rosskopf
'''

import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

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
    classdocs
    """


    def __init__(self, iface):
        """
        Constructor
        """

        print(self)

        self._iface = iface

        # set or determined later:
        self._no_zeros = False    # set zeros invisible
        self._layer_name = None


    def __str__(self):
        return self.__class__.__name__


    def out(self, s, ok=True):
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)


    def _show_message(self, qgis_state, layer_name, duration):

        if qgis_state == Qgis.Success:
            title = "Success"
            msg = "Layer '{}' loaded!".format(layer_name)
        else:
            title = "Error"
            msg = "Layer '{}' failed to load!".format(layer_name)
            self.out(msg, False)

        self._iface.messageBar().pushMessage(title, msg, level=qgis_state, duration=duration)


    def load_raster(self, tif_file, qml_file=None):

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
        uri = "{}{}?delimiter=,&xField=LON&yField=LAT&crs=EPSG:4326".format('file:///', csv_file)
        self.out("uri: {}".format(uri))

        # Make a vector layer:
        csv_layer = QgsVectorLayer(uri, csv_file.name, 'delimitedtext')

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
            self.out('Layer with existing name "{}" found - removing.'.format(layer.name()))
            QgsProject.instance().removeMapLayer(layer.id())


    def _insert_layer(self, layer, qml_file, duration):

        # Build pyramids
        self.out("Building pyramids ...")
        layer = self._build_pyramids(layer)

        # Style layer with qml file
        if qml_file:
            self._set_qml(layer, qml_file)

        # Set opacity - also for black white (without QML):
        # Sets the opacity for the layer, where opacity is a value
        # between 0 (totally transparent) and 1.0 (fully opaque).
        opa = 0.6    # 0.6 = 40% transparency

        if isinstance(layer, QgsRasterLayer):
            layer.renderer().setOpacity(opa)
        else:
            # layer.setLayerTransparency(40)    # %    this method seems only be available for vector layer
            layer.setOpacity(opa)

        # Set zero values to transparent
        if self._no_zeros:
            self._set_zeroes_invisible(layer)

        # Set temporal settings for layer (since QGIS 3.14)
        self.out("Setting temporal settings ...")
        if Qgis.QGIS_VERSION_INT >= 31400:
            self._set_time_range(layer)


        # Insert layer at a certain position

        # Add the layer to the QGIS Map Layer Registry (the second argument must be set to False
        # to specify a custom position:
        QgsProject.instance().addMapLayer(layer, False)  # first add the layer without showing it

        # obtain the layer tree of the top-level group in the project
        layerTree = self._iface.layerTreeCanvasBridge().rootGroup()
        # The position is a number starting from 0, with -1 an alias for the end.
        # Index 0: ganz oben, Index 1: 2. Position unter der Vektor-Layer-Gruppe:
        layerTree.insertChildNode(1, QgsLayerTreeLayer(layer))

        # mark the new layer and zoom to it's extent:
        self._iface.setActiveLayer(layer)
        self._iface.zoomToActiveLayer()

        self._show_message(Qgis.Success, layer.name(), duration)


    def _set_zeroes_invisible(self, layer):
        self.out("setting zeroes to 100% transparency")
        '''
        # Set 0 values to NODATA (= transparent):
        provider = active_raster_layer.dataProvider()
        provider.setNoDataValue(1, 0)    # first one is referred to band number
        # -> is working
        '''
        # better, conserves 0 value:
        tr = QgsRasterTransparency()
        tr.initializeTransparentPixelList(0)
        layer.renderer().setRasterTransparency(tr)


    def _set_qml(self, layer, qml_file):
        """
        @param raster_layer: QgsRasterLayer
        """

        self.out("using QML file '{}'".format(qml_file))

        # if layer.geometryType() == QGis.Point:
        layer.loadNamedStyle(str(qml_file))    # str() if Path

        # if hasattr(raster_layer, "setCacheImage"):    # OK, 09.12.2020
        try:
            layer.setCacheImage(None)
        except AttributeError:
            pass

        layer.triggerRepaint()    # muss aufgerufen werden, Layer bleibt sonst schwarzweiß
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

        temp_props = layer.temporalProperties()
        temp_props.setMode(QgsRasterLayerTemporalProperties.ModeFixedTemporalRange)
        temp_props.setFixedTemporalRange(QgsDateTimeRange(timestamp_start, timestamp_end))
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

        return timedelta(minutes=PRODUCT_DICT[product_name]) - timedelta(minute=1)  # -1 minute to avoid overlapping of layers TODO: not really effective


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
        result = processing.run('gdal:overviews', parameters)

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
