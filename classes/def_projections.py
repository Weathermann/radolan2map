"""
Created on 21.11.2019
"""

from collections import OrderedDict


# int: String
# EPSG code, projection description
projs = OrderedDict()

# The projections are inserted in the projection combo box in the specified order.
# Key: number, Value: description, optional: projection parameters - value must be list type then.
projs[3035] = "EPSG 3035: ETRS89 / LAEA Europe"
projs[3857] = "EPSG 3857: Web Mercator / Pseudo Mercator"
projs[4326] = "EPSG 4326: WGS84 / World Geodetic System 1984"

""" With QGIS 3.10.1-A Coruña on openSUSE Linux 15.1 this projection
wasn't processed by gdal.Warp() with GDAL version 3.0.2 any more; maybe 'k' is the problem:
'+proj=stere +lat_0=90 +lat_ts=60 +lon_0=10 +k=0.93301270189 +x_0=0 +y_0=0 +a=6370040 +b=6370040 +units=m +no_defs' """
projs[0]    = ['RADOLAN polarstereographic projection', \
               '+proj=stere +lat_0=90 +lat_ts=60 +lon_0=10 +a=6370040 +b=6370040 +units=m +no_defs' ]
