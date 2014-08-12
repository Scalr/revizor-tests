import os
import time
import logging
from datetime import timedelta

from lettuce import world, step
from lxml import html

from revizor2.api import IMPL
from revizor2.conf import CONF
from revizor2.utils import wait_until
from revizor2.fixtures import resources
from revizor2.helpers import generate_random_string
from revizor2.consts import Platform, ServerStatus, Dist

LOG = logging.getLogger(__name__)


def convert_preset_config(config, filename):
    new_config = []
    for key in config:
        new_config.append({'key': key, 'value': config[key], 'configFile': filename})
    return new_config


@step('"([\w\.]+)" file from ([\w]+) presets config')
def get_preset_file(step, filename, behavior):
    preset_configs = world.farm.get_presets(behavior)
    if not getattr(world, '%s_presets' % behavior, None):
        setattr(world, '%s_presets' % behavior, {})
    setattr(world, '%s_presets' % behavior, preset_configs['config'][filename])


@step('"([\w\.]+)" file from ([\w]+) contains keys [([\w\d,/_]+)]')
def verify_keys_in_preset_file(step, filename, behavior, keys):
    keys = keys.split(',')
    config = getattr(world, '%s_presets' % behavior)[filename]
    for key in keys:
        if not key in config:
            raise AssertionError('Config file "%s" from %s doesn\'t has a key: "%s"' % (filename, behavior, key))


@step('"([\w\.]+)" file from ([\w]+) contains values {([\w\d,/_]+)}')
def verify_keys_in_preset_file(step, filename, behavior, values):
    values = {x.split(':')[0]: x.split(':')[1] for x in values.split(':')}
    config = getattr(world, '%s_presets' % behavior)[filename]
    for key in values:
        if not key in config:
            raise AssertionError('Config file "%s" from %s doesn\'t has a key: "%s"' % (filename, behavior, key))
        if not config[key] == values[key]:
            raise AssertionError('Key "%s" != "%s" it == "%s" in config file "%s" from %s' %
                                 (key, config[key], values[key], filename, behavior))


@step('I save "([\w\.]+)" content for ([\w]+) presets')
def save_config_file(step, filename, behavior):
    config = getattr(world, '%s_presets' % behavior)[filename]
    config = convert_preset_config(config, filename)
    world.farm.save_presets(behavior, config)


@step('I change keys in "([\w\.]+)" file from ([\w]+) to {([\w\d,/_]+)}')
def change_keys_in_config(step, filename, behavior, values):
    values = {x.split(':')[0]: x.split(':')[1] for x in values.split(':')}
    config = getattr(world, '%s_presets' % behavior)
    for key in values:
        config[filename][key] = values[key]
    setattr(world, '%s_presets' % behavior, config)
