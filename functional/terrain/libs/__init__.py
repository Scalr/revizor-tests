import os
import glob


def import_libs():
    """Import all .py files in this directory and all functions registers in world (if use decorator world.absorb)"""
    path = os.path.dirname(os.path.abspath(__file__))
    for module in glob.glob(os.path.join(path, '*.py')):
        if module.startswith('__'):
            continue
        __import__(module.split('/')[-1].split('.')[0], globals(), locals())

import_libs()
