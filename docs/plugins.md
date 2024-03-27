# Plugins module

Boldi's Plugins module support extending any Python libraries with feature provided through
[Python package entry points](https://setuptools.pypa.io/en/latest/userguide/entry_point.html).

## Install

Boldi's Plugins module is distributed as the
[`boldi-plugins` Python package](https://pypi.org/project/boldi-plugin/),
thus to install it, run:

```shell
pip install boldi-plugins
```

...or add `"boldi-plugins"` as a dependency to your project.

## Import

Import the module like so:

```py
import boldi.plugins
# or:
from boldi.plugins import load
```

## Usage

Use the [`boldi.plugins.load`][] function to load all entry points (plugin classes) that both:

* match the given entry point `group`, and
* have the required type (`cls`).

## API

::: boldi.plugins
