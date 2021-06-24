# Core Library
# Core Library modules
import ast
from typing import Set

# Third party modules
import pytest

# First party modules
# First party
from flake8_qgis import Plugin

"""Tests for `flake8_qgis` package."""


def _results(s: str) -> Set[str]:
    tree = ast.parse(s)
    plugin = Plugin(tree)
    return {f"{line}:{col} {msg}" for line, col, msg, _ in plugin.run()}


def test_trivial_case():
    assert _results("") == set()


def test_plugin_version():
    assert isinstance(Plugin.version, str)
    assert "." in Plugin.version


def test_plugin_name():
    assert isinstance(Plugin.name, str)


def test_QGS201_pass():
    ret = _results("from qgs.core import QgsMapLayer, QgsVectorLayer")
    assert ret == set()


def test_QGS201():
    ret = _results("from qgs._core import QgsMapLayer, QgsVectorLayer")
    assert ret == {
        "1:0 QGS101 Use 'from qgs.core import QgsMapLayer, QgsVectorLayer' instead of "
        "'from qgs._core import QgsMapLayer, QgsVectorLayer'"
    }
