# Process module

The Process module provides a friendlier wrapper around [`subprocess.run`][].

## String argument processing

```py
from boldi.proc import run

run("echo 'Hello, World!'")
# Prints: Hello, World!
# Returns: CompletedProcess(args=['echo', 'Hello, World!'], returncode=0)
```

As you can see from the return value, `echo` was invoked with one argument: `"Hello, World!"`.
Simple string args passed to `run()` are processed via [`shlex.split`][].

## Quoting arguments

Another way to quote arguments is to pass them inside a list.

```py
from boldi.proc import run

run("echo", ["Hello, World!"])
# Prints: Hello, World!
# Returns: CompletedProcess(args=['echo', 'Hello, World!'], returncode=0)
```

This example is equivalent to the previous one.

Think of the `[` list `]` as a way of quoting arguments,
telling the `run()` function not to further process those arguments.

## Other positional arguments

Other types of positional arguments are converted to [`str`][]
and directly passed as arguments to the subprocess.

This is useful for passing numbers or [`pathlib.Path`][] objects that may contain spaces.

## Keyword arguments

Keyword arguments are the same as in [`subprocess.run`][] except that a few default values are different.

See the [`boldi.proc.run`][] API docs for details.

## Running Python scripts

The [`run_py()`][boldi.proc.run_py] function is a shortcut for running Python scripts.
It correctly selects the current Python interpreter ([`sys.executable`][]) as the first argument.
All other arguments are the same as in [`run()`][boldi.proc.run].

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

## API

::: boldi.proc
