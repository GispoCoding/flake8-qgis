# flake8_qgis
[![PyPI version](https://badge.fury.io/py/flake8-qgis.svg)](https://badge.fury.io/py/flake8-qgis)
![CI](https://github.com/GispoCoding/flake8-qgis/workflows/CI/badge.svg)
[![Code on Github](https://img.shields.io/badge/Code-GitHub-brightgreen)](https://github.com/MartinThoma/flake8-simplify)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)


A [flake8](https://flake8.pycqa.org/en/latest/index.html) plugin for QGIS3 python plugins written in Python.


Made with Cookiecutter template [cookiecutter-flake8-plugin](https://github.com/MartinThoma/cookiecutter-flake8-plugin).
Inspired by [flake8-simplify](https://github.com/MartinThoma/flake8-simplify).

## Installation

Install with `pip`:

```bash
pip install flake8-qgis
```

## Usage

Just call `flake8 .` in your package or `flake your.py`.


## Rules

* `QGS101`: Don't use from-imports from qgis projected members ([example](#QGS101))
* `QGS102`: Don't use imports from qgis projected members ([example](#QGS102))
* `QGS103`: Don't use from-imports from PyQt directly ([example](#QGS103))
* `QGS104`: Don't use imports from PyQt directly ([example](#QGS104))
* `QGS105`: Don't pass QgisInterface as an argument ([example](#QGS105))


You might have good reasons to ignore some rules.
To do that, use the standard Flake8 configuration. For example, within the `setup.cfg` file:

```python
[flake8]
ignore = QGS101, QGS102
```


## Examples

### QGS101

```python
# Bad
from qgs._core import QgsMapLayer, QgsVectorLayer

# Good
from qgs.core import QgsMapLayer, QgsVectorLayer
```

### QGS102

```python
# Bad
import qgs._core.QgsVectorLayer as QgsVectorLayer

# Good
import qgs.core.QgsVectorLayer as QgsVectorLayer
```

### QGS103

```python
# Bad
from PyQt5.QtCore import pyqtSignal

# Good
from qgis.PyQt.QtCore import pyqtSignal
```

### QGS104

```python
# Bad
import PyQt5.QtCore.pyqtSignal as pyqtSignal

# Good
import qgis.PyQt.QtCore.pyqtSignal as pyqtSignal
```

### QGS105

```python
# Bad: iface passed as argument
def some_function(somearg, iface):
    # do something with iface


# Good: iface imported
from qgis.utils import iface

def some_function(somearg):
    # do something with iface
```
