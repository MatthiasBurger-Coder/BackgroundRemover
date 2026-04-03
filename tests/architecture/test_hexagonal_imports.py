"""Executable architecture checks aligned with Import Linter contracts."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "src" / "application"
LAYER_ORDER = {
    "infrastructure": 0,
    "adapters": 1,
    "application": 2,
    "ports": 3,
    "domain": 4,
}
LAYER_PREFIXES = {
    "src.application.infrastructure": "infrastructure",
    "src.application.adapters": "adapters",
    "src.application.application": "application",
    "src.application.ports": "ports",
    "src.application.domain": "domain",
}


class HexagonalImportTests(unittest.TestCase):
    """Protect the same hexagonal dependency rules as the Import Linter config."""

    def test_layers_only_depend_inward(self) -> None:
        violations: list[str] = []
        for module_name, path in _iter_application_modules():
            source_layer = _layer_for_module(module_name)
            if source_layer is None:
                continue

            for imported_module in _collect_internal_imports(path):
                target_layer = _layer_for_module(imported_module)
                if target_layer is None:
                    continue
                if LAYER_ORDER[target_layer] < LAYER_ORDER[source_layer]:
                    violations.append(
                        f"{module_name} ({source_layer}) must not import {imported_module} ({target_layer})"
                    )

        self.assertEqual(violations, [], "\n".join(violations))

    def test_incoming_and_outgoing_adapters_stay_separate(self) -> None:
        violations: list[str] = []
        for module_name, path in _iter_application_modules():
            imported_modules = _collect_internal_imports(path)
            if module_name.startswith("src.application.adapters.incoming"):
                for imported_module in imported_modules:
                    if imported_module.startswith("src.application.adapters.outgoing"):
                        violations.append(f"{module_name} must not import {imported_module}")
            if module_name.startswith("src.application.adapters.outgoing"):
                for imported_module in imported_modules:
                    if imported_module.startswith("src.application.adapters.incoming"):
                        violations.append(f"{module_name} must not import {imported_module}")

        self.assertEqual(violations, [], "\n".join(violations))


def _iter_application_modules() -> list[tuple[str, Path]]:
    modules: list[tuple[str, Path]] = []
    for path in SOURCE_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        modules.append((_module_name_for_path(path), path))
    return modules


def _module_name_for_path(path: Path) -> str:
    relative_parts = path.relative_to(PROJECT_ROOT).with_suffix("").parts
    if relative_parts[-1] == "__init__":
        relative_parts = relative_parts[:-1]
    return ".".join(relative_parts)


def _collect_internal_imports(path: Path) -> set[str]:
    imports: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src.application."):
                    imports.add(alias.name)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
            and node.module.startswith("src.application.")
        ):
            imports.add(node.module)
    return imports


def _layer_for_module(module_name: str) -> str | None:
    for prefix, layer_name in LAYER_PREFIXES.items():
        if module_name == prefix or module_name.startswith(f"{prefix}."):
            return layer_name
    return None


if __name__ == "__main__":
    unittest.main()
