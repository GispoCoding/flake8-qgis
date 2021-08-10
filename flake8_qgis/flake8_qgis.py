# Core Library modules
import ast
import sys
from typing import Any, List, Optional, Tuple

# Third party modules
from _ast import FunctionDef, Import

CLASS_FACTORY = "classFactory"

QGIS_INTERFACE = "QgisInterface"

if sys.version_info < (3, 8):
    # Third party modules
    import importlib_metadata
else:
    # Core Library modules
    import importlib.metadata as importlib_metadata

QGS101_AND_QGS103 = (
    "{code} Use 'from {correct_module} import {members}' "
    "instead of 'from {module} import {members}'"
)
QGS102_AND_QGS104 = "{code} Use 'import {correct}' " "instead of 'import {incorrect}'"
QGS105 = (
    "QGS105 Do not pass iface (QgisInterface) as an argument, "
    "instead import it: 'from qgs.utils import iface'"
)
QGS106 = "QGS106 Use 'from osgeo import {members}' " "instead of 'import {members}'"


def _get_qgs101_and_103(
    node: ast.ImportFrom, code: str, package: str, correct_package: Optional[str] = None
) -> List[Tuple[int, int, str]]:
    errors: List[Tuple[int, int, str]] = []
    if node.module is None or not node.module.startswith(package):
        return errors
    errors.append(
        (
            node.lineno,
            node.col_offset,
            QGS101_AND_QGS103.format(
                code=code,
                module=node.module,
                correct_module=node.module.replace("._", ".")
                if correct_package is None
                else node.module.replace(package, correct_package),
                members=", ".join([alias.name for alias in node.names]),
            ),
        )
    )
    return errors


def _get_qgs102_and_qgs104(
    node: ast.Import, code: str, package: str, correct_package: Optional[str] = None
) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where access to a protected member of a class qgs is imported.
    eg. 'import qgs._core...' or 'import qgs._qui...'
    """
    errors: List[Tuple[int, int, str]] = []
    for alias in node.names:
        if alias.name.startswith(package):
            errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    QGS102_AND_QGS104.format(
                        code=code,
                        correct=alias.name.replace("._", ".")
                        if correct_package is None
                        else alias.name.replace(package, correct_package),
                        incorrect=alias.name,
                    ),
                )
            )
    return errors


def _get_qgs101(node: ast.ImportFrom) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where access to a protected member of a class qgs is imported.
    eg. 'from qgs._core import ...' or 'from qgs._qui import ...'
    """
    return _get_qgs101_and_103(node, "QGS101", "qgs._") + _get_qgs101_and_103(
        node, "QGS101", "qgis._"
    )


def _get_qgs102(node: ast.Import) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where access to a protected member of a class qgs is imported.
    eg. 'import qgs._core...' or 'import qgs._qui...'
    """
    return _get_qgs102_and_qgs104(node, "QGS102", "qgs._") + _get_qgs102_and_qgs104(
        node, "QGS102", "qgis._"
    )


def _get_qgs103(node: ast.ImportFrom) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where PyQt is directly imported.
    """
    errors: List[Tuple[int, int, str]] = []
    for qt_version_num in (4, 5, 6):
        errors += _get_qgs101_and_103(
            node, "QGS103", f"PyQt{qt_version_num}", "qgis.PyQt"
        )
    return errors


def _get_qgs104(node: ast.Import) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where PyQt is directly imported.
    """
    errors: List[Tuple[int, int, str]] = []
    for qt_version_num in (4, 5, 6):
        errors += _get_qgs102_and_qgs104(
            node, "QGS104", f"PyQt{qt_version_num}", "qgis.PyQt"
        )
    return errors


def _get_qgs105(node: ast.FunctionDef) -> List[Tuple[int, int, str]]:
    errors: List[Tuple[int, int, str]] = []
    if node.name == CLASS_FACTORY:
        return errors
    for arg in node.args.args:
        if (
            arg.arg == "iface"
            or (hasattr(arg, "type_comment") and arg.type_comment == QGIS_INTERFACE)
            or (
                arg.annotation
                and hasattr(arg.annotation, "id")
                and arg.annotation.id == QGIS_INTERFACE  # type: ignore
            )
        ):
            errors.append((node.lineno, node.col_offset, QGS105))
    return errors


def _get_qgs106(node: ast.Import) -> List[Tuple[int, int, str]]:
    errors: List[Tuple[int, int, str]] = []
    for alias in node.names:
        if alias.name in ("gdal", "ogr"):
            errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    QGS106.format(members=alias.name),
                )
            )
    return errors


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: List[Tuple[int, int, str]] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:  # noqa N802
        self.errors += _get_qgs101(node)
        self.errors += _get_qgs103(node)
        self.generic_visit(node)

    def visit_Import(self, node: Import) -> Any:  # noqa N802
        self.errors += _get_qgs102(node)
        self.errors += _get_qgs104(node)
        self.errors += _get_qgs106(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:  # noqa N802
        self.errors += _get_qgs105(node)
        self.generic_visit(node)


class Plugin:
    name = __name__
    version = importlib_metadata.version("flake8_qgis")

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self):  # noqa
        visitor = Visitor()

        # Add parent
        for node in ast.walk(self._tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore
        visitor.visit(self._tree)

        for line, col, msg in visitor.errors:
            yield line, col, msg, type(self)
