# Process module

The Process module a friendlier interface to [`subprocess.run`][].

## Install

Boldi's Process module is distributed as the
[`boldi-proc` Python package](https://pypi.org/project/boldi-proc/),
thus to install it, run:

```shell
pip install boldi-proc
```

...or add `"boldi-proc"` as a dependency to your project.

## Import

Import the module like so:

```py
import boldi.proc
# or:
from boldi.proc import run, run_py
```

## Usage

### `run()`

Use the [`run()`][boldi.proc.run] function to call a subprocess like a function.

The program and the command line arguments can be passed as any number of positional arguments.

* If a positional argument is an [`str`][] (string), it will be split using [`shlex.split`][].
* If a positional argument is a [`list`][] of objects, those objects will be converted to `str`,
  but then passed as one separate argument per list item (no further splitting).

This allows conveniently passing multiple arguments as a single string,
while allowing "escaping" command line arguments by embedding them in a list.

Any keyword argument is passed on to [`subprocess.run`][] after defaults are applied.

### `run_py()`

Use the [`run_py()`][boldi.proc.run_py] function to call a Python script or module subprocess like a function.

Positional and keyword arguments are the same, except [`sys.executable`][] is automatically added as the first argument.

## API

::: boldi.proc
