__author__ = 'gigimon'
import time

from lettuce import step


@step('I wait ([\d]+) minutes')
def wait_time(step, minutes):
    time.sleep(int(minutes)*60)
