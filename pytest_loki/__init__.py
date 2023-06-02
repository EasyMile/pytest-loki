import os
import re
import time
import numbers
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from urllib.parse import urljoin

import requests


class PytestLokiException(Exception):
    pass


def pytest_addoption(parser):
    group = parser.getgroup('terminal reporting')
    group.addoption(
        '--loki-url',
        help='Loki URL to send metrics to'
    )
    group.addoption(
        '--loki-metrics-prefix',
        help='Prefix for all metrics'
    )
    group.addoption(
        '--loki-extra-label',
        action='append',
        help='Extra labels to attach to reported metrics'
    )
    group.addoption(
        '--loki-env-label',
        metavar="label=value",
        action='append',
        help='Environment var to use as label. Will be lowercased.'
    )
    group.addoption(
        '--loki-env-value',
        action='append',
        help='Environment var to use as key=value in log lines. Will be lowercased. Key can be renamed with ENV_VAR=new_key syntax.'
    )
    group.addoption(
        '--loki-basic-auth',
        help='Optional HTTP Basic auth credentials in the user:password format'
    )


def pytest_configure(config):
    if config.getoption('loki_url'):
        config._loki = LokiReport(config)
        config.pluginmanager.register(config._loki)


def pytest_unconfigure(config):
    loki = getattr(config, '_loki', None)

    if loki:
        del config._loki
        config.pluginmanager.unregister(loki)


class LokiReport:

    def __init__(self, config):
        self._prefix = config.getoption('loki_metrics_prefix')
        self._push_error = None
        self._basic_auth = None
        self._tests_results = {}
        self._tests_results_raw = []
        self._loki_url = config.getoption('loki_url')
        if not self._loki_url.endswith('loki/api/v1/push'):
            self._loki_url = urljoin(self._loki_url, '/loki/api/v1/push')

        self._extra_labels = {}
        if extra_labels := config.getoption('loki_extra_label'):
            self._extra_labels = {item[0]: item[1] for item in [i.split('=', 1) for i in extra_labels]}

        if basicauth_creds := config.getoption('loki_basic_auth'):
            self._basic_auth = tuple(basicauth_creds.split(':'))

        # Collect env vars to use as labels
        for var in config.getoption('loki_env_label'):
            destvar = var
            if '=' in var:
                var, destvar = var.split('=')
            if not (value := os.environ.get(var)):
                raise PytestLokiException(f"No {var} in environment")
            self._extra_labels[destvar.lower()] = value

        self._env_vars_values = {}
        for var in config.getoption('loki_env_value'):
            self._env_vars_values[var.lower()] = os.environ[var]

    #
    # Public pytest plugin API
    #

    def pytest_runtest_logreport(self, report):
        # https://docs.pytest.org/en/latest/reference/reference.html#pytest.TestReport.when
        # 'call' is the phase when the test is being ran
        if report.when == 'call':
            test_suite = self._make_metric_name(report.location[2].split('.')[0])
            test_name = self._make_metric_name(report.location[2])

            if not self._tests_results.get(test_suite):
                self._tests_results[test_suite] = {}
            # TODO: Use a proper class instead of a big tuple
            self._tests_results[test_suite][test_name] = (report.outcome, report.duration, report.stop, f"{report.caplog}")

    def pytest_sessionfinish(self, session):
        streams = []
        for test_suite, tests in self._tests_results.items():
            streams.append(self._build_stream(test_suite, tests))
        self._push_error = self._push_to_loki(streams)

    def _build_stream(self, test_suite: str, tests: Dict):
        labels = {
            **{'test_suite': test_suite},
            **self._extra_labels,
        }
        lines = []
        for test_name, test_result in tests.items():
            success, duration, ts, caplog = test_result
            test_values = {'test_name': test_name, 'outcome': success, 'duration': duration}
            values = {**self._env_vars_values, **test_values}
            line = self._format_logfmt(values)
            if success == 'failed':
                line += caplog
            ns_ts = int(ts * 1000000000)
            lines.append([str(ns_ts), line])

        return (labels, lines)

    def pytest_terminal_summary(self, terminalreporter):
        # Write to the pytest terminal
        if not self._push_error:
            terminalreporter.write_sep('-', f'Successfully sent test results to loki at {self._loki_url}')
        else:
            terminalreporter.write_sep('-', self._push_error)
        for testreport in self._tests_results_raw:
            terminalreporter.write_sep('-', f'{testreport.__dict__}')

    #
    # Private helpers
    #

    @staticmethod
    def _format_logfmt(values):
        '''
        Formats arbitrary Dictionaries to logfmt log line
        Handles only string keys and simple types as values
        '''
        str_values = []
        for k, v in values.items():
            # Ignore non-str keys
            if not isinstance(k, str):
                continue
            # Ignore None values
            if v is None:
                continue
            if isinstance(v, bool):
                f"{v}".lower()
            elif not isinstance(v, numbers.Number):
                v = f'"{v}"'
            str_values.append(f"{k}={v}")
        return " ".join(str_values)

    def _push_to_loki(self, streams: List[Tuple[Dict, List[str]]]) -> str:

        payload = {'streams': []}

        for labels, lines in streams:
            stream = {
                'stream': labels,
                'values': lines
            }
            payload['streams'].append(stream)

        error_msg = None
        try:
            r = requests.post(self._loki_url, json=payload, auth=self._basic_auth)
        except requests.RequestException as e:
            error_msg = f"Could not send tests results to loki: {e}"
        else:
            if not r.ok:
                error_msg = f"Failed to send tests resulsts to loki: {r.status_code}: {r.content}"
        return error_msg

    def _make_metric_name(self, name):
        unsanitized_name = name
        if self._prefix:
            unsanitized_name = f'{self._prefix}_{name}'
        # Make test names prometheus-compatible to keep things as standard as possible
        # https://prometheus.io/docs/concepts/data_model/#metric-names-and-labels
        pattern = r'[^a-zA-Z0-9_]'
        replacement = '_'
        return re.sub(pattern, replacement, unsanitized_name)
