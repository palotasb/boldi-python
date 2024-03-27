# Process module

The Process module provides a friendlier interface to [`subprocess.run`][].

```py
from boldi.proc import run, run_py
from pathlib import Path

run("sh -c", ["msg=$1; subj=$2; echo \"$msg, $subj!\""], "-s", ["Hello", "My Friend"])
# Hello, My Friend!
# CompletedProcess(args=['sh', '-euc', 'msg=$1; subj=$2; echo "$msg, $subj!"', '-s', 'Hello', 'My Friend'], returncode=0)

run_py("-c", ["import sys; print(f'{sys.argv!r}')"], [Path(r"C:\Documents and Setting\Spacey Jane")])
# ['-c', 'C:\\Documents and Setting\\Spacey Jane']
# CompletedProcess(args=['/Users/example/boldi-python/.venv/bin/python', '-c', "import sys; print(f'{sys.argv!r}')", 'C:\\Documents and Setting\\Spacey Jane'], returncode=0)
```

For more details see [`run()`](#run) and [`run_py()`](#run_py).

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

```py
from boldi.proc import run

run("sh -c", ["msg=$1; subj=$2; echo \"$msg, $subj!\""], "-s", ["Hello", "My Friend"])
# Hello, My Friend!
# CompletedProcess(args=['sh', '-c', 'msg=$1; subj=$2; echo "$msg, $subj!"', '-s', 'Hello', 'My Friend'], returncode=0)
```

* String-type positional arguments are split using [`shlex.split`][] into further arguments.
* Items inside [`list`][]-type positional arguments are converted to [`str`][], but not split into further arguments.
  
This allows conveniently passing multiple arguments as a single string.
Enclosing values in `[` square brackets `]` can be thought of as a way of quoting arguments to prevent splitting.

Any keyword argument is passed on to [`subprocess.run`][] after defaults are applied.

### `run_py()`

Use the [`run_py()`][boldi.proc.run_py] function to call a Python script or module subprocess like a function.

```py
from boldi.proc import run_py
from pathlib import Path

run_py("-c", ["import sys; print(f'{sys.argv!r}')"], [Path(r"C:\Documents and Setting\Spacey Jane")])
# ['-c', 'C:\\Documents and Setting\\Spacey Jane']
# CompletedProcess(args=['/Users/example/boldi-python/.venv/bin/python', '-c', "import sys; print(f'{sys.argv!r}')", 'C:\\Documents and Setting\\Spacey Jane'], returncode=0)
```

Positional and keyword arguments are the same as with [`run()`](#run),
except [`sys.executable`][] is automatically added as the first argument.

## API

::: boldi.proc
