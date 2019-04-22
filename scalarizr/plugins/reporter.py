import os
import sys
import textwrap
import typing as tp

import pytest
from _pytest.config import Config
from _pytest.python import Function
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter
from py._io.terminalwriter import TerminalWriter

OUTCOME_MARKUP = {'passed': ('√', 'green'),
                  'failed': ('x', 'red'),
                  'skipped': ('-', 'yellow')}


@pytest.mark.trylast
def pytest_configure(config: Config):
    old_reporter = config.pluginmanager.getplugin('terminalreporter')
    rev_reporter = RevizorTerminalReporter(old_reporter.config)
    config.pluginmanager.unregister(old_reporter)
    config.pluginmanager.register(rev_reporter, 'terminalreporter')
    rev_reporter.clear()


def get_test_repr(item: Function, status: str = None):
    doc = None
    if item.obj.__doc__ is not None:
        doc = item.obj.__doc__.strip()
    mark = OUTCOME_MARKUP[status][0] if status in OUTCOME_MARKUP else '~'
    return '{} {}'.format(mark, doc or item.nodeid.split("::")[-1])


class RevizorTerminalReporter(TerminalReporter):
    def __init__(self, config, file=None):
        super().__init__(config, file)
        self.stdout = os.fdopen(os.dup(sys.stdout.fileno()), 'w')
        self._tw = TerminalWriter(self.stdout)
        self.started_test_classes = set()

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Function, call):
        outcome = yield
        report = outcome.get_result()
        setattr(report, 'test_repr', get_test_repr(item, report.outcome))
        return report

    def pytest_runtest_logstart(self, nodeid, location):
        pass

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item: Function):
        classname = item.parent.cls.__name__
        if classname not in self.started_test_classes:
            self.started_test_classes.add(classname)
            self._write_test_class_header(item.parent.obj)
        self._write_test_status(get_test_repr(item), item.location)
        yield

    def pytest_runtest_logreport(self, report: TestReport):
        cat, _, _ = self.config.hook.pytest_report_teststatus(report=report)
        self.stats.setdefault(cat, []).append(report)
        self._progress_nodeids_reported.add(report.nodeid)

        markup = {OUTCOME_MARKUP[report.outcome][1]: True} if report.outcome in OUTCOME_MARKUP else {}

        if report.when == 'call':
            test_repr = getattr(report, 'test_repr')
            self._write_test_status(test_repr, report.location, with_progress=True, rewrite=True, newline=True,
                                    **markup)

    def pytest_runtest_logfinish(self, nodeid):
        pass

    def _write_test_class_header(self, test_class: object):
        if test_class.__doc__ is not None:
            doc = textwrap.dedent(test_class.__doc__).strip()
        else:
            doc = test_class.__class__.__name__
        self.write_line('\n')
        self.write_line(textwrap.indent(doc, '  '), white=True)
        self.write_line('')

    def _write_test_status(self,
                           test_repr: str,
                           location: tp.Tuple[str, int, str],
                           with_progress: bool = False,
                           rewrite: bool = False,
                           newline: bool = False,
                           **markup):
        w = self._tw.fullwidth
        loc = location[2].replace('.', '::')
        if len(loc) > w // 2 - 8:
            loc = textwrap.shorten(loc, w // 2 - 8)
        right = loc + ' [100%]'
        l_left = len(test_repr)
        l_right = len(right) + 1
        if l_left + l_right >= w:
            test_repr = textwrap.shorten(test_repr, w - l_right - 1)
            l_left = len(test_repr)
        if rewrite:
            self.write('\r')
        self.write(test_repr, **markup)
        self.write(' ' * (w - l_left - l_right) + loc, light=True)
        if with_progress:
            self.write(self._get_progress_information_message(), cyan=True)
        else:
            self.write(' [ ~ %]', cyan=True)
        if newline:
            self.write_line('')

    def clear(self):
        self.write('\x1bc')
