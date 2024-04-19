# Core Library modules
import ast
import re
import sys
from _ast import FunctionDef, Import
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    List,
    Optional,
    Tuple,
    Type,
)

if TYPE_CHECKING:
    FlakeError = Tuple[int, int, str]


CLASS_FACTORY = "classFactory"

QGIS_INTERFACE = "QgisInterface"

if sys.version_info < (3, 8):
    # Third party modules
    import importlib_metadata
else:
    # Core Library modules
    import importlib.metadata as importlib_metadata

FROM_IMPORT_USE_INSTEAD_OF = (
    "{code} Use 'from {correct_module} import {members}' "
    "instead of 'from {module} import {members}'"
)
IMPORT_USE_INSTEAD_OF = "{code} Use 'import {correct}' instead of 'import {incorrect}'"
QGS105 = (
    "QGS105 Do not pass iface (QgisInterface) as an argument, "
    "instead import it: 'from qgis.utils import iface'"
)
QGS106 = "QGS106 Use 'from osgeo import {members}' instead of 'import {members}'"


def _test_qgis_module(module: Optional[str]) -> Optional[str]:
    if module is None:
        return None

    modules = module.split(".")
    if len(modules) < 2:
        return None

    if modules[0] in ("qgs", "qgis") and modules[1].startswith("_"):
        modules[1] = modules[1].removeprefix("_")
        return ".".join(modules)

    return None


def _test_pyqt_module(module: Optional[str]) -> Optional[str]:
    if module is None:
        return None

    modules = module.split(".")
    if re.match(r"^PyQt[456]$", modules[0]):
        modules[0] = "qgis.PyQt"
        return ".".join(modules)

    return None


def _test_module_at_from_import(
    error_code: str,
    node: ast.ImportFrom,
    tester: Callable[[Optional[str]], Optional[str]],
) -> List["FlakeError"]:
    fixed_module_name = tester(node.module)
    if fixed_module_name:
        message = FROM_IMPORT_USE_INSTEAD_OF.format(
            code=error_code,
            correct_module=fixed_module_name,
            module=node.module,
            members=", ".join([alias.name for alias in node.names]),
        )

        return [(node.lineno, node.col_offset, message)]

    return []


def _test_module_at_import(
    error_code: str, node: ast.Import, tester: Callable[[Optional[str]], Optional[str]]
) -> List["FlakeError"]:
    errors: List["FlakeError"] = []
    for alias in node.names:
        fixed_module_name = tester(alias.name)
        if fixed_module_name:
            message = IMPORT_USE_INSTEAD_OF.format(
                code=error_code, correct=fixed_module_name, incorrect=alias.name
            )
            errors.append((node.lineno, node.col_offset, message))

    return errors


def _get_qgs105(node: ast.FunctionDef) -> List["FlakeError"]:
    errors: List["FlakeError"] = []
    if node.name == CLASS_FACTORY:
        return errors
    for arg in node.args.args:
        if (
            arg.arg == "iface"
            or (hasattr(arg, "type_comment") and arg.type_comment == QGIS_INTERFACE)
            or (
                arg.annotation
                and hasattr(arg.annotation, "id")
                and arg.annotation.id == QGIS_INTERFACE
            )
        ):
            errors.append((node.lineno, node.col_offset, QGS105))
    return errors


def _get_qgs106(node: ast.Import) -> List["FlakeError"]:
    errors: List["FlakeError"] = []
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
        self.errors: List["FlakeError"] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        self.errors += _test_module_at_from_import("QGS101", node, _test_qgis_module)
        self.errors += _test_module_at_from_import("QGS103", node, _test_pyqt_module)
        self.generic_visit(node)

    def visit_Import(self, node: Import) -> None:  # noqa: N802
        self.errors += _test_module_at_import("QGS102", node, _test_qgis_module)
        self.errors += _test_module_at_import("QGS104", node, _test_pyqt_module)
        self.errors += _get_qgs106(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: FunctionDef) -> None:  # noqa: N802
        self.errors += _get_qgs105(node)
        self.generic_visit(node)


class Plugin:
    name = __name__
    version = importlib_metadata.version("flake8_qgis")

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        visitor = Visitor()

        # Add parent
        for node in ast.walk(self._tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore
        visitor.visit(self._tree)

        for line, col, msg in visitor.errors:
            yield line, col, msg, type(self)
