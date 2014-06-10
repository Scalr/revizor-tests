__author__ = 'gigimon'

import sys

from lxml import etree

from lettuce.terrain import after
from lettuce.terrain import before


class States(object):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    NOTRUNNING = 'NOT RUNNING'
    OUTLINE = 'OUTLINE'


def wrt(what):
    what = etree.tostring(what)
    if isinstance(what, unicode):
        what = what.encode('utf-8')
    sys.stdout.write(what+'\n')


@before.each_feature
def before_feature(feature):
    f = etree.Element('feature', name=feature.name, state=States.PENDING)
    f.text = '\n'.join([x for x in feature.description.splitlines() if not x.startswith('@')])
    wrt(f)


@after.each_feature
def after_feature(feature):
    state = States.FAILED if getattr(feature, '_failed', False) else States.SUCCESS
    f = etree.Element('feature', name=feature.name, state=state)
    wrt(f)


@before.each_scenario
def before_scenario(scenario):
    sc = etree.Element('scenario', name=scenario.name, state=States.PENDING)
    tags = etree.SubElement(sc, 'tags')
    tags.text = ','.join(scenario.tags)
    wrt(sc)


@after.each_scenario
def after_scenario(scenario):
    state = States.SUCCESS if scenario.passed else States.FAILED
    sc = etree.Element('scenario', name=scenario.name, state=state)
    wrt(sc)


@before.each_step
def before_step(step):
    state = States.PENDING
    if step.scenario and step.scenario.outlines:
        state = States.OUTLINE
    sc = etree.Element('step', name=step.original_sentence, state=state)
    wrt(sc)


@after.each_step
def after_step(step):
    if step.scenario and step.scenario.outlines:
        return
    if step.ran:
        state = States.SUCCESS if step.passed else States.FAILED
        if step.scenario and step.scenario.outlines:
            state = States.NOTRUNNING
    else:
        state = States.NOTRUNNING

    sc = etree.Element('step', name=step.original_sentence, state=state)
    if step.failed:
        trace = etree.SubElement(sc, 'traceback')
        trace.text = step.why.traceback
        step.scenario.feature._failed = True
    wrt(sc)


@after.outline
def print_outline(scenario, order, outline, reasons_to_fail):
    if order == 0:
        sc = etree.Element('outline', state=States.PENDING)
        head = etree.SubElement(sc, 'head')
        head.text = ','.join(scenario.keys)
        wrt(sc)
    state = States.FAILED if reasons_to_fail else States.SUCCESS
    sc = etree.Element('outlinestep', state=state,
                       keys=','.join(['%s=%s' % (x[0], x[1]) for x in scenario.outlines[order].items()]))
    if state == States.FAILED:
        trace = etree.SubElement(sc, 'traceback')
        trace.text = reasons_to_fail[0].traceback
    wrt(sc)
    if order+1 == len(scenario.outlines):
        sc = etree.Element('outline', state=States.SUCCESS)
        wrt(sc)