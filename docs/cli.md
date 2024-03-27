# CLI module

The CLI module defines the `boldi` CLI and the classes necessary
for other modules to define `boldi` CLI subcommands via an internal plugin system.

## Install

Boldi's CLI module is distributed as the
[`boldi-cli` Python package](https://pypi.org/project/boldi-cli/),
thus to install it, run:

```shell
pip install boldi-cli
```

...or add `"boldi-cli"` as a dependency to your project.

## Run

The Boldi CLI can be invoked using the `boldi` command:

```shell
boldi --help
```

## Subcommands

### `boldi`

Same as [`boldi help`](#boldi).

### `boldi help`

Shows the help message for a subcommand.

### `boldi dev`

Subcommand used for developing Boldi's Python libraries.
Available if the `boldi-dev` Python package is installed.

See: [Development module](dev.md).

## Plugins

Subcommands for `boldi` (such as `boldi help` or `boldi dev`) can be defined using plugins.

The plugin must be declared as a
[Python package entry point](https://setuptools.pypa.io/en/latest/userguide/entry_point.html),
with the following properties:

* The entry point group must be `boldi.cli.action`.
* The entry point name will be used as the name of the subcommand.
* The entry point must refer to a class that inherits from [`boldi.cli.CliAction`].
* The class must implement the subcommand:
  * The class's `__init__` method must implement the subcommand argument parser.
  * The class's `do_action` method must implement the feature provided by the subcommand.

## API

::: boldi.cli
