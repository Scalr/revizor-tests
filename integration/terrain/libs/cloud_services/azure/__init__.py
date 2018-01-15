import glob
import os


def import_services():
    """Import all services in this directory in order to execute registration decorator"""
    path = os.path.dirname(os.path.abspath(__file__))
    for module in glob.glob(os.path.join(path, '*.py')):
        if module.startswith('__') or module.startswith('base_'):
            continue
        __import__(module.split('/')[-1].split('.')[0], globals(), locals())


import_services()
