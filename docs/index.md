# Boldi's Python Libraries

These are Boldi's personal Python libraries.

## `boldi` package

To install all of Boldi's Python libraries, run:

```shell
pip install boldi
```

...or add `"boldi"` to your Python dependencies.

See also: [PyPI: `boldi`](https://pypi.org/project/boldi/).

## `boldi` namespace

`boldi` is the root namespace shared by all modules.
It is a [namespace package](https://realpython.com/python-namespace-package/),
so while it can be imported, it doesn't directly define anything.

To achieve something useful, install one of the subpackages and use the corresponding submodules.

* [`boldi.proc`](proc.md) (`boldi-proc` package)
* [`boldi.ctx`](ctx.md) (`boldi-ctx` package)
* [`boldi.plugins`](plugins.md) (`boldi-plugins` package)
* [`boldi.cli`](cli.md) (`boldi-cli` package)
* [`boldi.dev`](dev.md) (`boldi-dev` package)
