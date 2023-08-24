# pytest Loki Reporter

A [pytest](https://docs.pytest.org/en/latest/) plugin that reports test results
to a [Loki instance](https://github.com/grafana/loki).

## Installation

There is no pypi repo yet. You can however install it with pip directly from github:

```bash
pip install git+https://github.com/EasyMile/pytest-loki.git@v0.1.3
```

You can also install it manually using setup.py.

Once installed, it'll automatically register as a pytest plugin - no extra steps needed.
If no loki url is provided the plugin will not do anything.

## Usage

When invoking `py.test`, provide the following arguments:

1. `--loki-url`

   URL to the Loki instance to send log lines to. Authentication is supported via `--loki-basic-auth`.

2. `--loki-metrics-prefix`

   Each metric exported will be prefixed with this.

3. `--loki-env-label`

   Environment variables to use as labels. Will be lowercased for readability.
   Can be renamed with `ENV_VAR=renamed_key` syntax. Can be repeated many times.

4. `--loki-extra-label`

   This takes values of form `key=value`, and each metric will have these key
   value pairs as labels. Can be repeated many times.

5. `--loki-env-value`

   Environment variables to use as key=value in log lines. Will be lowercased. Key can be renamed with `ENV_VAR=new_key` syntax. Can be repeated many times.

6. `--loki-basic-auth`

   Optional HTTP Basic auth credentials in the format `user:password`.

7. `--loki-retry-attempts`

   Number of retry attempts for pushing to Loki (default: 3).

8. `--loki-retry-interval`

   Interval in seconds between each retry attempt for pushing to Loki (default: 30).


## Inspiration

[pytest-prometheus](https://github.com/yuvipanda/pytest-prometheus) was an inspiration for
this codebase!
