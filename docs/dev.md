# Development module

The Development module implements features useful for developing Boldi's Python libraries.
It is only a dev dependency of the main `boldi` Python package, not a regular dependency,
like the other packages.

## Install

Boldi's Development module is distributed as the
[`boldi-dev` Python package](https://pypi.org/project/boldi-XXX/),
thus to install it, run:

```shell
pip install boldi-dev
```

...or add `"boldi-dev"` as a dependency to your project.

## Run

Boldi's Development module defines extensions to the [`boldi` CLI](cli.md),
so to use it, run the following command:

```shell
boldi dev --help
```

The `boldi dev` command is only available if the `boldi-dev` package is installed.

### `boldi dev`

This commands shows the help message for the other `boldi dev` subcommands.

### `boldi dev docs`

Generated the docs for Boldi's Python libraries.

### `boldi dev package`

Builds the Python packages for Boldi's Python libraries.

## API

::: boldi.dev
