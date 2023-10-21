# -*- coding: utf-8 -*-

'''
Model

Manages everything with paths (from config), QGIS environment,
working on file system (create, delete).
For the special works, such as transformations, own classes exists.

Created on 23.11.2017
last change: 08.11.2019
@author: Weatherman
'''

import os
from pathlib import Path
import sys

from configparser import ConfigParser, NoOptionError
from glob import glob
#import platform    # to determine wether Windows or not

from qgis.core import QgsApplication, QgsProject, QgsVectorLayer
from qgis.core import QgsCoordinateReferenceSystem, QgsLayerTreeGroup


from .NumpyRadolanReader import NumpyRadolanReader

from . import def_products       # File 'def_products.py'
from . import def_projections    # File 'def_projections.py'
CONFIG_NAME = "config.ini"



class Model:
    '''
    classdocs
    '''
    
    
    def __init__(self):
        '''
        Constructor
        '''
        
        print(self)
        
        #self._plugin_dir = path.abspath(path.join(path.dirname(__file__), os.pardir))
        #self._plugin_dir = Path(self._plugin_dir)
        self._plugin_dir = Path(__file__).resolve().parent.parent    # classes/Model.py -> classes -> .. 
        
        config_file = self._plugin_dir / CONFIG_NAME
        
        if not config_file.exists():
            raise FileNotFoundError("Config file '{}'".format(config_file))
        
        #
        # Parameter
        #
        self._config_file = config_file
        
        #
        # Ermittelt
        #
        
        # Objekt, auf das wir im Folgenden immer zugreifen.
        # Statisch ging es leider aus welchen Gründen auch immer (war in anderen Methoden 'None').
        self._config = ConfigParser()
        self._config.read(config_file)
        
        self._product_defs = def_products.dict_titles
        self.out("{}: {} product titles loaded.".format(def_products.__name__, len(self._product_defs)))
        
        self._data_root  = None    # Path
        self._data_dir   = None    # Path    <root>/radolan or .../radklim or .../regnie
        
        self._l_projections      = []    # EPSG numbers or projection parameters
        self._list_of_used_files = []
        
        
        
    
    def __str__(self):
        return self.__class__.__name__
    
    
    def out(self, s, ok=True):
        if ok:
            print("{}: {}".format(self, s))
        else:
            print("{}: {}".format(self, s), file=sys.stderr)
    
    
    def set_data_dir(self, subdir_name):
        self._data_dir = self.data_root / subdir_name
        self.out("set_data_dir(): {}".format(self._data_dir))
    
    
    def create_storage_folder_structure(self, temp_dir=None):
        '''
        affects filesystem
        
        temp_dir: if it is set, then only create the temp_dir
        '''
        
        self.out("create_storage_folder_structure()")
        
        
        if temp_dir:
            """
            temp dir    (with cleaning)
            """
            
            temp_dir = self.temp_dir
            
            try:
                os.makedirs(temp_dir)    # inclusive data dir
            except FileExistsError:
                # Remove old content:
                print("  remove temp dir contents...")
                # If ignore_errors is set, errors are ignored; otherwise, if onerror is set, it is called to handle ...
                #shutil.rmtree(temp_dir)
                #shutil.rmtree(path, ignore_errors=True)
                # -> Deleting a whole directory is problematic ("in use").
                
                tempdir_pattern = str( Path(temp_dir) / '*' )
                
                for f in glob(tempdir_pattern):
                    try:
                        os.remove(f)
                        """ Curiously an exception occurred in Windows (7) when loading data
                    multiple times. Somehow the system does not let go of the data it touches. """
                    except WindowsError as e:    # only available on Windows
                        self.out("ERROR: {}\n  try to ignore.".format(e))
                # for
            else:
                self.out("temp dir created: {}".format(temp_dir))
            
            return
        # if temp_dir
        
        
        """
        temp dir    maybe root was changed, so check again...
        data dir
        """
        
        for _dir in (self.temp_dir, self._data_dir):
            
            try:
                os.makedirs(_dir)
                self.out("makedirs(): {}".format(_dir))
            except FileExistsError:
                pass
        
        
        
    
    
    def write_history_file(self):
        """
        hint: 'l_files' was filled in method "_init_dock()"
        """
        
        if not self.list_of_used_files:
            return
        
        
        _max = 9
        
        # write the _max items back:
        with self.history_file.open('w') as hf:
            for i, line in enumerate(self.list_of_used_files):
                if i >= _max:
                    break
                hf.write(line + '\n')
        
        self.out("selected file stored in '{}'".format(self.history_file))
        
    
    
    
    def create_default_project(self):
        ''' Load a prepared template project.
        see https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/loadproject.html '''
        
        self.out("create_default_project()")
        
        
        # Get the project instance
        project = QgsProject.instance()    # current project
        
        # Load another project:
        project_file = self.default_project_file
        self.out("loading template project: {}".format(project_file))
        project.read(project_file)
        
        
        """ Related to Windows / QGIS 3.10
        Phenomenon 1: after loading the template project,
        QGIS map canvas 'jumps outside' the layer extents, even though the template project
        was saved with map centered to Germany.
        Phenomenon 2: after loading the template project (actually) with crs EPSG:3035
        but the mouse pointer on the map showed WGS1984 coordinates.
        So the assumption was to try to fix that by extra setting up the project crs "from outside"
        to EPSG:3035.
        But the problem wasn't fixed with that.
        The crs setting below was actually inserted for Windows but we leave it here for all platforms.
        It can not hurt to set up the crs from outside again for the new project.
        """
        crs = QgsCoordinateReferenceSystem(3035)
        project.setCrs(crs)
        
        return project
    
    
    
    def product_description(self, prod_id):
        try:
            return self._product_defs[prod_id]
        except KeyError:
            return "Product has not been defined yet"
    
    
    def title(self, prod_id, dt_date=None):
        ''' Zugriff auf Title im Dictionary. '''
        
        s_date = dt_date.strftime("%d.%m.%Y, %H:%M UTC") if dt_date  else "<datetime>"
        
        return "{}, {}".format(self.product_description(prod_id), s_date)
    
    
    def qml_file(self, interval_minutes):
        '''
        interval_minutes: from header of binary file or determined by RADOLANAdder
        '''
        
        self.out("qml_file(interval_minutes={})".format(interval_minutes))
        
        if interval_minutes == -1:    # products in RVP6-Units: RX, WX, EX
            qml_fn = 'rvp6units'
        elif interval_minutes < 60:
            qml_fn = '5min'
        elif interval_minutes < 1440:
            qml_fn = 'hourly'
        elif interval_minutes < 4320:    # 3 days: 1440 * 3
            qml_fn = 'daily'
        elif interval_minutes <= 10080:    # 1440 * 7
            qml_fn = 'daily+'
        elif interval_minutes <= 259200:    # 1440 * (30 * 6) -> approx. 6 months
            qml_fn = 'monthly'
        # greater:
        else:
            qml_fn = 'yearly'
        
        
        qml_fn += ".qml"
        qml_file = self.symbology_path / qml_fn
        
        # QML file exists?
        if not qml_file.exists():
            self.out("qml_file(): QML file '{}' not found.".format(qml_file), False)
            qml_file = None
        
        return qml_file
    
    
    
    """
    Properties
    """
    
    # Dirs:
    
    @property
    def profile_dir(self):
        return QgsApplication.qgisSettingsDirPath()
    
    @property
    def plugin_dir(self):
        return self._plugin_dir    # Path
    @property
    def data_root(self):
        ''' read from definition file
        raise FileNotFoundError '''
        if self._data_root:    # cached?
            return self._data_root
        
        with self.data_root_def_file.open() as f:    # FileNotFoundError
            self.out("read 'data dir' from '{}':".format(f.name))
            self._data_root = Path( f.read() )
            print("  {}".format(self._data_root))
            return self._data_root
    @data_root.setter
    def data_root(self, d):
        ''' update, when user writes a new path in data dir def file '''
        self.out("update 'data_root': {}".format(d))
        self._data_root = d
    @property
    def data_dir(self):
        return self._data_dir
    @property
    def temp_dir(self):
        return self.data_root / 'tmp'    # important NOT to use '_data_root' here!
    '''
    @property
    def layout_dir(self):
        return self._plugin_dir / self._config.get('Paths', 'LAYOUT_PATH')
    '''
    @property
    def list_of_used_files(self):
        return self._list_of_used_files
    @list_of_used_files.setter
    def list_of_used_files(self, l):
        self._list_of_used_files = l
    
    @property
    def default_border_shape(self):
        """ gleich mit Check """
        #border_shape = path.join(self._plugin_dir, self._config.get('Paths', 'CUT_TO'))
        #
        #if not path.exists(border_shape):
        #    self.out("default shape mask '{}' not found!".format(border_shape), False)
        #    return None
        
        border_shape = self._plugin_dir / self._config.get('Paths', 'CUT_TO')
        
        if not border_shape.exists():
            self.out("default shape mask '{}' not found!".format(border_shape), False)
            return None
        
        return str(border_shape)    # convert as string, otherwise error "Posix path"
    
    @property
    def default_print_template(self):
        # verschiedene Namen wegen internem Pfad für Logo:
        #fn = "Druckvorlage.qpt" if not platform.system() == 'Windows'  else "Druckvorlage_win.qpt"
        
        #print_template = path.join( self._config.get('Paths', 'RESSOURCE_PATH'), "Layout/{}".format(fn) )
        #print_template = Path(self._config.get('Paths', 'RESSOURCE_PATH')) / "Layout" / fn
        
        print_template = self._plugin_dir / self._config.get('Paths', 'print_layout')
        
        #if not path.exists(print_template):
        if not print_template.exists():
            self.out("default print template '{}' not found!".format(print_template), False)
            return None
        
        return print_template
    
    @property
    def default_project_file(self):
        #project_file = self._config.get('Paths', 'DEFAULT_PROJECT')
        #project_file = path.join(self._plugin_dir, project_file)
        project_file = self._plugin_dir / self._config.get('Paths', 'DEFAULT_PROJECT')
        
        #if not path.exists(project_file):
        if not project_file.exists():
            self.out("default project '{}' not found!".format(project_file), False)
            return None
        
        return str(project_file)
    
    
    @property
    def symbology_path(self):
        #symb_path = self._config.get('Paths', 'STYLE_PATH')
        #symb_path = path.join(self._plugin_dir, symb_path)
        symb_path = self._plugin_dir / self._config.get('Paths', 'STYLE_PATH')
        
        #if not path.exists(symb_path):
        if not symb_path.exists():
            self.out("symbology path '{}' not found!".format(symb_path), False)
            return None
        
        return symb_path
    
    
    @property
    def logo_path(self):
        default_logo_image = self._plugin_dir / "img" / 'qgis_logo.png'
        
        try:
            logo_image = Path(self._config.get('Paths', 'logo_image'))
        except NoOptionError:    # use standard logo
            logo_image = default_logo_image
        else:
            if not logo_image.exists():
                self.out("logo image '{}' not found!".format(logo_image), False)
                logo_image = default_logo_image
        
        return logo_image
    
    @property
    def check_file(self):
        return Path(self.plugin_dir) / '__check__'
    @property
    def news_file(self):
        return Path(self.plugin_dir) / 'news.txt'
    @property
    def settings_file(self):
        return Path(self.plugin_dir) / 'settings.json'
    @property
    def data_root_def_file(self):
        return Path(self.profile_dir) / self._config.get('Paths', 'datadir_deffile_basename')
    @property
    def history_file(self):
        return Path(self.profile_dir) / self._config.get('Paths', 'last_products_basename')

    
    # Projections
    
    @property
    def dict_projections(self):
        return def_projections.projs
    
    @property
    def projection_radolan(self):
        _, params = def_projections.projs[0]    # [ desc, params ]
        return params
    
    @property
    def projections(self):
        return self._l_projections
    
    

def test_product_get_id(radolan_file):
    ''' Special function, called separately
    True if product is X-product (RX, WX, EX, that means coded in RVP6-units);
    False if not '''
    
    print('test_product_get_id("{}")'.format(radolan_file))
    
    nrr = NumpyRadolanReader(radolan_file)    # FileNotFoundError
    # -> file handle open
    header = nrr._read_radolan_header()
    nrr._fobj.close()
    
    prod_id = header[:2]
    
    print("  {}".format(header))
    print("  product id:", prod_id)
    
    return prod_id
    
    
