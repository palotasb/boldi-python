# Boldi's Python Libraries

These are Boldi's personal Python libraries.

[Read the docs on `python.boldi.net`.](https://python.boldi.net/)

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

* [`boldi.proc`](https://python.boldi.net/proc/) (`boldi-proc` package)
* [`boldi.ctx`](https://python.boldi.net/ctx/) (`boldi-ctx` package)
* [`boldi.plugins`](https://python.boldi.net/plugins/) (`boldi-plugins` package)
* [`boldi.cli`](https://python.boldi.net/cli/) (`boldi-cli` package)
* [`boldi.dev`](https://python.boldi.net/dev/) (`boldi-dev` package)
