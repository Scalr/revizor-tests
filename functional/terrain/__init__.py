import os
import glob
import libs


def import_terrains():
    """Import all terrain files (by mask *_terrain.py) and register it in lettuce"""
    path = os.path.dirname(os.path.abspath(__file__))
    for module in glob.glob(os.path.join(path, '*_terrain.py')):
        __import__(module.split('/')[-1].split('.')[0], globals(), locals())

import_terrains()
