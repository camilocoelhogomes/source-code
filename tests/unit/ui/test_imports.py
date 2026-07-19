"""Unit — conformidade imports UI / FastAPI (T18 / BDD-024).

I-T27-002: constantes e extração AST promovidas a ``tests/unit/ui/helpers.py``
(mesma asserção, mesmo resultado — refactor comportamentalmente neutro).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.unit.ui.helpers import (
    DOMAIN_MODULES,
    FASTAPI_MODULES,
    FORBIDDEN_HOMEMADE,
    FORBIDDEN_IN_DOMAIN,
    UI_PKG,
    imports_of_file,
)


class TestUiImports(unittest.TestCase):
    def test_domain_modules_without_fastapi(self) -> None:
        for name in DOMAIN_MODULES:
            path = UI_PKG / name
            self.assertTrue(path.is_file(), msg=name)
            found = imports_of_file(path) & FORBIDDEN_IN_DOMAIN
            self.assertFalse(found, msg=f"{name}: {found}")

    def test_app_api_use_fastapi(self) -> None:
        for name in FASTAPI_MODULES:
            path = UI_PKG / name
            self.assertTrue(path.is_file(), msg=name)
            self.assertIn("fastapi", imports_of_file(path), msg=name)

    def test_no_homemade_http_clients_in_ui_pkg(self) -> None:
        for path in UI_PKG.glob("*.py"):
            found = imports_of_file(path) & FORBIDDEN_HOMEMADE
            self.assertFalse(found, msg=f"{path.name}: {found}")

    def test_imports_of_file_raises_for_missing_file(self) -> None:
        """UT-DEC-R03 (review Architect R-3): arquivo inexistente propaga erro.

        ``imports_of_file`` foi promovida a helper público (I-T27-002); antes
        desta revisão nenhum teste chamava a função com um ``Path``
        inexistente — todas as chamadas usavam arquivos reais do pacote
        ``ui``. A função não deve engolir a ausência do arquivo.
        """
        with self.assertRaises((FileNotFoundError, OSError)):
            imports_of_file(Path("/no/such/arquivo-t27-fixture.py"))


if __name__ == "__main__":
    unittest.main()
