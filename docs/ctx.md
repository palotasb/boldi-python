# Context module

The purpose of the Context module is to allow removing mutable global variables from Python code,
and allow replacing it with a single explicit parameter: [`ctx: Ctx`][boldi.ctx.Ctx].

## Install

Boldi's Context module is distributed as the
[`boldi-ctx` Python package](https://pypi.org/project/boldi-ctx/),
thus to install it, run:

```shell
pip install boldi-ctx
```

...or add `"boldi-ctx"` as a dependency to your project.

## Import

Import the module like so:

```py
import boldi.ctx
# or:
from boldi.ctx import Ctx
```

## Usage

The [`Ctx` class][boldi.ctx.Ctx] encapsulates mutable globals defined in the Python standard library,
and often used in regular Python code.
Code that whishes to get rid of mutable global variables can use an instance of the `Ctx` class
as a function argument, and manipulate only that object instead of global variables.

A `Ctx` instance can replace these otherwise mutable global variables:

* [`sys.argv`][sys.argv],
* [`os.environ`][os.environ],
* [`os.getcwd`][os.getcwd], [`os.chdir`][os.chdir],
* [`sys.stdin`][sys.stdin], [`sys.stdout`][sys.stdout], [`sys.stderr`][sys.stderr].

Using a `Ctx` doesn't change any global state (that's the point),
thus code unaware of `Ctx` won't use the values defined and set in a `Ctx` instance.
To make use of values inside a `Ctx` instance in 3rd party code or in Python standard library functions,
the values must be passed explicitly.
For example:

```py
import subprocess

from boldi.ctx import Ctx

def printing_example(ctx):
    print(..., file=ctx.stderr)

def subprocess_example(ctx, args):
    # these two are equivalent:
    subprocess.run(
        args,
        check=True,
        text=True,
        stdin=ctx.stdin, stdout=ctx.stdout, stderr=ctx.stderr,
        cwd=ctx.cwd,
        env=ctx.env
    )
    ctx.run(args)
```

A default `Ctx()` will hold the original mutable global variables.
This is safe to use if constructed in the `main()` function,
or when no explicit `ctx` parameter has been provided to a function.

```py
from boldi.ctx import Ctx

# for convenience, allows omitting the ctx parameter
def example(ctx: Ctx | None = None):
    ctx = ctx or Ctx()
    ...
```

Custom ctx values can be set inside unit tests or in any other context
where changing the original global variables is not intended.

### `run()` and `run_py()`

The [`Ctx.run()`][boldi.ctx.Ctx.run] and [`Ctx.run_py()`][boldi.ctx.Ctx.run_py]
methods are provided for convenience to call the [`boldi.proc.run`][] and [`boldi.proc.run_py`][]
functions with the keyword arguments using default values from the `Ctx` object.

## API

::: boldi.ctx
