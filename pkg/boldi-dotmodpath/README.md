---
title: Python import mechanism detailed explanation
author: palotasb
threadId: T-019e22d7-d2ac-7645-b454-f2deacb9e323
created: 2026-05-13T19:37:10.521Z
agentMode: smart
---

# Python import mechanism detailed explanation

## User

Explain the Python import process when e.g., `import namespacepackage.subpackage.module` is executed. What are all the internal steps that happen within the interpreter, the module system, the finders, etc.? How are the steps different for the different packages, modules? Explain using direct references to https://docs.python.org/3/reference/import.html, https://docs.python.org/3/library/importlib.html, or other parts of docs.python.org.

## Assistant

**Tool Use:** `read_web_page`

```json
{
  "url": "https://docs.python.org/3/reference/import.html",
  "objective": "Get the precise steps and section anchors for how Python imports a dotted name like namespacepackage.subpackage.module, including finders, loaders, sys.modules caching, namespace packages, __path__, and submodule binding."
}
```

**Tool Use:** `read_web_page`

```json
{
  "url": "https://docs.python.org/3/library/importlib.html",
  "objective": "Get section anchors and key APIs for importlib.import_module, importlib._bootstrap, MetaPathFinder, PathFinder, FileFinder, importers, loaders, spec, exec_module, create_module."
}
```

## User

**Tool Result:** `toolu_vrtx_014d7E5DNz3V99srUGYuqBS4`

```
# 5. The import system ¶
A direct call to `__import__()` performs only the module search and, if
found, the module creation operation. While certain side-effects may occur,
such as the importing of parent packages, and the updating of various caches
(including `sys.modules` ), only the `import` statement performs
a name binding operation.
When an `import` statement is executed, the standard builtin `__import__()` function is called. Other mechanisms for invoking the
import system (such as `importlib.import_module()` ) may choose to bypass `__import__()` and use their own solutions to implement import semantics.

...

## 5.2. Packages ¶
All modules have a name. Subpackage names are separated from their parent
package name by a dot, akin to Python’s standard attribute access syntax. Thus
you might have a package called `email` , which in turn has a subpackage
called `email.mime` and a module within that subpackage called `email.mime.text` .

### 5.2.1. Regular packages ¶
Python defines two types of packages, regular packages and namespace packages . Regular
packages are traditional packages as they existed in Python 3.2 and earlier.
A regular package is typically implemented as a directory containing an `__init__.py` file. When a regular package is imported, this `__init__.py` file is implicitly executed, and the objects it defines are
bound to names in the package’s namespace. The `__init__.py` file can
contain the same Python code that any other module can contain, and Python
will add some additional attributes to the module when it is imported.
For example, the following file system layout defines a top level `parent` package with three subpackages:
```
parent / 
    __init__ . py 
    one / 
        __init__ . py 
    two / 
        __init__ . py 
    three / 
        __init__ . py
```

...

### 5.2.2. Namespace packages ¶
A namespace package is a composite of various portions ,
where each portion contributes a subpackage to the parent package. Portions
may reside in different locations on the file system. Portions may also be
found in zip files, on the network, or anywhere else that Python searches
during import. Namespace packages may or may not correspond directly to
objects on the file system; they may be virtual modules that have no concrete
representation.
Namespace packages do not use an ordinary list for their `__path__` attribute. They instead use a custom iterable type which will automatically
perform a new search for package portions on the next import attempt within
that package if the path of their parent package (or `sys.path` for a
top level package) changes.
With namespace packages, there is no `parent/__init__.py` file. In fact,
there may be multiple `parent` directories found during import search, where
each one is provided by a different portion. Thus `parent/one` may not be
physically located next to `parent/two` . In this case, Python will create a
namespace package for the top-level `parent` package whenever it or one of
its subpackages is imported.
See also [**PEP 420**](https://peps.python.org/pep-0420/) for the namespace package specification.

## 5.3. Searching ¶
To begin the search, Python needs the fully qualified name of the module (or package, but for the purposes of this discussion, the
difference is immaterial) being imported. This name may come from various
arguments to the `import` statement, or from the parameters to the `importlib.import_module()` or `__import__()` functions.
This name will be used in various phases of the import search, and it may be
the dotted path to a submodule, e.g. `foo.bar.baz` . In this case, Python
first tries to import `foo` , then `foo.bar` , and finally `foo.bar.baz` .
If any of the intermediate imports fail, a `ModuleNotFoundError` is raised.

### 5.3.1. The module cache ¶
The first place checked during import search is `sys.modules` . This
mapping serves as a cache of all modules that have been previously imported,
including the intermediate paths. So if `foo.bar.baz` was previously
imported, `sys.modules` will contain entries for `foo` , `foo.bar` ,
and `foo.bar.baz` . Each key will have as its value the corresponding module
object.
During import, the module name is looked up in `sys.modules` and if
present, the associated value is the module satisfying the import, and the
process completes. However, if the value is `None` , then a `ModuleNotFoundError` is raised. If the module name is missing, Python will
continue searching for the module.

...

### 5.3.2. Finders and loaders ¶
If the named module is not found in `sys.modules` , then Python’s import
protocol is invoked to find and load the module. This protocol consists of
two conceptual objects, finders and loaders .
A finder’s job is to determine whether it can find the named module using
whatever strategy it knows about. Objects that implement both of these
interfaces are referred to as importers - they return
themselves when they find that they can load the requested module.
Python includes a number of default finders and importers. The first one
knows how to locate built-in modules, and the second knows how to locate
frozen modules. A third default finder searches an import path for modules. The import path is a list of locations that may
name file system paths or zip files. It can also be extended to search
for any locatable resource, such as those identified by URLs.
The import machinery is extensible, so new finders can be added to extend the
range and scope of module searching.
Finders do not actually load modules. If they can find the named module, they
return a _module spec_ , an encapsulation of the module’s import-related
information, which the import machinery then uses when loading the module.
The following sections describe the protocol for finders and loaders in more
detail, including how you can create and register new ones to extend the
import machinery.
Changed in version 3.4: In previous versions of Python, finders returned loaders directly, whereas now they return module specs which _contain_ loaders.
Loaders are still used during import but have fewer responsibilities.

### 5.3.3. Import hooks ¶
The import machinery is designed to be extensible; the primary mechanism for
this are the _import hooks_ . There are two types of import hooks: _meta hooks_ and _import path hooks_ .
Meta hooks are called at the start of import processing, before any other
import processing has occurred, other than `sys.modules` cache look up.
This allows meta hooks to override `sys.path` processing, frozen
modules, or even built-in modules. Meta hooks are registered by adding new
finder objects to `sys.meta_path` , as described below.
Import path hooks are called as part of `sys.path` (or `package.__path__` ) processing, at the point where their associated path
item is encountered. Import path hooks are registered by adding new callables
to `sys.path_hooks` as described below.

### 5.3.4. The meta path ¶
When the named module is not found in `sys.modules` , Python next
searches `sys.meta_path` , which contains a list of meta path finder
objects. These finders are queried in order to see if they know how to handle
the named module. Meta path finders must implement a method called `find_spec()` which takes three arguments:
a name, an import path, and (optionally) a target module. The meta path
finder can use any strategy it wants to determine whether it can handle
the named module or not.
If the meta path finder knows how to handle the named module, it returns a
spec object. If it cannot handle the named module, it returns `None` . If `sys.meta_path` processing reaches the end of its list without returning
a spec, then a `ModuleNotFoundError` is raised. Any other exceptions
raised are simply propagated up, aborting the import process.
The `find_spec()` method of meta path
finders is called with two or three arguments. The first is the fully
qualified name of the module being imported, for example `foo.bar.baz` .
The second argument is the path entries to use for the module search. For
top-level modules, the second argument is `None` , but for submodules or
subpackages, the second argument is the value of the parent package’s `__path__` attribute. If the appropriate `__path__` attribute cannot
be accessed, a `ModuleNotFoundError` is raised. The third argument
is an existing module object that will be the target of loading later.
The import system passes in a target module only during reload.

...

## 5.4. Loading ¶
```
module = None 
 if spec . loader is not None and hasattr ( spec . loader , 'create_module' ): 
    # It is assumed 'exec_module' will also be defined on the loader. 
    module = spec . loader . create_module ( spec ) 
 if module is None : 
    module = ModuleType ( spec . name ) 
 # The import-related module attributes get set here: 
 _init_module_attrs ( spec , module ) 

 if spec . loader is None : 
    # unsupported 
    raise ImportError 
 if spec . origin is None and spec . submodule_search_locations is not None : 
    # namespace package 
    sys . modules [ spec . name ] = module 
 elif not hasattr ( spec . loader , 'exec_module' ): 
    module = spec . loader . load_module ( spec . name ) 
 else : 
    sys . modules [ spec . name ] = module 
    try : 
        spec . loader . exec_module ( module ) 
    except BaseException : 
        try : 
            del sys . modules [ spec . name ] 
        except KeyError : 
            pass 
```

...

* If there is an existing module object with the given name in `sys.modules` , import will have already returned it.
* The module will exist in `sys.modules` before the loader
executes the module code. This is crucial because the module code may
(directly or indirectly) import itself; adding it to `sys.modules` beforehand prevents unbounded recursion in the worst case and multiple
loading in the best.
* If loading fails, the failing module – and only the failing module –
gets removed from `sys.modules` . Any module already in the `sys.modules` cache, and any module that was successfully loaded
as a side-effect, must remain in the cache. This contrasts with
reloading where even the failing module is left in `sys.modules` .
* After the module is created but before execution, the import machinery
sets the import-related module attributes (“_init_module_attrs” in
the pseudo-code example above), as summarized in a later section .

...

### 5.4.2. Submodules ¶
Given Python’s familiar name binding rules this might seem surprising, but
it’s actually a fundamental feature of the import system. The invariant
holding is that if you have `sys.modules['spam']` and `sys.modules['spam.foo']` (as you would after the above import), the latter
must appear as the `foo` attribute of the former.

...

### 5.4.4. __path__ attributes on modules ¶
The `__path__` attribute should be a (possibly empty) sequence of strings enumerating the locations where the package’s
submodules will be found. By definition, if a module has a `__path__` attribute, it is a package .
A package’s `__path__` attribute is used during imports of its
subpackages.
Within the import machinery, it functions much the same as `sys.path` ,
i.e. providing a list of locations to search for modules during import.
However, `__path__` is typically much more constrained than `sys.path` .
The same rules used for `sys.path` also apply to a package’s `__path__` . `sys.path_hooks` (described below) are
consulted when traversing a package’s `__path__` .
A package’s `__init__.py` file may set or alter the package’s `__path__` attribute, and this was typically the way namespace packages were implemented
prior to [**PEP 420**](https://peps.python.org/pep-0420/) . With the adoption of [**PEP 420**](https://peps.python.org/pep-0420/) , namespace packages no
longer need to supply `__init__.py` files containing only `__path__` manipulation code; the import machinery automatically sets `__path__` correctly for the namespace package.

...

## 5.5. The Path Based Finder ¶
A word of warning: this section and the previous both use the term _finder_ ,
distinguishing between them by using the terms meta path finder and path entry finder . These two types of finders are very similar,
support similar protocols, and function in similar ways during the import
process, but it’s important to keep in mind that they are subtly different.
In particular, meta path finders operate at the beginning of the import
process, as keyed off the `sys.meta_path` traversal.
By contrast, path entry finders are in a sense an implementation detail
of the path based finder, and in fact, if the path based finder were to be
removed from `sys.meta_path` , none of the path entry finder semantics
would be invoked.

### 5.5.1. Path entry finders ¶
The path based finder is responsible for finding and loading
Python modules and packages whose location is specified with a string path entry . Most path entries name locations in the file system,
but they need not be limited to this.
As a meta path finder, the path based finder implements the `find_spec()` protocol previously
described, however it exposes additional hooks that can be used to
customize how modules are found and loaded from the import path .
Three variables are used by the path based finder , `sys.path` , `sys.path_hooks` and `sys.path_importer_cache` . The `__path__` attributes on package objects are also used. These provide additional ways
that the import machinery can be customized.
`sys.path` contains a list of strings providing search locations for
modules and packages. It is initialized from the `PYTHONPATH` environment variable and various other installation- and
implementation-specific defaults. Entries in `sys.path` can name
directories on the file system, zip files, and potentially other “locations”
(see the `site` module) that should be searched for modules, such as
URLs, or database queries. Only strings should be present on `sys.path` ; all other data types are ignored.
The path based finder is a meta path finder , so the import
machinery begins the import path search by calling the path
based finder’s `find_spec()` method as
described previously. When the `path` argument to `find_spec()` is given, it will be a
list of string paths to traverse - typically a package’s `__path__` attribute for an import within that package. If the `path` argument is `None` , this indicates a top level import and `sys.path` is used.
The path based finder iterates over every entry in the search path, and
for each of these, looks for an appropriate path entry finder ( `PathEntryFinder` ) for the
path entry. Because this can be an expensive operation (e.g. there may be `stat()` call overheads for this search), the path based finder maintains
a cache mapping path entries to path entry finders. This cache is maintained
in `sys.path_importer_cache` (despite the name, this cache actually
stores finder objects rather than being limited to importer objects).
In this way, the expensive search for a particular path entry location’s path entry finder need only be done once. User code is
free to remove cache entries from `sys.path_importer_cache` forcing
the path based finder to perform the path entry search again.

...

If `sys.path_hooks` iteration ends with no path entry finder being returned, then the path based finder’s `find_spec()` method will store `None` in `sys.path_importer_cache` (to indicate that there is no finder for
this path entry) and return `None` , indicating that this meta path finder could not find the module.
If a path entry finder _is_ returned by one of the path entry hook callables on `sys.path_hooks` , then the following protocol is used
to ask the finder for a module spec, which is then used when loading the
module.

...

### 5.5.2. Path entry finder protocol ¶
In order to support imports of modules and initialized packages and also to
contribute portions to namespace packages, path entry finders must implement
the `find_spec()` method.
`find_spec()` takes two arguments: the
fully qualified name of the module being imported, and the (optional) target
module. `find_spec()` returns a fully populated spec for the module.
This spec will always have “loader” set (with one exception).
To indicate to the import machinery that the spec represents a namespace portion , the path entry finder sets `submodule_search_locations` to
a list containing the portion.
Changed in version 3.4: `find_spec()` replaced `find_loader()` and `find_module()` , both of which
are now deprecated, but will be used if `find_spec()` is not defined.

...

The `find_module()` method on path entry finders is deprecated,
as it does not allow the path entry finder to contribute portions to
namespace packages. If both `find_loader()` and `find_module()` exist on a path entry finder, the import system will always call `find_loader()` in preference to `find_module()` .
Changed in version 3.10: Calls to `find_module()` and `find_loader()` by the import
system will raise `ImportWarning` .
Changed in version 3.12: `find_module()` and `find_loader()` have been removed.

...

## 5.9. References ¶
The import machinery has evolved considerably since Python’s early days. The
original [specification for packages](https://www.python.org/doc/essays/packages/) is still available to read,
although some details have changed since the writing of that document.
The original specification for `sys.meta_path` was [**PEP 302**](https://peps.python.org/pep-0302/) , with
subsequent extension in [**PEP 420**](https://peps.python.org/pep-0420/) .
[**PEP 420**](https://peps.python.org/pep-0420/) introduced namespace packages for
Python 3.3. [**PEP 420**](https://peps.python.org/pep-0420/) also introduced the `find_loader()` protocol as an
alternative to `find_module()` .
[**PEP 366**](https://peps.python.org/pep-0366/) describes the addition of the `__package__` attribute for
explicit relative imports in main modules.
```

**Tool Result:** `toolu_vrtx_01Lvovg5L7nDTM8L4fG8GYoZ`

```
# `importlib` — The implementation of `import` ¶
## Functions ¶
importlib. __import__ ( _name_ , _globals = None_ , _locals = None_ , _fromlist = ()_ , _level = 0_ ) ¶
An implementation of the built-in `__import__()` function.
Note
Programmatic importing of modules should use `import_module()` instead of this function.
importlib. import_module ( _name_ , _package = None_ ) ¶
Import a module. The _name_ argument specifies what module to
import in absolute or relative terms
(e.g. either `pkg.mod` or `..mod` ). If the name is
specified in relative terms, then the _package_ argument must be set to
the name of the package which is to act as the anchor for resolving the
package name (e.g. `import_module('..mod', 'pkg.subpkg')` will import `pkg.mod` ).
The `import_module()` function acts as a simplifying wrapper around `importlib.__import__()` . This means all semantics of the function are
derived from `importlib.__import__()` . The most important difference
between these two functions is that `import_module()` returns the
specified package or module (e.g. `pkg.mod` ), while `__import__()` returns the top-level package or module (e.g. `pkg` ).
If you are dynamically importing a module that was created since the
interpreter began execution (e.g., created a Python source file), you may
need to call `invalidate_caches()` in order for the new module to be
noticed by the import system.
Changed in version 3.3: Parent packages are automatically imported.

...

## `importlib.abc` – Abstract base classes related to import ¶
**Source code:** [Lib/importlib/abc.py](https://github.com/python/cpython/tree/3.14/Lib/importlib/abc.py)
The `importlib.abc` module contains all of the core abstract base classes
used by `import` . Some subclasses of the core abstract base classes
are also provided to help in implementing the core ABCs.
ABC hierarchy:
```
object 
 +-- MetaPathFinder 
 +-- PathEntryFinder 
 +-- Loader 
      +-- ResourceLoader --------+ 
      +-- InspectLoader          | 
           +-- ExecutionLoader --+ 
                                 +-- FileLoader 
                                 +-- SourceLoader
```
_class_ importlib.abc. MetaPathFinder ¶
An abstract base class representing a meta path finder .
Added in version 3.3.
Changed in version 3.10: No longer a subclass of `Finder` .
find_spec ( _fullname_ , _path_ , _target = None_ ) ¶
An abstract method for finding a spec for
the specified module. If this is a top-level import, _path_ will
be `None` . Otherwise, this is a search for a subpackage or
module and _path_ will be the value of `__path__` from the
parent package. If a spec cannot be found, `None` is returned.
When passed in, `target` is a module object that the finder may
use to make a more educated guess about what spec to return. `importlib.util.spec_from_loader()` may be useful for implementing
concrete `MetaPathFinders` .
Added in version 3.4.
invalidate_caches ( ) ¶
An optional method which, when called, should invalidate any internal
cache used by the finder. Used by `importlib.invalidate_caches()` when invalidating the caches of all finders on `sys.meta_path` .
Changed in version 3.4: Returns `None` when called instead of `NotImplemented` .
_class_ importlib.abc. PathEntryFinder ¶
An abstract base class representing a path entry finder . Though
it bears some similarities to `MetaPathFinder` , `PathEntryFinder` is meant for use only within the path-based import subsystem provided
by `importlib.machinery.PathFinder` .
Added in version 3.3.
Changed in version 3.10: No longer a subclass of `Finder` .
find_spec ( _fullname_ , _target = None_ ) ¶
An abstract method for finding a spec for
the specified module. The finder will search for the module only
within the path entry to which it is assigned. If a spec
cannot be found, `None` is returned. When passed in, `target` is a module object that the finder may use to make a more educated
guess about what spec to return. `importlib.util.spec_from_loader()` may be useful for implementing concrete `PathEntryFinders` .
Added in version 3.4.
invalidate_caches ( ) ¶
An optional method which, when called, should invalidate any internal
cache used by the finder. Used by `importlib.machinery.PathFinder.invalidate_caches()` when invalidating the caches of all cached finders.
_class_ importlib.abc. Loader ¶
An abstract base class for a loader .
See [**PEP 302**](https://peps.python.org/pep-0302/) for the exact definition for a loader.
Loaders that wish to support resource reading should implement a `get_resource_reader()` method as specified by `importlib.resources.abc.ResourceReader` .
Changed in version 3.7: Introduced the optional `get_resource_reader()` method.
create_module ( _spec_ ) ¶
A method that returns the module object to use when
importing a module. This method may return `None` ,
indicating that default module creation semantics should take place.
Added in version 3.4.

...

Changed in version 3.4: Raise `ImportError` when called instead of `NotImplementedError` . Functionality provided when `exec_module()` is available.
Deprecated since version 3.4, will be removed in version 3.15: The recommended API for loading a module is `exec_module()` (and `create_module()` ). Loaders should implement it instead of `load_module()` . The import machinery takes care of all the
other responsibilities of `load_module()` when `exec_module()` is implemented.
_class_ importlib.abc. ResourceLoader ¶
_Superseded by TraversableResources_

...

## `importlib.machinery` – Importers and path hooks ¶
Only class methods are defined by this class to alleviate the need for
instantiation.
Changed in version 3.5: As part of [**PEP 489**](https://peps.python.org/pep-0489/) , the builtin importer now implements `Loader.create_module()` and `Loader.exec_module()`
_class_ importlib.machinery. FrozenImporter ¶
An importer for frozen modules. This class implements the `importlib.abc.MetaPathFinder` and `importlib.abc.InspectLoader` ABCs.
Only class methods are defined by this class to alleviate the need for
instantiation.
Changed in version 3.4: Gained `create_module()` and `exec_module()` methods.
_class_ importlib.machinery. WindowsRegistryFinder ¶
Finder for modules declared in the Windows registry. This class
implements the `importlib.abc.MetaPathFinder` ABC.
Only class methods are defined by this class to alleviate the need for
instantiation.
Added in version 3.3.
Deprecated since version 3.6: Use `site` configuration instead. Future versions of Python may
not enable this finder by default.
_class_ importlib.machinery. PathFinder ¶
A Finder for `sys.path` and package `__path__` attributes.
This class implements the `importlib.abc.MetaPathFinder` ABC.
Only class methods are defined by this class to alleviate the need for
instantiation.

...

_classmethod_ invalidate_caches ( ) ¶
Calls `importlib.abc.PathEntryFinder.invalidate_caches()` on all
finders stored in `sys.path_importer_cache` that define the method.
Otherwise entries in `sys.path_importer_cache` set to `None` are
deleted.
Changed in version 3.7: Entries of `None` in `sys.path_importer_cache` are deleted.
Changed in version 3.4: Calls objects in `sys.path_hooks` with the current working
directory for `''` (i.e. the empty string).
_class_ importlib.machinery. FileFinder ( _path_ , _* loader_details_ ) ¶
A concrete implementation of `importlib.abc.PathEntryFinder` which
caches results from the file system.
The _path_ argument is the directory for which the finder is in charge of
searching.

...

path ¶
The path the finder will search in.
find_spec ( _fullname_ , _target = None_ ) ¶
Attempt to find the spec to handle _fullname_ within `path` .
Added in version 3.4.
invalidate_caches ( ) ¶
Clear out the internal cache.
_classmethod_ path_hook ( _* loader_details_ ) ¶
A class method which returns a closure for use on `sys.path_hooks` .
An instance of `FileFinder` is returned by the closure using the
path argument given to the closure directly and _loader_details_ indirectly.
If the argument to the closure is not an existing directory, `ImportError` is raised.
_class_ importlib.machinery. SourceFileLoader ( _fullname_ , _path_ ) ¶
A concrete implementation of `importlib.abc.SourceLoader` by
subclassing `importlib.abc.FileLoader` and providing some concrete
implementations of other methods.
Added in version 3.3.
name ¶
The name of the module that this loader will handle.
path ¶
The path to the source file.
is_package ( _fullname_ ) ¶
Return `True` if `path` appears to be for a package.
path_stats ( _path_ ) ¶
Concrete implementation of `importlib.abc.SourceLoader.path_stats()` .
set_data ( _path_ , _data_ ) ¶
Concrete implementation of `importlib.abc.SourceLoader.set_data()` .
load_module ( _name = None_ ) ¶
Concrete implementation of `importlib.abc.Loader.load_module()` where
specifying the name of the module to load is optional.
Deprecated since version 3.6, will be removed in version 3.15: Use `importlib.abc.Loader.exec_module()` instead.
_class_ importlib.machinery. SourcelessFileLoader ( _fullname_ , _path_ ) ¶
A concrete implementation of `importlib.abc.FileLoader` which can
import bytecode files (i.e. no source code files exist).

...

_class_ importlib.machinery. ExtensionFileLoader ( _fullname_ , _path_ ) ¶
A concrete implementation of `importlib.abc.ExecutionLoader` for
extension modules.
The _fullname_ argument specifies the name of the module the loader is to
support. The _path_ argument is the path to the extension module’s file.
Note that, by default, importing an extension module will fail
in subinterpreters if it doesn’t implement multi-phase init
(see [**PEP 489**](https://peps.python.org/pep-0489/) ), even if it would otherwise import successfully.
Added in version 3.3.
Changed in version 3.12: Multi-phase init is now required for use in subinterpreters.
name ¶
Name of the module the loader supports.
path ¶
Path to the extension module.
create_module ( _spec_ ) ¶
Creates the module object from the given specification in accordance
with [**PEP 489**](https://peps.python.org/pep-0489/) .
Added in version 3.5.

...

When a module is loaded with this loader, the `__file__` for the module
will report as the location of the `.fwork` file. This allows code to use
the `__file__` of a module as an anchor for file system traversal.
However, the spec origin will reference the location of the _actual_ binary
in the `.framework` folder.
The Xcode project building the app is responsible for converting any `.so` files from wherever they exist in the `PYTHONPATH` into frameworks in the `Frameworks` folder (including stripping extensions from the module file,
the addition of framework metadata, and signing the resulting framework),
and creating the `.fwork` and `.origin` files. This will usually be done
with a build step in the Xcode project; see the iOS documentation for
details on how to construct this build step.
Added in version 3.13.
Availability : iOS.
name ¶
Name of the module the loader supports.

...

## `importlib.util` – Utility code for importers ¶
importlib.util. find_spec ( _name_ , _package = None_ ) ¶
Find the spec for a module, optionally relative to
the specified **package** name. If the module is in `sys.modules` ,
then `sys.modules[name].__spec__` is returned (unless the spec would be `None` or is not set, in which case `ValueError` is raised).
Otherwise a search using `sys.meta_path` is done. `None` is
returned if no spec is found.
If **name** is for a submodule (contains a dot), the parent module is
automatically imported.
**name** and **package** work the same as for `import_module()` .
Added in version 3.4.
Changed in version 3.7: Raises `ModuleNotFoundError` instead of `AttributeError` if **package** is in fact not a package (i.e. lacks a `__path__` attribute).
importlib.util. module_from_spec ( _spec_ ) ¶
Create a new module based on **spec** and `spec.loader.create_module` .
If `spec.loader.create_module` does not return `None` , then any pre-existing attributes will not be reset.
Also, no `AttributeError` will be raised if triggered while accessing **spec** or setting an attribute on the module.
This function is preferred over using `types.ModuleType` to create a
new module as **spec** is used to set as many import-controlled attributes on
the module as possible.
Added in version 3.5.
importlib.util. spec_from_loader ( _name_ , _loader_ , _*_ , _origin = None_ , _is_package = None_ ) ¶
A factory function for creating a `ModuleSpec` instance based on a loader. The parameters have the same meaning as they do
for ModuleSpec. The function uses available loader APIs, such as `InspectLoader.is_package()` , to fill in any missing
information on the spec.
Added in version 3.4.
importlib.util. spec_from_file_location ( _name_ , _location_ , _*_ , _loader = None_ , _submodule_search_locations = None_ ) ¶
A factory function for creating a `ModuleSpec` instance based on the path to a file. Missing information will be filled in
on the spec by making use of loader APIs and by the implication that the
module will be file-based.
Added in version 3.4.
Changed in version 3.6: Accepts a path-like object .
importlib.util. source_hash ( _source_bytes_ ) ¶
Return the hash of _source_bytes_ as bytes. A hash-based `.pyc` file embeds
the `source_hash()` of the corresponding source file’s contents in its
header.
Added in version 3.7.

...

```
suffixes = importlib . machinery . SOURCE_SUFFIXES 
 loader = importlib . machinery . SourceFileLoader 
 lazy_loader = importlib . util . LazyLoader . factory ( loader ) 
 finder = importlib . machinery . FileFinder ( path , ( lazy_loader , suffixes ))
```

## Examples ¶
### Importing programmatically ¶
To programmatically import a module, use `importlib.import_module()` .
```
import importlib 

 itertools = importlib . import_module ( 'itertools' )
```

### Checking if a module can be imported ¶
If you need to find out if a module can be imported without actually doing the
import, then you should use `importlib.util.find_spec()` .
Note that if `name` is a submodule (contains a dot), `importlib.util.find_spec()` will import the parent module.
```
import importlib.util 
 import sys 

 # For illustrative purposes. 
 name = 'itertools' 

 if name in sys . modules : 
    print ( f " { name !r} already in sys.modules" ) 
 elif ( spec := importlib . util . find_spec ( name )) is not None : 
    # If you chose to perform the actual import ... 
    module = importlib . util . module_from_spec ( spec ) 
    sys . modules [ name ] = module 
    spec . loader . exec_module ( module ) 
    print ( f " { name !r} has been imported" ) 
 else : 
    print ( f "can't find the { name !r} module" )
```

...

### Setting up an importer ¶
```
import importlib.machinery 
 import sys 

 # For illustrative purposes only. 
 SpamMetaPathFinder = importlib . machinery . PathFinder 
 SpamPathEntryFinder = importlib . machinery . FileFinder 
 loader_details = ( importlib . machinery . SourceFileLoader , 
                  importlib . machinery . SOURCE_SUFFIXES ) 

 # Setting up a meta path finder. 
 # Make sure to put the finder in the proper location in the list in terms of 
 # priority. 
 sys . meta_path . append ( SpamMetaPathFinder ) 

 # Setting up a path entry finder. 
 # Make sure to put the path hook in the proper location in the list in terms 
 # of priority. 
 sys . path_hooks . append ( SpamPathEntryFinder . path_hook ( loader_details ))
```

### Approximating `importlib.import_module()` ¶
Import itself is implemented in Python code, making it possible to
expose most of the import machinery through importlib. The following
helps illustrate the various APIs that importlib exposes by providing an
approximate implementation of `importlib.import_module()` :
```
import importlib.util 
 import sys 

 def import_module ( name , package = None ): 
 """An approximate implementation of import.""" 
    absolute_name = importlib . util . resolve_name ( name , package ) 
    try : 
        return sys . modules [ absolute_name ] 
    except KeyError : 
        pass 

    path = None 
    if '.' in absolute_name : 
        parent_name , _ , child_name = absolute_name . rpartition ( '.' ) 
        parent_module = import_module ( parent_name ) 
        path = parent_module . __spec__ . submodule_search_locations 
    for finder in sys . meta_path : 
        spec = finder . find_spec ( absolute_name , path ) 
        if spec is not None : 
            break 
    else : 
        msg = f 'No module named { absolute_name !r} ' 
        raise ModuleNotFoundError ( msg , name = absolute_name ) 
    module = importlib . util . module_from_spec ( spec ) 
    sys . modules [ absolute_name ] = module 
    spec . loader . exec_module ( module ) 
    if path is not None : 
        setattr ( parent_module , child_name , module ) 
    return module
```
© Copyright 2001 Python Software Foundation.
This page is licensed under the Python Software Foundation License Version 2.
Examples, recipes, and other code in the documentation are additionally licensed under the Zero Clause BSD License.
See History and License for more information.
The Python Software Foundation is a non-profit corporation. [Please donate.](https://www.python.org/psf/donations/)
Last updated on May 13, 2026 (18:02 UTC). Found a bug ?
Created using [Sphinx](https://www.sphinx-doc.org/) 8.2.3.
*[*]: Keyword-only parameters separator (PEP 3102)
```

## Assistant

## The Python Import Process for `import namespacepackage.subpackage.module`

Below is a step‑by‑step walk through what the interpreter does, with direct references to the [language reference (§5 The import system)](https://docs.python.org/3/reference/import.html) and the [`importlib`](https://docs.python.org/3/library/importlib.html) library docs. The same machinery handles every dotted name; the differences appear only at the *finder/loader* stage depending on whether each segment turns out to be a regular package, a namespace package, a source module, an extension module, a frozen module, etc.

---

### 1. The `import` statement compiles to a call to `__import__`

The compiler turns `import namespacepackage.subpackage.module` into bytecode that calls the built‑in [`__import__()`](https://docs.python.org/3/library/functions.html#import__) with `name='namespacepackage.subpackage.module'` and `fromlist=()`, then performs a *name binding* of the **top‑level** name (`namespacepackage`) into the current namespace. This is the bit emphasized at the very top of [§5](https://docs.python.org/3/reference/import.html):

> A direct call to `__import__()` performs only the module search and, if found, the module creation operation. While certain side‑effects may occur, such as the importing of parent packages, and the updating of various caches (including `sys.modules`), only the `import` statement performs a name binding operation.

That is why, after `import a.b.c`, you have `a` bound locally but can still write `a.b.c.foo` — the submodules are reached through attribute access on the parent packages (see [§5.4.2 Submodules](https://docs.python.org/3/reference/import.html#submodules)). Contrast this with [`importlib.import_module()`](https://docs.python.org/3/library/importlib.html#importlib.import_module), which returns the *leaf* module instead of the top‑level one.

`__import__` is implemented in pure Python in `importlib._bootstrap` (the [`importlib`](https://docs.python.org/3/library/importlib.html) intro paragraph notes this is "the implementation of `import`").

---

### 2. The dotted name is split and imported left‑to‑right

Per [§5.3 Searching](https://docs.python.org/3/reference/import.html#searching):

> This name will be used in various phases of the import search, and it may be the dotted path to a submodule, e.g. `foo.bar.baz`. In this case, Python first tries to import `foo`, then `foo.bar`, and finally `foo.bar.baz`. If any of the intermediate imports fail, a `ModuleNotFoundError` is raised.

So three import operations happen in order:

1. `namespacepackage`
2. `namespacepackage.subpackage`
3. `namespacepackage.subpackage.module`

The pseudo‑implementation at the bottom of the [`importlib` docs ("Approximating `importlib.import_module()`")](https://docs.python.org/3/library/importlib.html#approximating-importlib-import-module) makes this recursion explicit:

```python
parent_name, _, child_name = absolute_name.rpartition('.')
parent_module = import_module(parent_name)
path = parent_module.__spec__.submodule_search_locations
```

The crucial output of importing a parent is its `__spec__.submodule_search_locations` (mirrored as the package's `__path__`), which becomes the search path for the next segment.

---

### 3. For each segment: check `sys.modules` first

[§5.3.1 The module cache](https://docs.python.org/3/reference/import.html#the-module-cache):

> The first place checked during import search is `sys.modules`. […] So if `foo.bar.baz` was previously imported, `sys.modules` will contain entries for `foo`, `foo.bar`, and `foo.bar.baz`.

Behavior:

- **Hit** → that module object is used and the search ends for this segment.
- **Value is `None`** → `ModuleNotFoundError` is raised (this is how packages can poison a name).
- **Miss** → the finder/loader protocol kicks in.

This cache is also why a partially‑initialized module can be observed by code that imports it during its own `exec_module` (see [§5.4 Loading](https://docs.python.org/3/reference/import.html#loading)).

---

### 4. Run the meta path finders (`sys.meta_path`)

[§5.3.4 The meta path](https://docs.python.org/3/reference/import.html#the-meta-path):

> When the named module is not found in `sys.modules`, Python next searches `sys.meta_path`, which contains a list of meta path finder objects. These finders are queried in order […] Meta path finders must implement a method called `find_spec()` which takes three arguments: a name, an import path, and (optionally) a target module.

For each segment Python iterates `sys.meta_path` calling

```python
spec = finder.find_spec(fullname, path, target=None)
```

where:

- `fullname` is the full dotted name (`'namespacepackage'`, then `'namespacepackage.subpackage'`, then `'namespacepackage.subpackage.module'`).
- `path` is **`None` for a top‑level import** (segment 1) and **the parent package's `__path__`** for subsequent segments (segments 2 and 3). This is exactly the part of [§5.3.4](https://docs.python.org/3/reference/import.html#the-meta-path) that says: *"For top‑level modules, the second argument is `None`, but for submodules or subpackages, the second argument is the value of the parent package's `__path__` attribute."*

The default `sys.meta_path` (described in [`importlib.machinery`](https://docs.python.org/3/library/importlib.html#module-importlib.machinery)) contains, in order:

1. [`BuiltinImporter`](https://docs.python.org/3/library/importlib.html#importlib.machinery.BuiltinImporter) — handles built‑in C modules like `sys`, `_io`.
2. [`FrozenImporter`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FrozenImporter) — handles modules whose bytecode is frozen into the interpreter (e.g. `_frozen_importlib` itself, much of `importlib`, and many stdlib modules in 3.11+).
3. [`PathFinder`](https://docs.python.org/3/library/importlib.html#importlib.machinery.PathFinder) — the **path‑based finder** that searches `sys.path` (top level) or the parent's `__path__` (sub‑levels).

The first finder that returns a non‑`None` `ModuleSpec` wins. If none returns a spec, `ModuleNotFoundError` is raised — see [§5.3.4](https://docs.python.org/3/reference/import.html#the-meta-path).

For our example, `namespacepackage` is almost certainly not built‑in or frozen, so all three segments end up at `PathFinder`.

---

### 5. The path‑based finder ([§5.5](https://docs.python.org/3/reference/import.html#the-path-based-finder))

`PathFinder.find_spec(fullname, path, target)` does the following — see [§5.5 The Path Based Finder](https://docs.python.org/3/reference/import.html#the-path-based-finder) and [§5.5.1 Path entry finders](https://docs.python.org/3/reference/import.html#path-entry-finders):

1. **Pick the search list**: `sys.path` for the top‑level import, otherwise the supplied `path` (the parent package's `__path__`).
2. **For each entry in that list**, look up a path entry finder in [`sys.path_importer_cache`](https://docs.python.org/3/library/sys.html#sys.path_importer_cache).
3. If the entry isn't cached, walk [`sys.path_hooks`](https://docs.python.org/3/library/sys.html#sys.path_hooks) calling each hook with the path entry. The first hook that doesn't raise `ImportError` returns a path entry finder (typically a [`FileFinder`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FileFinder) for a directory, or a `zipimporter` for a `.zip`/`.whl`). The result is cached in `sys.path_importer_cache` (the docs explicitly note: *"despite the name, this cache actually stores finder objects rather than being limited to importer objects."*).
4. Call `path_entry_finder.find_spec(fullname, target)`.

`FileFinder` is the workhorse for files on disk. It is constructed with `(SourceFileLoader, SOURCE_SUFFIXES)`, `(SourcelessFileLoader, BYTECODE_SUFFIXES)`, and `(ExtensionFileLoader, EXTENSION_SUFFIXES)` (see the example at the bottom of [`importlib.machinery`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FileFinder.path_hook) and [§5.5.1](https://docs.python.org/3/reference/import.html#path-entry-finders)). For a single name (say `subpackage`) inside a directory `D`, it looks for, in order:

- `D/subpackage/__init__.py` (or `.pyc` / `.so`) → **regular package** ([§5.2.1 Regular packages](https://docs.python.org/3/reference/import.html#regular-packages))
- `D/subpackage.py`, `D/subpackage.pyc`, `D/subpackage.{abi}.so`, etc. → **module**
- `D/subpackage/` with **no** `__init__.*` → records a **namespace portion** ([§5.5.2 Path entry finder protocol](https://docs.python.org/3/reference/import.html#path-entry-finder-protocol)):

  > To indicate to the import machinery that the spec represents a namespace portion, the path entry finder sets `submodule_search_locations` to a list containing the portion.

#### How namespace packages are assembled

When `PathFinder` finishes iterating every entry of `sys.path` (or the parent's `__path__`):

- If any entry produced a real spec with a loader → that wins immediately.
- Otherwise, if one or more entries produced **only** namespace portions → `PathFinder` fabricates a single `ModuleSpec` whose `loader is None`, `origin is None`, and `submodule_search_locations` is the concatenation of all those portions. That is the namespace package described in [§5.2.2 Namespace packages](https://docs.python.org/3/reference/import.html#namespace-packages):

  > A namespace package is a composite of various portions, where each portion contributes a subpackage to the parent package. Portions may reside in different locations on the file system. […] With namespace packages, there is no `parent/__init__.py` file. In fact, there may be multiple `parent` directories found during import search […].

The same section also explains why a namespace package's `__path__` isn't an ordinary list — it's a custom iterable that re‑scans on every subsequent import:

> Namespace packages do not use an ordinary list for their `__path__` attribute. They instead use a custom iterable type which will automatically perform a new search for package portions on the next import attempt within that package if the path of their parent package (or `sys.path` for a top level package) changes.

That's the [`_NamespacePath`](https://docs.python.org/3/library/importlib.html#importlib.machinery.PathFinder) object, and it's the mechanism that lets `boldi.backup`, `boldi.dotmodpath`, `boldi.webalbum`, etc. live in completely separate `pkg/boldi-*/` directories yet still appear as one `boldi` package — because there is no `boldi/__init__.py` anywhere.

---

### 6. Loading: turn the spec into a module ([§5.4](https://docs.python.org/3/reference/import.html#loading))

Once a spec has been obtained, the loading protocol from [§5.4 Loading](https://docs.python.org/3/reference/import.html#loading) runs. The exact pseudocode in the docs is:

```python
module = None
if spec.loader is not None and hasattr(spec.loader, 'create_module'):
    module = spec.loader.create_module(spec)
if module is None:
    module = ModuleType(spec.name)
_init_module_attrs(spec, module)

if spec.loader is None:
    raise ImportError
if spec.origin is None and spec.submodule_search_locations is not None:
    # namespace package
    sys.modules[spec.name] = module
elif not hasattr(spec.loader, 'exec_module'):
    module = spec.loader.load_module(spec.name)
else:
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        try:
            del sys.modules[spec.name]
        except KeyError:
            pass
```

Important properties from the same section:

- *"The module will exist in `sys.modules` before the loader executes the module code"* — preventing infinite recursion on circular imports.
- *"If loading fails, the failing module — and only the failing module — gets removed from `sys.modules`."*
- `_init_module_attrs` sets `__name__`, `__loader__`, `__spec__`, `__package__`, `__path__` (for packages), `__file__` (when applicable), etc., as summarised in [§5.4.4 `__path__` attributes on modules](https://docs.python.org/3/reference/import.html#path__-attributes-on-modules) and the "module attributes" sub‑section.

The branching above is exactly where the differences between module *kinds* show up:

| Kind | Loader | What `exec_module` does |
|---|---|---|
| Built‑in (e.g. `sys`) | [`BuiltinImporter`](https://docs.python.org/3/library/importlib.html#importlib.machinery.BuiltinImporter) | C `PyInit_<name>` (multi‑phase init, [PEP 489](https://peps.python.org/pep-0489/)) |
| Frozen | [`FrozenImporter`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FrozenImporter) | execute the embedded marshalled bytecode |
| Source `.py` | [`SourceFileLoader`](https://docs.python.org/3/library/importlib.html#importlib.machinery.SourceFileLoader) | read source, compare with cached `.pyc`, compile if needed, write `.pyc`, exec bytecode in `module.__dict__` |
| Bytecode‑only `.pyc` | [`SourcelessFileLoader`](https://docs.python.org/3/library/importlib.html#importlib.machinery.SourcelessFileLoader) | exec the cached bytecode |
| Extension `.so`/`.pyd` | [`ExtensionFileLoader`](https://docs.python.org/3/library/importlib.html#importlib.machinery.ExtensionFileLoader) | `dlopen` and run `PyInit_<name>` |
| **Regular package** | `SourceFileLoader` for `__init__.py` | execute `__init__.py`; `__path__` is set from the package directory |
| **Namespace package** | `loader is None` (note the special branch in the pseudocode that just stores the module in `sys.modules` without executing anything) | nothing to execute; `__file__` is **not** set; `__path__` is the magic `_NamespacePath` |

This is the only really meaningful behavioural difference between the package types from the language spec's point of view. Per [§5.2.1](https://docs.python.org/3/reference/import.html#regular-packages):

> A regular package is typically implemented as a directory containing an `__init__.py` file. When a regular package is imported, this `__init__.py` file is implicitly executed, and the objects it defines are bound to names in the package's namespace.

…versus [§5.2.2](https://docs.python.org/3/reference/import.html#namespace-packages) for namespace packages, plus the no‑exec branch in the §5.4 pseudocode.

---

### 7. After loading: bind the submodule on the parent

[§5.4.2 Submodules](https://docs.python.org/3/reference/import.html#submodules) states the invariant:

> if you have `sys.modules['spam']` and `sys.modules['spam.foo']` (as you would after the above import), the latter must appear as the `foo` attribute of the former.

You can see this happen in the docs' approximation:

```python
if path is not None:
    setattr(parent_module, child_name, module)
```

So after step 4 finishes for `namespacepackage.subpackage`, the import machinery does `setattr(namespacepackage, 'subpackage', subpackage)`; after step 4 finishes for `namespacepackage.subpackage.module`, it does `setattr(subpackage, 'module', module)`.

---

### 8. Finally: name binding in the importing module

Returning to [§5 introduction](https://docs.python.org/3/reference/import.html): the `import` statement now binds the **top‑level** name (`namespacepackage`) in the current scope. Because of step 7, `namespacepackage.subpackage.module` is reachable via attribute access. Variants:

- `import a.b.c as x` → binds `x = sys.modules['a.b.c']` (the leaf).
- `from a.b import c` → imports `a`, `a.b`, then either retrieves `a.b.c` from `sys.modules` (after running the import machinery for it) or, if missing, falls back to `getattr(a.b, 'c')`. This is described in the "Submodules" and "The import statement" subsections of [§5](https://docs.python.org/3/reference/import.html).

---

### End‑to‑end timeline for our example

Assuming nothing is cached yet and `namespacepackage` is a PEP‑420 namespace package living in two `sys.path` entries, while `subpackage` is a regular package and `module` is a `.py` file:

```diagram
import namespacepackage.subpackage.module
        │
        ▼
__import__('namespacepackage.subpackage.module', ..., fromlist=())
        │
        ├── import 'namespacepackage'              (path=None  → sys.path)
        │     ├── sys.modules miss
        │     ├── meta_path: Builtin? Frozen? PathFinder ✓
        │     │     PathFinder iterates sys.path:
        │     │       entryA → FileFinder → no __init__, dir exists  → portion A
        │     │       entryB → FileFinder → no __init__, dir exists  → portion B
        │     │     → ModuleSpec(loader=None, submodule_search_locations=[A,B])
        │     ├── Loading: namespace branch → no exec_module
        │     └── sys.modules['namespacepackage'] = <namespace module>
        │
        ├── import 'namespacepackage.subpackage'   (path=namespacepackage.__path__)
        │     ├── sys.modules miss
        │     ├── meta_path → PathFinder
        │     │     iterates [A, B]:
        │     │       A/subpackage/__init__.py exists → SourceFileLoader spec
        │     ├── Loading: create_module + exec_module(__init__.py)
        │     ├── sys.modules['namespacepackage.subpackage'] = <pkg>
        │     └── setattr(namespacepackage, 'subpackage', <pkg>)
        │
        └── import 'namespacepackage.subpackage.module' (path=subpackage.__path__)
              ├── sys.modules miss
              ├── meta_path → PathFinder → FileFinder finds module.py
              ├── SourceFileLoader: read source, check __pycache__/module.cpython-XY.pyc,
              │     compile if stale, write .pyc, exec bytecode in module.__dict__
              ├── sys.modules['namespacepackage.subpackage.module'] = <module>
              └── setattr(subpackage, 'module', <module>)
        │
        ▼
import statement binds 'namespacepackage' in the local namespace.
```

---

### Summary of where the kinds differ

All segments traverse the same pipeline (`sys.modules` → `sys.meta_path` → spec → loading → parent‑attribute binding). The only kind‑dependent behaviour is the **finder result** and the **loading branch**:

- **Built‑in / frozen modules** are found by their dedicated meta‑path finders before `PathFinder` is even consulted ([§5.3.2 Finders and loaders](https://docs.python.org/3/reference/import.html#finders-and-loaders), [`importlib.machinery.BuiltinImporter`](https://docs.python.org/3/library/importlib.html#importlib.machinery.BuiltinImporter), [`FrozenImporter`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FrozenImporter)).
- **Regular packages** have an `__init__.py` whose `SourceFileLoader.exec_module` runs and whose directory becomes `__path__` ([§5.2.1](https://docs.python.org/3/reference/import.html#regular-packages)).
- **Namespace packages** have no loader and no code execution; their `__path__` is a self‑refreshing `_NamespacePath` aggregating every directory contributing a portion ([§5.2.2](https://docs.python.org/3/reference/import.html#namespace-packages), [§5.5.2](https://docs.python.org/3/reference/import.html#path-entry-finder-protocol), and the namespace‑package branch in the [§5.4](https://docs.python.org/3/reference/import.html#loading) pseudocode).
- **Source modules** go through compile + `.pyc` cache + `exec_module` via [`SourceFileLoader`](https://docs.python.org/3/library/importlib.html#importlib.machinery.SourceFileLoader); **bytecode‑only** modules use [`SourcelessFileLoader`](https://docs.python.org/3/library/importlib.html#importlib.machinery.SourcelessFileLoader); **C extensions** use [`ExtensionFileLoader`](https://docs.python.org/3/library/importlib.html#importlib.machinery.ExtensionFileLoader) which `dlopen`s the file and runs `PyInit_*` per [PEP 489](https://peps.python.org/pep-0489/).

The architectural framing of all of this — finders versus loaders, meta path versus path entry finders, specs as the unit of currency between them — is the topic of [§5.3.2 Finders and loaders](https://docs.python.org/3/reference/import.html#finders-and-loaders) and [§5.5](https://docs.python.org/3/reference/import.html#the-path-based-finder), and the executable Python form lives in [`importlib._bootstrap` and `importlib._bootstrap_external`](https://docs.python.org/3/library/importlib.html), exposed via [`importlib.abc`](https://docs.python.org/3/library/importlib.html#module-importlib.abc), [`importlib.machinery`](https://docs.python.org/3/library/importlib.html#module-importlib.machinery), and [`importlib.util`](https://docs.python.org/3/library/importlib.html#module-importlib.util).

## User

Review and critique boldi.dotmodpath in light of the above.

## Assistant

**Tool Use:** `Read`

```json
{
  "path": "/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/boldi/dotmodpath.py"
}
```

**Tool Use:** `Read`

```json
{
  "path": "/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/pyproject.toml"
}
```

## User

**Tool Result:** `toolu_vrtx_017RctNBM19r2CDwJuS4xQ4P`

```
{
  "content": "1: import importlib.machinery\n2: import importlib.metadata\n3: import importlib.util\n4: import os\n5: import sys\n6: from collections.abc import Sequence\n7: from importlib.abc import MetaPathFinder\n8: from pathlib import Path\n9: \n10: ENTRY_POINT_GROUP = \"boldi.dotmodpath\"\n11: FINDER: \"DottedModuleNameFinder | None\" = None\n12: \n13: \n14: def install() -> \"DottedModuleNameFinder\":\n15:     \"\"\"Install the importer and register prefixes advertised by entry points.\"\"\"\n16:     global FINDER\n17: \n18:     if FINDER is None:\n19:         FINDER = DottedModuleNameFinder()\n20:         try:\n21:             path_finder_index = sys.meta_path.index(importlib.machinery.PathFinder)\n22:             sys.meta_path.insert(path_finder_index + 1, FINDER)\n23:         except ValueError:\n24:             sys.meta_path.append(FINDER)\n25: \n26:     # Entry point names are the import prefixes that may use dotted filenames.\n27:     for entry_point in importlib.metadata.entry_points(group=ENTRY_POINT_GROUP):\n28:         FINDER.register_prefix(entry_point.name)\n29: \n30:     return FINDER\n31: \n32: \n33: def mark_as_package(module_name: str) -> None:\n34:     \"\"\"Mark a dotted-file module as package-like so it can have submodules.\"\"\"\n35:     module = sys.modules[module_name]\n36:     module_file = getattr(module, \"__file__\", None)\n37:     if module_file is None:\n38:         raise ValueError(f\"{module_name!r} has no __file__\")\n39: \n40:     # A dotted-file module can opt into having submodules by setting __path__.\n41:     module.__path__ = [str(Path(module_file).parent)]\n42:     if module.__spec__:\n43:         module.__spec__.submodule_search_locations = module.__path__\n44: \n45: \n46: class DottedModuleNameFinder(MetaPathFinder):\n47:     def __init__(self) -> None:\n48:         self.prefixes: set[str] = set()\n49: \n50:     def register_prefix(self, prefix: str) -> None:\n51:         self.prefixes.add(prefix)\n52: \n53:     def find_spec(self, fullname: str, path: Sequence[str] | None = None, target=None):\n54:         for prefix in sorted(self.prefixes, key=len, reverse=True):\n55:             if fullname != prefix and not fullname.startswith(f\"{prefix}.\"):\n56:                 continue\n57: \n58:             # For prefix \"boldi.dotmodpath\", search under the \"boldi\" package\n59:             # for files named like \"dotmodpath.foo.py\".\n60:             anchor = prefix.rpartition(\".\")[0]\n61:             tail = fullname[len(anchor) + 1 :] if anchor else fullname\n62:             module_file = f\"{tail}.py\"\n63: \n64:             for root in self._roots(path, anchor):\n65:                 file = root / module_file\n66:                 if file.is_file():\n67:                     return importlib.util.spec_from_file_location(fullname, file)\n68: \n69:         return None\n70: \n71:     @staticmethod\n72:     def _roots(path: Sequence[str] | None, anchor: str) -> tuple[Path, ...]:\n73:         if path is not None:\n74:             # Submodule imports search inside the parent package's __path__.\n75:             return tuple(root for entry in path if (root := Path(entry or os.getcwd())).is_dir())\n76: \n77:         # Prefix imports search for the prefix anchor on sys.path.\n78:         anchor_path = Path(*anchor.split(\".\")) if anchor else Path()\n79:         return tuple(root for entry in sys.path if (root := Path(entry or os.getcwd()) / anchor_path).is_dir())",
  "absolutePath": "/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/boldi/dotmodpath.py"
}
```

**Tool Result:** `toolu_vrtx_01ELQZzAwGqyPFxpEADjjTG9`

```
{
  "content": "1: [project]\n2: name = \"boldi-dotmodpath\"\n3: description = \"boldi.dotmodpath part of Boldi's Python libraries\"\n4: authors = [\n5:     { name = \"Boldizsár Palotás\", email = \"boldizsar.palotas@gmail.com\" },\n6: ]\n7: requires-python = \">=3.12\"\n8: readme = \"README.md\"\n9: license = { text = \"MIT\" }\n10: dynamic = [\"version\"]\n11: \n12: dependencies = []\n13: optional-dependencies = {}\n14: \n15: [build-system]\n16: requires = [\"hatchling\", \"hatch-vcs\"]\n17: build-backend = \"hatchling.build\"\n18: \n19: [tool.hatch.build]\n20: packages = [\"boldi\"]\n21: \n22: [tool.hatch.build.targets.sdist.force-include]\n23: \"boldi-dotmodpath.pth\" = \"boldi-dotmodpath.pth\"\n24: \"hatch_hooks.py\" = \"hatch_hooks.py\"\n25: \n26: [tool.hatch.build.targets.wheel.force-include]\n27: \"boldi-dotmodpath.pth\" = \"boldi-dotmodpath.pth\"\n28: \n29: [tool.hatch.build.hooks.vcs]\n30: version-file = \"boldi/_dotmodpath_version.py\"\n31: \n32: [tool.hatch.metadata.hooks.custom]\n33: path = \"hatch_hooks.py\"\n34: \n35: [tool.hatch.version]\n36: source = \"vcs\"\n37: raw-options = { \"root\" = \"../..\" }",
  "absolutePath": "/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/pyproject.toml"
}
```

## Assistant

**Tool Use:** `Bash`

```json
{
  "cmd": "ls /Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/"
}
```

**Tool Use:** `Bash`

```json
{
  "cmd": "cat /Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/boldi-dotmodpath.pth /Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/README.md 2>/dev/null"
}
```

**Tool Use:** `Bash`

```json
{
  "cmd": "rg -n \"boldi.dotmodpath\" /Users/palotasb/Dropbox/Projects/boldi-python --type toml --type py -g '!**/_dotmodpath_version.py'"
}
```

## User

**Tool Result:** `toolu_vrtx_018jQGSuqzgQYh55pAbkQmyd`

```
{
  "output": "__pycache__\nboldi\nboldi-dotmodpath.pth\nhatch_hooks.py\npyproject.toml\nREADME.md\ntests\n",
  "exitCode": 0
}
```

**Tool Result:** `toolu_vrtx_011ZLqJdfQ5hghEyAbFfzreP`

```
{
  "output": "import boldi.dotmodpath; boldi.dotmodpath.install()\n# boldi-dotmodpath\n\nDotted module path importer for Boldi's Python libraries.\n",
  "exitCode": 0
}
```

**Tool Result:** `toolu_vrtx_01BrjsffzPDtTKtCMfdbp66F`

```
{
  "output": "/Users/palotasb/Dropbox/Projects/boldi-python/pyproject.toml:19:    \"boldi-dotmodpath\",\n/Users/palotasb/Dropbox/Projects/boldi-python/pyproject.toml:56:boldi-dotmodpath = { workspace = true }\n/Users/palotasb/Dropbox/Projects/boldi-python/pyproject.toml:72:    \"pkg/boldi-dotmodpath\",\n/Users/palotasb/Dropbox/Projects/boldi-python/pyproject.toml:101:    \"boldi.dotmodpath\",\n/Users/palotasb/Dropbox/Projects/boldi-python/pyproject.toml:109:mypy_path = \"pkg/boldi:pkg/boldi-backup:pkg/boldi-build:pkg/boldi-cli:pkg/boldi-ctx:pkg/boldi-dotmodpath:pkg/boldi-githooks:pkg/boldi-plugins:pkg/boldi-proc:pkg/boldi-sitebuilder:pkg/boldi-webalbum:pkg/boldi-webalbum-app\"\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/boldi/dotmodpath.py:10:ENTRY_POINT_GROUP = \"boldi.dotmodpath\"\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/boldi/dotmodpath.py:58:            # For prefix \"boldi.dotmodpath\", search under the \"boldi\" package\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/pyproject.toml:2:name = \"boldi-dotmodpath\"\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/pyproject.toml:3:description = \"boldi.dotmodpath part of Boldi's Python libraries\"\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/pyproject.toml:23:\"boldi-dotmodpath.pth\" = \"boldi-dotmodpath.pth\"\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/pyproject.toml:27:\"boldi-dotmodpath.pth\" = \"boldi-dotmodpath.pth\"\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/tests/dmptest.py:1:from boldi.dotmodpath import mark_as_package\n/Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/tests/dmptest.foo.py:1:from boldi.dotmodpath import mark_as_package\n",
  "exitCode": 0
}
```

## Assistant

**Tool Use:** `Bash`

```json
{
  "cmd": "ls /Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/tests/"
}
```

**Tool Use:** `Bash`

```json
{
  "cmd": "cat /Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/tests/*.py /Users/palotasb/Dropbox/Projects/boldi-python/pkg/boldi-dotmodpath/hatch_hooks.py"
}
```

## User

**Tool Result:** `toolu_vrtx_015r3hXrWS1wXJY6NPGmGDax`

```
{
  "output": "__pycache__\ndmptest.foo.bar.py\ndmptest.foo.py\ndmptest.py\nnotregistered.foo.py\n",
  "exitCode": 0
}
```

**Tool Result:** `toolu_vrtx_013d4DG3KB3vbBoxQgyuCZeB`

```
{
  "output": "print(__file__)\nfrom boldi.dotmodpath import mark_as_package\n\nmark_as_package(__name__)\nprint(__file__)\nfrom boldi.dotmodpath import mark_as_package\n\nmark_as_package(__name__)\nprint(__file__)\nraise RuntimeError(\"notregistered.foo imported unexpectedly\")\nfrom pathlib import Path\n\nfrom hatch_vcs.version_source import VCSVersionSource\nfrom hatchling.metadata.plugin.interface import MetadataHookInterface\nfrom packaging.requirements import Requirement\n\n\ndef update_internal_dependencies(dependencies: list[str], version: str):\n    for i, dependency in enumerate(dependencies):\n        requirement = Requirement(dependency)\n        if requirement.name.startswith(\"boldi\"):\n            requirement.specifier &= f\"=={version}\"\n            dependencies[i] = str(requirement)\n\n\nclass CustomMetadataHook(MetadataHookInterface):\n    def __init__(self, root: str, config: dict) -> None:\n        super().__init__(root, config)\n\n    def update(self, metadata: dict) -> None:\n        version_source = VCSVersionSource(root=str(Path(self.root).parent.parent.resolve()), config={})\n        version = version_source.get_version_data()[\"version\"]\n        update_internal_dependencies(metadata.get(\"dependencies\", []), version)\n",
  "exitCode": 0
}
```

## Assistant

## Review: `boldi.dotmodpath`

### What it does (so the critique has context)

It installs a custom **meta path finder** (`DottedModuleNameFinder`) into `sys.meta_path` *after* `PathFinder`. For prefixes registered via the `boldi.dotmodpath` entry-point group, it allows files named with **dots in the filename itself** (e.g. `dmptest.foo.bar.py`) to be imported as if they were `dmptest.foo.bar`. `mark_as_package()` is a helper that retroactively sets `__path__` on such a flat file so it can have "submodules" (which are actually sibling files with longer dotted names).

It's a clever escape hatch — it lets you keep a single‑file module as a single file even after it grows submodules — but the implementation has a number of issues when measured against the Python import system docs ([§5](https://docs.python.org/3/reference/import.html), [`importlib`](https://docs.python.org/3/library/importlib.html)).

---

### 1. Parent-package importing is bypassed

Per [§5.3 Searching](https://docs.python.org/3/reference/import.html#searching):

> Python first tries to import `foo`, then `foo.bar`, and finally `foo.bar.baz`. If any of the intermediate imports fail, a `ModuleNotFoundError` is raised.

And [§5.4.2 Submodules](https://docs.python.org/3/reference/import.html#submodules):

> if you have `sys.modules['spam']` and `sys.modules['spam.foo']`, the latter must appear as the `foo` attribute of the former.

When `find_spec('dmptest.foo.bar', path=...)` matches a file `dmptest.foo.bar.py`, the finder returns a spec but never ensures that `dmptest.foo` actually exists or that the resulting module gets attached as `bar` on a parent. The dotted name is treated as a filename, not as a hierarchy. That breaks the invariant above:

- `sys.modules['dmptest.foo.bar']` may exist while `sys.modules['dmptest.foo']` does not (unless the user loaded it first).
- `dmptest.foo.bar` is **not** discoverable via attribute access on `dmptest.foo`.
- For the "prefix only" case (e.g. `import dmptest`) the finder hands the import machinery a single‑file spec with no `submodule_search_locations` — the whole reason for `mark_as_package` existing — but if a user does `import dmptest.foo.bar` first, no parent gets imported and `mark_as_package` was never given a chance to run.

This is a fundamental departure from the contract that `__import__` and `importlib.import_module` enforce, and it'll produce confusing failures when one user does `import dmptest.foo` and another does `from dmptest import foo` — the latter ultimately falls back to `getattr(dmptest, 'foo')` (per [§5: The import statement](https://docs.python.org/3/reference/import.html#the-import-statement)) and may not find it.

### 2. `path=` argument is ignored for sub‑imports of dotted files

[§5.3.4 The meta path](https://docs.python.org/3/reference/import.html#the-meta-path):

> For top-level modules, the second argument is `None`, but for submodules or subpackages, the second argument is the value of the parent package's `__path__` attribute.

In `_roots`, when `path is not None`, the code searches *that* path for `f"{tail}.py"`. But `tail` is computed from the prefix's *anchor*, not from the actual parent that triggered the recursion. Concrete failure mode:

- prefix = `"dmptest"`, anchor = `""` → for `import dmptest.foo.bar` triggered by parent `dmptest.foo` (whose `__path__` is `[…/tests]`), the finder looks for `dmptest.foo.bar.py` in `…/tests`. That happens to work because the parent's `__path__` points to the same directory, but only by coincidence.
- prefix = `"boldi.dotmodpath"`, anchor = `"boldi"` → for `import boldi.dotmodpath.x.y` triggered with `path = boldi.__path__`, `tail = "dotmodpath.x.y"`. The finder looks for `dotmodpath.x.y.py` directly under each `boldi/` portion. Fine in principle, but the `prefix == fullname` / `startswith(prefix + ".")` check is done *before* validating that the supplied `path` matches the prefix's anchor at all. Any unrelated subpackage that happens to share a prefix segment with a registered name can be misrouted.

A correct path‑aware finder should: when `path` is given, treat it as authoritative and only look for the leaf segment (`fullname.rpartition('.')[2] + ".py"`) in those entries — exactly like `FileFinder` does ([§5.5.2](https://docs.python.org/3/reference/import.html#path-entry-finder-protocol)).

### 3. Ordering relative to `PathFinder` is wrong for the intended use case

The finder is inserted *after* `PathFinder`:

```python
path_finder_index = sys.meta_path.index(importlib.machinery.PathFinder)
sys.meta_path.insert(path_finder_index + 1, FINDER)
```

Per [§5.3.4](https://docs.python.org/3/reference/import.html#the-meta-path), finders are queried in order, first‑hit wins. Consider `boldi.dotmodpath`: there is *also* a real file `boldi/dotmodpath.py`, so `PathFinder` will find it first — which is what you want here. But for a hypothetical prefix `pkg.foo` where both `pkg/foo.py` and `pkg/foo.bar.py` exist alongside each other, `PathFinder` will succeed for `pkg.foo` and the dotmodpath finder never gets to mark it as a package. The user is then forced into the `mark_as_package(__name__)` workaround inside the file itself. That's documented behaviour today, but it's worth noting that the ordering is what *requires* `mark_as_package` to exist at all.

### 4. `mark_as_package` mutates a module post‑hoc, violating loader/spec contract

[§5.4 Loading](https://docs.python.org/3/reference/import.html#loading) describes `_init_module_attrs(spec, module)` running *before* `exec_module`. The spec's `submodule_search_locations` is the canonical source of `__path__`. `mark_as_package` mutates both `module.__path__` and `module.__spec__.submodule_search_locations` *after* the module has already been registered in `sys.modules`. A few problems:

- It sets `__path__` to a plain `list`, not the `_NamespacePath` object that PEP 420 / [§5.2.2](https://docs.python.org/3/reference/import.html#namespace-packages) describes:
  > Namespace packages do not use an ordinary list for their `__path__` attribute. They instead use a custom iterable type which will automatically perform a new search for package portions on the next import attempt within that package if the path of their parent package […] changes.

  This module isn't a namespace package, so a plain list is technically allowed by [§5.4.4](https://docs.python.org/3/reference/import.html#path__-attributes-on-modules), but if `boldi` itself is a namespace package (it is, in this repo), then dynamically inserting another package directly under it via attribute assignment can confuse later `_NamespacePath` re‑scans because they don't know about this entry.
- It must be called from inside the module body before any submodule is imported. There's no way to enforce that, and there's no error if the user forgets — submodule lookups will simply fail with a misleading `ModuleNotFoundError`.
- The cleaner approach is to detect "this is a prefix root that may have dotted children" *in the finder* and produce a spec with `submodule_search_locations` already set ([`importlib.util.spec_from_file_location(..., submodule_search_locations=[…])`](https://docs.python.org/3/library/importlib.html#importlib.util.spec_from_file_location)). Then the import machinery itself, in `_init_module_attrs`, sets `__path__` correctly *before* user code runs, and `mark_as_package` becomes unnecessary.

### 5. `find_spec` does not honour the `target` parameter (reload)

The signature in [`importlib.abc.MetaPathFinder.find_spec`](https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.find_spec) defines `target` as "a module object that the finder may use to make a more educated guess about what spec to return … The import system passes in a target module only during reload" ([§5.3.4](https://docs.python.org/3/reference/import.html#the-meta-path)). The implementation accepts `target` but ignores it. For `importlib.reload(mod)` of a previously dot‑found module, this means a stale path can be returned. For now this is benign because `mark_as_package`‑style modules can't easily be reloaded anyway, but it's a correctness gap worth noting.

### 6. `register_prefix` is not invalidation-aware

[`MetaPathFinder.invalidate_caches`](https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.invalidate_caches) is the documented hook for telling Python that a finder's view of the world has changed. The class doesn't implement it, and `register_prefix` doesn't call [`importlib.invalidate_caches()`](https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches). If a prefix is registered after import attempts have already been made (e.g. an entry point added by a plugin loaded later), `sys.path_importer_cache`'s negative entries from earlier failed lookups can shadow the newly available files. Less of a problem for this finder (it doesn't use `sys.path_importer_cache`), but `install()` is called eagerly and re‑callable, which suggests dynamic registration is intended; a defensive `importlib.invalidate_caches()` after registering new prefixes is cheap insurance.

### 7. Filesystem search semantics

- `Path(entry or os.getcwd())` — correct in spirit (matches what [`FileFinder`/`PathFinder`](https://docs.python.org/3/library/importlib.html#importlib.machinery.PathFinder) do for the empty string `''` on `sys.path`), but `sys.path` may contain things that are **not directories**: zip files, `.whl`s, eggs, anything `sys.path_hooks` knows about. [§5.5](https://docs.python.org/3/reference/import.html#the-path-based-finder) is explicit: *"Entries in `sys.path` can name directories on the file system, zip files, and potentially other 'locations' […]"*. `is_dir()` silently skips them, so dotted modules inside a zip or wheel will never be found. If you want to support installed wheels, you have to go through `sys.path_hooks` / a path entry finder, not `Path.is_dir`.
- Only `.py` is handled. `SOURCE_SUFFIXES`, `BYTECODE_SUFFIXES`, and `EXTENSION_SUFFIXES` (see [`importlib.machinery`](https://docs.python.org/3/library/importlib.html#importlib.machinery.SOURCE_SUFFIXES)) all exist for a reason; if a deployment uses `.pyc`-only or a Cython-compiled `.so`, dotted names won't resolve.
- No handling of `__pycache__`/bytecode caching. `spec_from_file_location` for a raw `.py` will use [`SourceFileLoader`](https://docs.python.org/3/library/importlib.html#importlib.machinery.SourceFileLoader) which *does* manage `.pyc`s correctly, so this is fine — but it does mean every `find_spec` call hits the filesystem with `is_dir()` and `is_file()` for every prefix and every `sys.path` entry. `FileFinder` deliberately caches `os.listdir` results ([`importlib.machinery.FileFinder`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FileFinder): "A concrete implementation of `importlib.abc.PathEntryFinder` which **caches results from the file system**"). For a project with many `sys.path` entries this finder will be measurably slower.

### 8. Prefix matching has subtle bugs

```python
for prefix in sorted(self.prefixes, key=len, reverse=True):
    if fullname != prefix and not fullname.startswith(f"{prefix}."):
        continue
```

- Sorting by length (longest first) is the right intuition — `boldi.dotmodpath` should win over `boldi` — but it's not actually checking *segment* boundaries against multi‑segment prefixes, only against `f"{prefix}."`, which is correct. OK.
- However, `fullname == prefix` matches the prefix itself — e.g. `import boldi.dotmodpath` will hit this finder with `tail = "dotmodpath"` and look for `boldi/dotmodpath.py`. That file genuinely exists, but it's already going to be found by `PathFinder` first (because the finder is registered after `PathFinder`). So the `fullname == prefix` branch is dead code in the common case, and active *only* when the real package is missing — at which point the finder will load the source file as a flat module without `__path__`, and any `import prefix.x` will then fail unless `mark_as_package` was called from inside `prefix.py`. The two implementation strategies (load `prefix.py` as a real package vs find `prefix.x.py` files) are mutually inconsistent and rely on user code to bridge them.

### 9. Module-level mutable global

```python
FINDER: "DottedModuleNameFinder | None" = None

def install() -> "DottedModuleNameFinder":
    global FINDER
    if FINDER is None:
        ...
```

Functionally fine, but: the meta path is shared per *interpreter*, while module globals are shared per *module instance*. With subinterpreters ([PEP 684](https://peps.python.org/pep-0684/), now public in 3.12+ and relevant since this package requires `>=3.12`), each subinterpreter will have its own `FINDER` global but they all install into separate `sys.meta_path`s — that's actually OK by accident. The bigger issue is that there's no `uninstall()`, and re‑calling `install()` after the finder has been removed from `sys.meta_path` (e.g. by a test fixture) silently does nothing because `FINDER is not None`.

### 10. Type / API hygiene nits

- `find_spec`'s `target` parameter is untyped. The `MetaPathFinder.find_spec` signature in [`importlib.abc`](https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.find_spec) is `find_spec(fullname, path, target=None)` returning `Optional[ModuleSpec]`. Add the annotation.
- The class doesn't inherit `MetaPathFinder` *behavior* (only the ABC marker), which is fine, but it also doesn't implement `invalidate_caches` — an explicit no-op `def invalidate_caches(self) -> None: pass` is good documentation.
- No tests for: dotted import without prior parent import, attribute access (`dmptest.foo.bar` after `import dmptest.foo.bar`), reload, registration of a prefix that doesn't exist on `sys.path`, prefix collision with a real submodule.

---

### Suggested direction

A more orthodox implementation that aligns with [§5](https://docs.python.org/3/reference/import.html):

1. Treat the prefix as a real anchor: when `find_spec(fullname, path, target)` is called and `path is not None`, restrict the search to those entries; only fall back to the `anchor`‑under‑`sys.path` strategy when `path is None`.
2. When returning a spec for a file that should act as a package (i.e. there exist sibling files `fullname.<x>.py`), pass `submodule_search_locations=[str(directory)]` to `spec_from_file_location` so the import machinery itself sets `__path__` per [§5.4.4](https://docs.python.org/3/reference/import.html#path__-attributes-on-modules). This eliminates `mark_as_package`.
3. After returning the spec for `a.b.c`, ensure parent imports happen — actually, the import machinery already does this *if* the user enters via `__import__('a.b.c')`. The remaining issue is users who write `from a.b import c`: the import system imports `a`, then `a.b`, then asks `a.b` for attribute `c`. To make that work you must (a) import the parent during your finder's resolution and (b) `setattr(parent, leaf, child_module)` after exec. Easier to require that all dotted modules go through their parent; document this prominently.
4. Implement [`invalidate_caches`](https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.invalidate_caches), and call `importlib.invalidate_caches()` after `register_prefix`.
5. Use [`sys.path_hooks`](https://docs.python.org/3/library/sys.html#sys.path_hooks) / a `PathEntryFinder` instead of a `MetaPathFinder` if you want zip‑file / wheel support per [§5.5.1](https://docs.python.org/3/reference/import.html#path-entry-finders) — but this is a much bigger refactor and probably overkill for the use case.

---

### Bottom line

The design is interesting and the implementation is small, but it doesn't fully respect the contracts the import system documents in [§5.3](https://docs.python.org/3/reference/import.html#searching), [§5.4.2](https://docs.python.org/3/reference/import.html#submodules), [§5.4.4](https://docs.python.org/3/reference/import.html#path__-attributes-on-modules), and [§5.5.2](https://docs.python.org/3/reference/import.html#path-entry-finder-protocol). The biggest correctness risks are:

1. Submodule binding on the parent (§5.4.2) is not maintained.
2. `path` argument from `find_spec` is misused.
3. `mark_as_package` patches `__path__` after the fact instead of returning a spec with `submodule_search_locations` set.
4. Only filesystem `.py` is supported; zips/wheels and `.pyc`/`.so` are silently invisible.
5. No cache invalidation; no `target`/reload handling.

Most of these are fixable with a tighter `find_spec` and by pushing `__path__` setup into the spec itself.

## User

What points could be fixed and how exactly? What's not fixable?

## Assistant

## Fixable vs. not-fixable points in `boldi.dotmodpath`

I'll group the previous critique into concrete fixes (with code sketches) and inherent limitations.

---

### Easily fixable

#### A. Set `submodule_search_locations` on the spec → eliminate `mark_as_package`

This is the single biggest fix and removes most of the §5.4.2 / §5.4.4 problems. The import machinery (per [§5.4 pseudo‑code](https://docs.python.org/3/reference/import.html#loading)) sets `module.__path__` from `spec.submodule_search_locations` *before* `exec_module` runs. So if `find_spec` returns a spec with that field populated, the file behaves as a package and **no post‑hoc patching is needed**.

```python
def find_spec(self, fullname, path=None, target=None):
    for prefix in sorted(self.prefixes, key=len, reverse=True):
        if fullname != prefix and not fullname.startswith(f"{prefix}."):
            continue
        anchor = prefix.rpartition(".")[0]
        tail = fullname[len(anchor) + 1:] if anchor else fullname
        for root in self._roots(path, anchor):
            for suffix in importlib.machinery.SOURCE_SUFFIXES:
                file = root / f"{tail}{suffix}"
                if file.is_file():
                    # Treat *every* dotmodpath file as package-capable so that
                    # `import prefix.a.b.c` can recurse without ModuleNotFoundError.
                    return importlib.util.spec_from_file_location(
                        fullname,
                        file,
                        submodule_search_locations=[str(file.parent)],
                    )
    return None
```

This also fixes the §5.3 chain‑import problem: when `import a.b.c` runs, the import machinery imports `a`, then `a.b`, then `a.b.c`. With `submodule_search_locations` set on every dotmodpath spec, `a.b.__path__` exists, so `find_spec('a.b.c', path=a.b.__path__, ...)` is reached normally. And [§5.4.2](https://docs.python.org/3/reference/import.html#submodules) `setattr(parent, leaf, child)` happens automatically because `path is not None`.

After this, `mark_as_package` becomes unused. You can either delete it or keep it for the rare case where a *real* `prefix.py` (loaded by `PathFinder`) wants to opt in — but document that "use the dotmodpath finder" is the preferred path.

#### B. Use `path` correctly when given

When the import machinery passes `path` (the parent's `__path__`), it is authoritative ([§5.5.2](https://docs.python.org/3/reference/import.html#path-entry-finder-protocol)). The current `_roots` ignores the relationship between `path` and `anchor` and instead scans the parent's `__path__` for a filename built from the *full* tail. Replace with:

```python
@staticmethod
def _roots(path, anchor):
    if path is not None:
        return tuple(Path(e or os.getcwd()) for e in path
                     if Path(e or os.getcwd()).is_dir())
    anchor_path = Path(*anchor.split(".")) if anchor else Path()
    return tuple(r for e in sys.path
                 if (r := Path(e or os.getcwd()) / anchor_path).is_dir())
```

Combined with fix A, the file name to look for inside `path` becomes simply the last segment or the dotted suffix relative to the parent. The code above keeps the current "filename = `tail`" convention; the important change is that `path` is now strictly trusted when supplied.

#### C. Honour all source/bytecode suffixes

Iterate over `importlib.machinery.SOURCE_SUFFIXES` (and optionally `BYTECODE_SUFFIXES` / `EXTENSION_SUFFIXES`) instead of hard‑coding `".py"`. See the example at the bottom of [`importlib.machinery`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FileFinder.path_hook). Already shown in fix A.

#### D. Implement `invalidate_caches` and call it on registration

```python
def invalidate_caches(self) -> None:
    pass  # No internal cache today; reserved for future caching layer.

def register_prefix(self, prefix: str) -> None:
    if prefix not in self.prefixes:
        self.prefixes.add(prefix)
        importlib.invalidate_caches()  # let other finders drop stale negatives
```

Per [`importlib.abc.MetaPathFinder.invalidate_caches`](https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.invalidate_caches) and [`importlib.invalidate_caches`](https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches).

#### E. Honour `target` (reload)

```python
def find_spec(self, fullname, path=None, target=None):
    # `target` is the existing module during reload; we don't need it
    # because the spec we'd return is fully derived from filesystem state,
    # but document and accept it explicitly.
    ...
```

The signature was already correct; just type it: `target: types.ModuleType | None = None`.

#### F. Add `uninstall()` and make `install()` idempotent against external removal

```python
def uninstall() -> None:
    global FINDER
    if FINDER is not None and FINDER in sys.meta_path:
        sys.meta_path.remove(FINDER)
    FINDER = None

def install() -> "DottedModuleNameFinder":
    global FINDER
    if FINDER is None or FINDER not in sys.meta_path:
        FINDER = DottedModuleNameFinder()
        try:
            i = sys.meta_path.index(importlib.machinery.PathFinder)
            sys.meta_path.insert(i + 1, FINDER)
        except ValueError:
            sys.meta_path.append(FINDER)
    for ep in importlib.metadata.entry_points(group=ENTRY_POINT_GROUP):
        FINDER.register_prefix(ep.name)
    return FINDER
```

Useful for tests and for plugin systems that swap the finder.

#### G. Type annotations and ABC alignment

```python
from importlib.machinery import ModuleSpec
import types

def find_spec(
    self,
    fullname: str,
    path: Sequence[str] | None = None,
    target: types.ModuleType | None = None,
) -> ModuleSpec | None: ...
```

#### H. Remove dead/ambiguous `fullname == prefix` branch (or formalise it)

Decide one of the two:

- **Drop it**: rely on `PathFinder` to find a real `prefix.py` first (current de‑facto behaviour). Then `find_spec` only handles `fullname.startswith(prefix + ".")`.
- **Make it real**: when matched, ensure the returned spec includes `submodule_search_locations=[str(parent_dir)]` so `prefix.py` loaded through *this* finder is package‑capable. With fix A this happens automatically.

Either way, document the invariant that `prefix` itself is the parent of dotted children.

#### I. Tests for the gaps

Add cases for: `import prefix.x.y.z` from a fresh interpreter (no `mark_as_package` calls), `from prefix.x import y`, attribute access (`prefix.x.y` after `import prefix.x.y`), `importlib.reload`, registering a prefix dynamically and importing immediately afterwards, and a prefix file that doesn't exist on disk.

---

### Hard but possible

#### J. Zip/wheel support

To support importing `prefix.a.b.py` *from inside a wheel/zip on `sys.path`*, the meta‑path‑finder approach fundamentally won't do — you can't `Path(entry).is_dir()` a zip. The orthodox path is to register a [path hook](https://docs.python.org/3/library/sys.html#sys.path_hooks) producing a `PathEntryFinder` per [§5.5.1](https://docs.python.org/3/reference/import.html#path-entry-finders), or to wrap `zipimport`. This is a non‑trivial refactor (~2× the code) and changes how installation works (you'd append to `sys.path_hooks` instead of `sys.meta_path`). Worth doing only if you actually ship dotmodpath modules inside built wheels.

#### K. Filesystem caching for performance

`FileFinder` caches `os.listdir` per directory ([`importlib.machinery.FileFinder`](https://docs.python.org/3/library/importlib.html#importlib.machinery.FileFinder)). The dotmodpath finder calls `is_file()` on every prefix × every `sys.path` entry × every `find_spec`. You can mirror the FileFinder approach: cache `set(os.listdir(root))` keyed on `(root, mtime)`, then check membership. Implement `invalidate_caches` to wipe the cache. Useful if you have many prefixes or many `sys.path` entries.

---

### Inherent limitations (not really fixable)

#### L. The "flat file masquerading as a package" concept is fundamentally exotic

Per [§5.2](https://docs.python.org/3/reference/import.html#packages), Python recognises only two package types: regular (`__init__.py` in a directory) and namespace (PEP 420). A `.py` file that is also a package is neither. You can *make* it work by setting `__path__`, but:

- IDEs, type checkers, linters, and packaging tools won't treat `prefix.foo.py` as a member of `prefix.foo` namespace; mypy will see `prefix.foo.bar.py` as the *module* `bar` inside a package called `foo`, not as `prefix.foo.bar`. The repo's `mypy_path` workaround in `pyproject.toml` papers over this for mypy only.
- Tooling like `python -m prefix.foo.bar` works because that goes through `runpy` → `importlib`, but `inspect.getsourcefile` on a class defined in `prefix.foo` will return `prefix.foo.py` even when the class lives in `prefix.foo.bar.py`.

You can't fix this without external tool plugins.

#### M. Cooperation with namespace packages

`boldi` is itself a PEP 420 namespace package ([§5.2.2](https://docs.python.org/3/reference/import.html#namespace-packages)). When dotmodpath ships its files under `boldi/`, the namespace's `_NamespacePath` re‑scans on each subsequent import. There is no public API for adding a "virtual portion" to a namespace package's path that survives a re‑scan correctly. In practice this is fine because the directories that contain dotmodpath files are still real on‑disk portions, but if you ever wanted dotmodpath modules to live *outside* any `sys.path` entry (e.g. fetched over the network), you'd fight `_NamespacePath` and lose.

#### N. `from prefix.x import y` semantics when `y` is the *name of a sibling file* but not the *attribute name*

`from a.b import c` is documented in [§5: The import statement](https://docs.python.org/3/reference/import.html#the-import-statement) as: import `a.b.c`, then assign `a.b.c` to `c`; if that fails, `getattr(a.b, 'c')`. With dotmodpath, after `from prefix import x`, the file `prefix.x.py` is loaded as `prefix.x` and bound on the parent (with fix A). But `from prefix.x import y` requires `prefix.x.y` to exist and `prefix.x` to be a package — so fix A is mandatory and sufficient *for this case too*. The non‑fixable corner is when `prefix.x.y` is **also** a top‑level name in `prefix.x.py` (i.e. defined inside it as a regular Python object). Python's [§5.4.2](https://docs.python.org/3/reference/import.html#submodules) invariant says the submodule wins on attribute access ("if you have `sys.modules['spam.foo']`, the latter must appear as the `foo` attribute of the former"), which will silently shadow whatever `y` was defined as in `prefix.x.py`. There's no way to opt out.

#### O. PathFinder ordering

You cannot place this finder *both* before `PathFinder` (so dotted files always win) *and* let `PathFinder` find a real `prefix.py` first (so unmodified packages still work). The current "after PathFinder" ordering is the only choice that doesn't risk shadowing real packages. Live with it.

#### P. Subinterpreters and `.pth` install timing

`.pth`‑driven install runs at site initialisation per interpreter, but because `FINDER` is a module global, importing this module from within a subinterpreter (without re‑running `.pth`) won't auto‑install. There is no portable hook that re‑runs `.pth` files on subinterpreter creation. If subinterpreter use becomes important, document "call `boldi.dotmodpath.install()` explicitly at subinterpreter startup".

---

### Suggested order of work

1. **Fix A** (set `submodule_search_locations` in the spec) — biggest correctness win, removes `mark_as_package`.
2. **Fix B** (path semantics) and **C** (suffixes) — small, mechanical.
3. **Fix D, E, F, G, H** — hygiene; each is a few lines.
4. **Fix I** — write the tests; they'll catch regressions in 1–3.
5. **K** if perf becomes an issue.
6. **J** only if you actually want wheel‑shipped dotmodpath files.
7. Document **L–P** in the README so users know the boundaries.

Most of the critique boils down to *"return a spec that fully describes the module up front, instead of patching the module after the fact."* That single change makes the finder behave the way [§5.4](https://docs.python.org/3/reference/import.html#loading) expects.
