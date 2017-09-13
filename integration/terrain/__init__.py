import os
import sys
import glob

ROOT_PATH = os.path.abspath(os.path.join(__file__, '..', '..', '..'))
sys.path.append(ROOT_PATH)


def import_terrains():
    """Import all terrain files (by mask *_terrain.py) and register it in lettuce"""
    path = os.path.dirname(os.path.abspath(__file__))
    for module in glob.glob(os.path.join(path, '*_terrain.py')):
        __import__(module.split('/')[-1].split('.')[0], globals(), locals())
    __import__('functional.terrain', globals(), locals())

import_terrains()
