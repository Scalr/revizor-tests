import logging
import logging.config

import pytest

from datetime import datetime
from pathlib import Path

from revizor2.conf import CONF


pytest_plugins = [
    'plugins.surefire'
]


#FIXME: rework this because py.test override all settings
# @pytest.fixture(scope='session', autouse=True)
def logging_setup(request):
    package = request.session.items[0].location[0].split('/', maxsplit=1)[0]
    path = Path(CONF.logging_path) / package
    if not path.exists():
        path.mkdir(mode=0o755, parents=True)
    logging_configuration = {
        'version': 1,
        'formatters': {
            'detailed': {
                'format': '[%(asctime)s] - %(levelname)s - %(name)s:%(lineno)s - %(message)s'
            },
            'light': {
                'format': '%(asctime)s - %(name)s - %(message)s'
            }
        },
        'handlers': {
            'info': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'filename': None,
                'formatter': 'light',
                'encoding': 'UTF-8'
            },
            'debug': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'filename': None,
                'formatter': 'detailed',
                'encoding': 'UTF-8'
            }
        },
        'loggers': {
            'root': {
                'level': 'DEBUG',
                'handlers': ['info', 'debug'],
                'propagate': True
            },
            f'{package}': {
                'level': 'DEBUG',
                'handlers': ['info', 'debug'],
                'propagate': True
            },
            'revizor2': {
                'level': 'DEBUG',
                'handlers': ['info', 'debug'],
                'propagate': True
            },
            'libcloud': {
                'level': 'DEBUG',
                'handlers': ['info', 'debug'],
                'propagate': True
            },

        }
    }

    for handler_name, handler_value in logging_configuration['handlers'].items():
        f_name = '_'.join((handler_name, f"{datetime.now().strftime('%m%d-%H.%M.%S')}.log"))
        handler_value['filename'] = (path / f_name).as_posix()

    logging.config.dictConfig(logging_configuration)
    logging.captureWarnings(True)
