# Context module

## Overview

The purpose of the Context module is to allow removing mutable global variables from Python code.

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

def example(ctx):
    print(..., file=ctx.stderr)
    subprocess.run(..., pwd=ctx.cwd, env=ctx.env)
```

A default `Ctx()` will hold the original mutable global variables.
This is safe to use if constructed in the `main()` function,
or when no explicit `ctx` parameter has been provided to a function.

Custom values can be set inside unit tests or in any other context
where manipulating the original global variables is not intended.

## Installation and usage

The Context module is distributed under the `boldi-ctx` Python package name,
thus to use it, run:

```shell
pip install boldi-ctx
```

...or add `"boldi-ctx"` as a dependency to your project.

Import it like so:

```py
import boldi.ctx
# or:
from boldi.ctx import Ctx
```

::: boldi.ctx
