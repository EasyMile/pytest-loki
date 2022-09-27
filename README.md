# pytest Loki Reporter

A [pytest](https://docs.pytest.org/en/latest/) plugin that reports test results
to a [Loki instance](https://github.com/grafana/loki).

## Installation

You will be able to install it with pip:

```bash
pip install pytest-loki
```

But for now you'll have to install it manually using setup.py.

It'll automatically register as a pytest plugin - no extra steps needed. If no loki url is provided 
the plugin will not do anything.

## Usage

When invoking `py.test`, provide the following arguments:

1. `--loki-url`

   URL to the loki instance to send log lines to. Authentication is not supported.

2. `--loki-metrics-prefix`

   Each metric exported will be prefixed with this.

3. `--loki-env-label`

   Environment variabels to use as labels. Will be lowercased for readability.
   Can be rename with ENV_VAR=renamed_key syntax. Can be repeated many times.

3. `--loki-extra-label`

   This takes values of form `key=value`, and each metric will have these key
   value pairs as labels. Can be repeated many times.


## Inspiration

[pytest-prometheus](https://github.com/yuvipanda/pytest-prometheus) was an inspiration for
this codebase!
