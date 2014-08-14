import os
import time
import json
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
        new_config.append({'key': str(key), 'value': str(config[key]) if config[key] else '', 'configFile': str(filename)})
    return new_config


@step('"([\w\.]+)" file from ([\w]+) presets config')
def get_preset_file(step, filename, behavior):
    preset_configs = world.farm.get_presets(behavior)
    if not getattr(world, '%s_presets' % behavior, None):
        setattr(world, '%s_presets' % behavior, {})
    config = getattr(world, '%s_presets' % behavior)
    config[filename] = preset_configs['config'][filename]
    setattr(world, '%s_presets' % behavior, config)


@step('"([\w\.]+)" file from ([\w]+) contains keys \[([\w\d,/_-]+)\]')
def verify_keys_in_preset_file(step, filename, behavior, keys):
    keys = keys.split(',')
    config = getattr(world, '%s_presets' % behavior)[filename]
    LOG.debug('File "%s" contains:\n %s' % (filename, config))
    for key in keys:
        if not key in config:
            raise AssertionError('Config file "%s" from %s doesn\'t has a key: "%s"' % (filename, behavior, key))


@step('"([\w\.]+)" file from ([\w]+) not contains keys \[([\w\d,/_-]+)\]')
def verify_keys_in_preset_file(step, filename, behavior, keys):
    keys = keys.split(',')
    config = getattr(world, '%s_presets' % behavior)[filename]
    LOG.debug('File "%s" contains:\n %s' % (filename, config))
    for key in keys:
        if key in config:
            raise AssertionError('Config file "%s" from %s has a key: "%s"' % (filename, behavior, key))


@step('"([\w\.]+)" file from ([\w]+) contains values {([\w\d,:/_-]+)}')
def verify_keys_in_preset_file(step, filename, behavior, values):
    values = {x.split(':')[0]: x.split(':')[1] for x in values.split(',')}
    config = getattr(world, '%s_presets' % behavior)[filename]
    LOG.debug('File "%s" contains:\n %s' % (filename, config))
    for key in values:
        if not key in config:
            raise AssertionError('Config file "%s" from %s doesn\'t has a key: "%s"' % (filename, behavior, key))
        if not config[key] == values[key]:
            raise AssertionError('Key "%s" != "%s" it == "%s" in config file "%s" from %s' %
                                 (key, values[key], config[key], filename, behavior))


@step('I save "([\w\.]+)" content for ([\w]+) presets( I get error)?')
def save_config_file(step, filename, behavior, error):
    LOG.info('Save presets for %s' % behavior)
    config = getattr(world, '%s_presets' % behavior)[filename]
    config = json.dumps(convert_preset_config(config, filename))
    try:
        world.farm.save_presets(behavior, config)
    except:
        LOG.exception('Get error on save config "%s"' % filename)
        if error:
            LOG.debug('Don\'t raise exception because we expect this error')
            return
        raise
    if error:
        raise AssertionError('Expected error doesn\'t raised!')


@step('I (?:change|add) keys in "([\w\.]+)" file from ([\w]+) to {([\w\d,:/_-]+)}')
def change_keys_in_config(step, filename, behavior, values):
    values = {x.split(':')[0]: x.split(':')[1] for x in values.split(',')}
    config = getattr(world, '%s_presets' % behavior)
    LOG.debug('File "%s" contains:\n %s' % (filename, config))
    for key in values:
        config[filename][key] = values[key]
    setattr(world, '%s_presets' % behavior, config)

