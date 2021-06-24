# Core Library modules
import ast
import sys
from collections import Generator
from typing import Any, List, Tuple, Type

if sys.version_info < (3, 8):  # pragma: no cover (<PY38)
    # Third party
    # Third party modules
    import importlib_metadata
else:  # pragma: no cover (PY38+)
    # Core Library
    # Core Library modules
    import importlib.metadata as importlib_metadata

QGS101 = (
    "QGS101 Use 'from {correct_module} import {members}' "
    "instead of 'from {module} import {members}'"
)


def _get_qgs101(node: ast.ImportFrom) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where access to a protected member of a class qgs is imported.
    eg. 'from qgs._core import ...' or 'from qgs._qui import ...'
    """
    errors: List[Tuple[int, int, str]] = []
    if node.module is None or not node.module.startswith("qgs._"):
        return errors
    errors.append(
        (
            node.lineno,
            node.col_offset,
            QGS101.format(
                module=node.module,
                correct_module=node.module.replace("_", ""),
                members=", ".join([alias.name for alias in node.names]),
            ),
        )
    )
    return errors


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: List[Tuple[int, int, str]] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:  # noqa N802
        self.errors += _get_qgs101(node)
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
