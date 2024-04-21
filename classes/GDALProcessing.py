# -*- coding: utf-8 -*-

from pathlib import Path
import sys
import platform    # running on Windows or not
import subprocess

import processing
from processing.algs.gdal.GdalUtils import GdalUtils    # only for getting the version no.
from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem, QgsProcessingUtils, QgsProcessingContext
from qgis.PyQt.QtCore import QSettings

from osgeo import gdal    #, osr    # install Paket: 'python3-gdal'

gdal.UseExceptions()  # Enable exceptions

#convert_script = 'radolanasc_to_laeatif.py'    # <- .asc file


class GDALProcessing:
    """Created on 23.11.2017
    @author: Weatherman"""
    
    def __init__(self, model, full_asc_filename, full_tif_filename):
        
        self.out(f"<- model, '{full_asc_filename}', '{full_tif_filename}'")

        #
        # Input data
        #
        
        if not model:
            raise OSError("'model' is None!")
        
        self._model = model
        self._full_asc_filename = Path(full_asc_filename)
        self._full_tif_filename = Path(full_tif_filename)

        #
        # determined
        #
        
        self._result = None    # TIF-File oder TIF-Ergebnis im Speicher zur Weiterverarbeitung
        
        '''
        #convert_script_path = path.join(self._model.plugin_dir, convert_script)
        convert_script_path = path.join(path.dirname(__file__), convert_script)
        
        if not path.exists(convert_script_path):
            msg = "RADOLAN bin to tif convert script not found.\nSearched for: '{}'".format(convert_script_path)
            raise FileNotFoundError(msg)
        self._convert_script_path = convert_script_path
        '''
        self._convert_script_path = None    # only for old method

    def __str__(self):
        return self.__class__.__name__

    def out(self, s, ok=True):
        if ok:
            print(f"{self}: {s}")
        else:
            print(f"{self}: {s}", file=sys.stderr)
    
    def produce_warped_tif_by_python_gdal(self, prj_src, prj_dest_epsg, shapefile=None):
        """Convert by OSGEO python gdal module"""

        self.out(f"produce_warped_tif_by_python_gdal('{prj_dest_epsg}', shapefile='{shapefile}')")
        
        #proj4_params = "+proj=stere +lat_0=90 +lat_ts=60 +lon_0=10 +k=0.93301270189"\
        # + " +x_0=0 +y_0=0 +a=6370040 +b=6370040 +units=m +no_defs"
        '''
        # Mit dem Parameter 'k' funktionierte der Aufruf nicht (18.07.2019).
        proj4_params = ('+proj=stere +lat_0=90 +lat_ts=60 +lon_0=10'
                        '+x_0=0 +y_0=0 +a=6370040 +b=6370040'
                        '+units=m +no_defs')
        '''

        """\
A PRJ file contains a projected coordinate system.
It begins with a name for the projected coordinate system.
Then it describes the geographic coordinate system.
Then it defines the projection and all the parameters needed for the projection.
It then defines the linear units used in the projection.
The final entry (AUTHORITY) is optional and describes any standard designation for this projection.
Lines 2-8 define the geographic coordinate system.
It begins with a name for the geographic coordinate system.
Then it describes the datum.
Then it defines the prime meridian used. Finally, it defines the angular units.
Lines 3-5 define the geodetic datum. It begins with a name for the datum. Then it defines the spheroid.
Line 4 defines the spheroid. It begins with a name for the spheroid.
Then next parameter is the equatorial radius of the ellipsoid (in meters).
The last parameter is the inverse flattening factor.
"""
        spatial_ref = '''\
PROJCS["DWD (RADOLAN)",
    GEOGCS["RADOLAN Datum",
        DATUM["D_custom",
            SPHEROID["custom",6370040.0,0.0]],
        PRIMEM["Greenwich",0.0, AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.017453292519943295],
        AXIS["Longitude",EAST],
        AXIS["Latitude",NORTH]],
    PROJECTION["polar_stereographic"],
    PARAMETER["latitude_of_origin",90.0],
    PARAMETER["central_meridian",10.0],
    PARAMETER["standard_parallel_1",60.0],
    PARAMETER["scale_factor",0.93301270189],
    PARAMETER["false_easting",0.0],
    PARAMETER["false_northing",0.0],
    UNIT["Meter",1.0],
    AXIS["X",EAST],
    AXIS["Y",NORTH]]'''

        """
        Beginn
        """

        # string type important! otherwise problems with gdal.Warp()!
        ds_in = gdal.Open(str(self._full_asc_filename))
        #srs = osr.SpatialReference()
        #srs.ImportFromWkt(spatial_ref)
        #ds_in.SetProjection(srs.ExportToWkt())
        ds_in.SetProjection(spatial_ref)
    
        """ # works:
        dest = osr.SpatialReference()
        dest.ImportFromEPSG(3035)
        gdal.Warp(tif_file, ds_in, srcSRS=proj4_params, dstSRS=dest)
        """
    
        #gdal.Warp(tif_file, ds_in, srcSRS=proj4_params, dstSRS='EPSG:3035')
        
        self.out(f"gdal.Warp from '{prj_src}' -> '{prj_dest_epsg}'")
        #compress_method = 'LZW'
        compress_method = 'DEFLATE'    # lossless
        
        # from Config
        
        # with clipping:
        if shapefile:
            gdal.Warp(str(self._full_tif_filename), ds_in,
                      cutlineDSName=f'{shapefile}', cropToCutline=True,
                      srcSRS=prj_src, dstSRS=prj_dest_epsg,
                      creationOptions=[f'COMPRESS={compress_method}'])
        # without clipping:
        else:
            gdal.Warp(str(self._full_tif_filename), ds_in,
                      srcSRS=prj_src, dstSRS=prj_dest_epsg,
                      creationOptions=[f'COMPRESS={compress_method}'])

        ds_in = None  # should one do that?

    """
    following: old warp methods / scripts:
    """

    def produce_warped_tif_using_script(self):
        """
        Convert by command line
        """

        # starting with 'python3' so that it work on Windows?
        cmd = f'python3 {self._convert_script_path} "{self._full_asc_filename}"  -o "{self._full_tif_filename.parent}"'
        self.out(f'running: "{cmd}"')
        """
        * To also capture standard error in the result, use stderr=subprocess.STDOUT
        * shell=True, wenn cmd=string. Sonst als []
        * Since Python 3.6 you can make check_output() return a str instead
          of bytes by giving it an encoding parameter: ..., encoding='UTF-8' """
        # Exception (wenn exit != 0) auffangen:
        try:
            out = subprocess.check_output(cmd,
                                          stderr=subprocess.STDOUT, shell=True, universal_newlines=True,
                                          encoding='UTF-8')
        except subprocess.CalledProcessError as e:
            print(e.output)
        else:
            print(out)

    def produce_warped_tif(self, write_result):
        self.out("produce_warped_tif()")
        
        """
        ASCII to warped TIF
        """
        
        # very important!
        if self._full_tif_filename.exists():
            #self.out("removing old version of warped TIF before creating a new one...")
            self._full_tif_filename.unlink()
        
        proj_radolan = self._model.projection_radolan
        
        """
        METHOD Options:
        0 - near
        1 - bilinear
        2 - cubic
        3 - cubicspline
        4 - lanczos
        Eigentlich Default: 0 - aber man muss es angeben (QGIS 2.14 "Essen")
        
        RTYPE:  default: 5 = Float32
        
        COMPRESS(GeoTIFF options. Compression type:)
        0 - NONE
        1 - JPEG
        2 - LZW
        3 - PACKBITS
        4 - DEFLATE
        wohl kein Default, also angeben
        """
        # Standard (certain) params:
        params = {
            "INPUT":      str(self._full_asc_filename),
            "SOURCE_SRS": proj_radolan,
            #"DEST_SRS":  'EPSG:3035',    # QGIS 2?
            "TARGET_CRS": 'EPSG:3035',
            "METHOD":     0,
            "COMPRESS":   4
        }
        
        """
        useful tip:
        If you don't need to use the output for further elaborations, you may save it as memory layer.
        For doing this you only need to set the 'output' parameter as None:
        
        first = processing.runalg("gdalogr:warpreproject", { "INPUT": ... , "OUTPUT": None } )
        
        Instead, if you want to use the output, you may easily do this by giving it a name and
        then by calling it with getObject():
        
        second = processing.getObject( first['OUTPUT'] )

        -> https://gis.stackexchange.com/questions/224389/pyqgis-processing-runalg-release-input-in-windows
        """
        
        #params['OUTPUT'] = self._full_tif_filename if write_result  else None
        params['OUTPUT'] = self._full_tif_filename if write_result  else 'none'    # in QGIS 3. Verrückt
        
        
        # New GdalUtils version with some additional parameters! (RAST_EXT, ...)
        #if version >= 2000000:
        # Other possibility:
        #>>> QgsExpressionContextUtils.globalScope().variableNames(): show all avail vars
        #>>> QgsExpressionContextUtils.globalScope().variable('qgis_version')       # with name
        # out: u'2.99.0-Master'
        #>>> QgsExpressionContextUtils.globalScope().variable('qgis_version_no')    # better
        
        """ ..............................................................
        HERE WE CAN SEND A GDAL CALL ADAPTED TO THE CORRESPONDING VERSION!
        .............................................................. """
        
        add_additional_keys = False
        
        try:
            version = GdalUtils.version()
            
            if platform.system() == 'Windows':
                system_name = f"{platform.system()} {platform.release()}"
                raise OSError(f"Running on '{system_name}'")
            
        #except AttributeError as ex:    # ex: class GdalUtils has no attribute 'version'
        except AttributeError:
            self.out("WARN: GdalUtils.version could not determined (older version?)", False)
            self.out("continue without dict keys 'RAST_EXT', 'EXT_CRS'", False)
        
        except OSError as e:
            self.out(e, False)
            self.out("continue without dict keys 'RAST_EXT', 'EXT_CRS'", False)
        
        # only if try OK: section for determining the extent of input raster by creating layer datatype
        else:
            self.out(f"GdalUtils.version is {version}")
            # Result for
            # Dev-Version/Linux:  2010200
            # 2.18.15 Las Palmas: 2020300
            
            # For this version number it didn't work! (openSUSE Leap 42.3, QGIS version see above)
            if version != 2020300:
                add_additional_keys = True
            
        # End of try-except-else-block
        
        if add_additional_keys:
            # Make layer type from ASCII file to determine the mandatory 'extent':
            asc_layer = self._create_QGSRasterLayer_with_projection(proj_radolan)    # avoid projection dialog
            extent = asc_layer.extent()
            
            extent_params_as_string = "%f,%f,%f,%f" \
                % (extent.xMinimum(), extent.xMaximum(), extent.yMinimum(), extent.yMaximum() )
            
            # insert these params later for newer GDAL versions:
            params['RAST_EXT'] = extent_params_as_string    ### NEW! for new gdal versions.
            params['EXT_CRS' ] = proj_radolan               ### NEW! for new gdal versions. MUST be Radolan-Proj.!!!
            self.out("  -> inserting new keys 'RAST_EXT', 'EXT_CRS'")

        # Diagnose:
        print("### Dict params are:\n ", params)

        # For overview of the parameters use in QGIS python console:
        # processing.alghelp("gdalogr:warpreproject")
        #target = processing.runalg("gdalogr:warpreproject", params )    # return: dict    QGIS 2
        target = processing.run("gdal:warpreproject", params)    # QGIS 3
        
        fallback = False
        
        # TIF shouldt be written but doesn't exists:
        if write_result and not self._full_tif_filename.exists():
            fallback = True
        
        # Normal mode: return Memory Layer:
        if not fallback:
            #self._result = processing.getObject(target["OUTPUT"])    # key of dict, QGIS 2
            context = QgsProcessingContext()
            self._result = QgsProcessingUtils.mapLayerFromString(target["OUTPUT"], context)
            #print("result =", self._result)
            return    #return self._result

        """
        When warped TIF wasn't created:
        FALLBACK MODE without dict
            normally not, when dict is working
        The normal way is positive tested on a QGIS-dev on Linux 2.12.99.
        But the following fallback way need to implemented for the following
        configuration: also on Linux, Python-Version 2.7.12 (default, Jul 01 2016, 15:36:53) [GCC]
        QGIS-Version: 2.8.2 "Wien", exported
        """
        #return
        self._produce_warped_tif_fallback(write_result)
        
        # if success:
        # -> full_tif_filename is produced.

    def _create_QGSRasterLayer_with_projection(self, proj_radolan):
        """
        Change QGIS-Settings to avoid the assign CRS dialog to the ascii layer
        (appear at the point "QgsRasterLayer(...").
        asc_layer.setCrs(crs_radolan) is not sufficient!
        == Part 1 of 2 ==
        
        see
        https://gis.stackexchange.com/questions/27745/how-can-i-specify-the-crs-of-a-raster-layer-in-pyqgis/27765#27765
        """
        settings = QSettings()
        old_validation = settings.value("/Projections/defaultBehavior")
        settings.setValue("/Projections/defaultBehavior", "useGlobal")
        
        asc_layer = QgsRasterLayer(self._full_asc_filename, self._full_asc_filename.name)
        
        crs_radolan = QgsCoordinateReferenceSystem()
        crs_radolan.createFromProj4(proj_radolan)
        #asc_layer.setCrs( QgsCoordinateReferenceSystem(PROJ_RADOLAN_NATIVE, QgsCoordinateReferenceSystem.EpsgCrsId) )
        # -> funktioniert nicht :-/
        asc_layer.setCrs(crs_radolan)
        
        """
        Change QGIS-Settings to avoid the assign CRS dialog to the ascii layer.
        asc_layer.setCrs(crs_radolan) is not sufficient!
        == Part 2 of 2 ==
        """
        settings.setValue("/Projections/defaultBehavior", old_validation)
        
        return asc_layer

    def _produce_warped_tif_fallback(self, write_result):
        """ Fallback Method.
        Normally not used. Uses the same handed over parameters as the normal method """
        
        self.out("_produce_warped_tif_fallback()")
        
        self.out("ERROR: warped TIF wasn't produced, maybe there is a problem with"
                 " the processing.runalg dict interface(?)", False)
        self.out("switching to fallback mode with handed over conventional arguments", False)
        
        """
        !!! here we have to fill in every param in the correct order !!!
        
        ALGORITHM: Warp (reproject)
        
        INPUT <ParameterRaster>
        SOURCE_SRS <ParameterCrs>
        DEST_SRS <ParameterCrs>
        NO_DATA <ParameterString>
        TR <ParameterNumber>
        METHOD <ParameterSelection>
        RAST_EXT <ParameterExtent>               NEW (in this interface not used)
        EXT_CRS <ParameterCrs>                   NEW (in this interface not used)
        RTYPE <ParameterSelection>
        COMPRESS <ParameterSelection>
        JPEGCOMPRESSION <ParameterNumber>
        ZLEVEL <ParameterNumber>
        PREDICTOR <ParameterNumber>
        TILED <ParameterBoolean>
        BIGTIFF <ParameterSelection>
        TFW <ParameterBoolean>
        EXTRA <ParameterString>
        OUTPUT <OutputRaster>
        
        => Defaults / meaning of values see in above not fallback warp function
        """
        
        result = self._full_tif_filename if write_result  else None
        
        # without RAST_EXT, EXT_CRS:
        #processing.runalg("gdalogr:warpreproject",    # QGIS 2
        processing.run("gdal:warpreproject",    # QGIS 3
                        self._full_asc_filename,
                        self._model.projection_radolan, 'EPSG:3035',
                        "", 0, 0, 5, 4, 1, 1, 1, False, 2, False, "",
                        result)
        
        self._result = result
        #return result
    
    def clip_raster_by_mask(self, mask_shape):
        
        clipped_tif_name = self._full_tif_filename.name.replace('.tif', "_clipped.tif")
        clipped_tif_path = Path(self._model.data_dir, clipped_tif_name)
        
        self.out(f"clip_raster_by_mask('{mask_shape}')")
        
        if clipped_tif_path.exists():
            self.out("  removing old version of clipped TIF before creating a new one...")
            clipped_tif_path.unlink()
        
        # MemoryLayer as input for next step:
        
        #compress_method = 'LZW'
        compress_method = 'DEFLATE'    # lossless
        
        #processing.runandload("gdalogr:cliprasterbymasklayer", {
        # 'runandload' is useable here too, but we want to have the control, set name, position etc.
        processing.run("gdal:cliprasterbymasklayer", {
            'INPUT':   self._full_tif_filename,
            'MASK':    mask_shape,
            'OPTIONS': f'COMPRESS={compress_method}',
            'OUTPUT':  str(clipped_tif_path)
        })
        
        self.out(f"  -> '{clipped_tif_path}'")
        
        self._full_tif_filename = clipped_tif_path    # anpassen
        
        return clipped_tif_path
        
        ##--config GDALWARP_IGNORE_BAD_CUTLINE YES

    @property
    def tif_file(self):
        return self._full_tif_filename
