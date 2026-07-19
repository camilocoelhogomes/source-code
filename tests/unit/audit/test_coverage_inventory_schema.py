"""
Unit — CoverageInventory schema corners (T01 / UT-P* / UT-A*).

Pré-matriz: UT-A* falham por artefato ausente (RED esperado).
Fixtures UT-P* exercitam o helper de teste sem depender do path canônico.
"""

from __future__ import annotations

import unittest

from tests.unit.audit.inventory_schema import (
    EXPECTED_BDD_IDS,
    INVENTORY_PATH,
    T21_KNOWN_PARTIAL_OR_SMOKE,
    read_canonical_inventory,
    validate_coverage_inventory,
)

_COLS = (
    "bdd_id | superficie | status | evidencia_robot | evidencia_pytest | "
    "evidencia_browser | nota_parcial_t21 | motivo_lacuna"
)
_SEP = "|---|---|---|---|---|---|---|---|"


def _row(
    bdd: str,
    *,
    superficie: str = "catalog_indexing",
    status: str = "lacuna",
    robot: str = "e2e/robot/x.robot — Case (bdd00x)",
    pytest: str = "ausente",
    browser: str = "n/a",
    nota: str = "—",
    motivo: str = "motivo de teste",
) -> str:
    if bdd in T21_KNOWN_PARTIAL_OR_SMOKE and status == "lacuna":
        if nota == "—":
            nota = "T21 §3.5 parcial/smoke"
        if motivo == "motivo de teste":
            motivo = "fatia parcial T21"
    return (
        f"| {bdd} | {superficie} | {status} | {robot} | {pytest} | "
        f"{browser} | {nota} | {motivo} |"
    )


def _valid_matrix_text() -> str:
    rows = []
    for bdd in EXPECTED_BDD_IDS:
        if bdd in {"BDD-011", "BDD-012", "BDD-014"}:
            rows.append(
                _row(
                    bdd,
                    superficie="mcp",
                    status="coberto-integral",
                    robot=f"e2e/robot/mcp.robot — {bdd}",
                    pytest="tests/bdd/test_mcp_evidence_server.py",
                    browser="n/a",
                    nota="—",
                    motivo="—",
                )
            )
        elif bdd == "BDD-020":
            rows.append(
                _row(
                    bdd,
                    superficie="health",
                    status="coberto-integral",
                    robot="e2e/robot/health.robot — BDD-020 (bdd020)",
                    pytest="ausente",
                    browser="n/a",
                    nota="—",
                    motivo="—",
                )
            )
        elif bdd == "BDD-004":
            rows.append(
                _row(
                    bdd,
                    status="coberto-integral",
                    robot="e2e/robot/catalog_indexing.robot — BDD-004 (bdd004)",
                    pytest="tests/bdd/test_indexing_orchestrator.py",
                    browser="n/a",
                    nota="—",
                    motivo="—",
                )
            )
        elif bdd == "BDD-021":
            rows.append(
                _row(
                    bdd,
                    status="coberto-integral",
                    robot="e2e/robot/catalog_indexing.robot — BDD-001 tags bdd021",
                    pytest="tests/bdd/test_config_loader.py",
                    browser="n/a",
                    nota="—",
                    motivo="—",
                )
            )
        else:
            rows.append(_row(bdd))
    body = "\n".join(rows)
    return (
        "# CoverageInventory fixture\n\n"
        f"| {_COLS} |\n{_SEP}\n{body}\n"
    )


class TestUTPParserSchemaFixtures(unittest.TestCase):
    """UT-P01..P14 — corners com Markdown sintético."""

    def test_ut_p01_missing_matrix_table(self) -> None:
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory("# sem tabela\n")
        self.assertIn("não encontrada", str(ctx.exception).lower())

    def test_ut_p02_missing_required_column(self) -> None:
        text = (
            "| bdd_id | status |\n|---|---|\n| BDD-001 | lacuna |\n"
        )
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("coluna obrigatória", str(ctx.exception).lower())

    def test_ut_p03_invalid_superficie(self) -> None:
        text = _valid_matrix_text().replace(
            "| BDD-001 | catalog_indexing |",
            "| BDD-001 | unknown_surface |",
            1,
        )
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("superficie", str(ctx.exception).lower())

    def test_ut_p04_invalid_status(self) -> None:
        text = _valid_matrix_text().replace(
            "| BDD-001 | catalog_indexing | lacuna |",
            "| BDD-001 | catalog_indexing | parcial |",
            1,
        )
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("status", str(ctx.exception).lower())

    def test_ut_p05_invalid_browser(self) -> None:
        old = (
            "| BDD-001 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | n/a |"
        )
        new = (
            "| BDD-001 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | maybe |"
        )
        text = _valid_matrix_text().replace(old, new, 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("evidencia_browser", str(ctx.exception).lower())

    def test_ut_p06_integral_without_real_evidence(self) -> None:
        old = (
            "| BDD-004 | catalog_indexing | coberto-integral | "
            "e2e/robot/catalog_indexing.robot — BDD-004 (bdd004) | "
            "tests/bdd/test_indexing_orchestrator.py | n/a | — | — |"
        )
        new = (
            "| BDD-004 | catalog_indexing | coberto-integral | "
            "ausente | n/a | n/a | — | — |"
        )
        text = _valid_matrix_text().replace(old, new, 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("evidência real", str(ctx.exception).lower())

    def test_ut_p07_lacuna_without_motivo(self) -> None:
        old = (
            "| BDD-001 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | n/a | — | "
            "motivo de teste |"
        )
        new = (
            "| BDD-001 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | n/a | — | — |"
        )
        text = _valid_matrix_text().replace(old, new, 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("motivo_lacuna", str(ctx.exception).lower())

    def test_ut_p08_bdd015_row_forbidden(self) -> None:
        text = _valid_matrix_text().replace("| BDD-001 |", "| BDD-015 |", 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("015", str(ctx.exception))

    def test_ut_p09_duplicate_bdd_id(self) -> None:
        text = _valid_matrix_text().replace("| BDD-002 |", "| BDD-001 |", 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        msg = str(ctx.exception).lower()
        self.assertTrue("duplicado" in msg or "divergente" in msg)

    def test_ut_p10_missing_one_expected_id(self) -> None:
        lines = _valid_matrix_text().splitlines()
        filtered = [ln for ln in lines if "| BDD-002 |" not in ln]
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory("\n".join(filtered))
        self.assertIn("divergente", str(ctx.exception).lower())

    def test_ut_p11_t21_partial_cannot_be_integral(self) -> None:
        old = (
            "| BDD-003 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | n/a | "
            "T21 §3.5 parcial/smoke | fatia parcial T21 |"
        )
        new = (
            "| BDD-003 | catalog_indexing | coberto-integral | "
            "e2e/robot/x.robot — Case (bdd00x) | tests/bdd/x.py | n/a | "
            "— | — |"
        )
        text = _valid_matrix_text().replace(old, new, 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("003", str(ctx.exception))

    def test_ut_p12_t21_partial_requires_nota(self) -> None:
        old = (
            "| BDD-006 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | n/a | "
            "T21 §3.5 parcial/smoke | fatia parcial T21 |"
        )
        new = (
            "| BDD-006 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | n/a | — | "
            "fatia parcial T21 |"
        )
        text = _valid_matrix_text().replace(old, new, 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("nota_parcial_t21", str(ctx.exception).lower())

    def test_ut_p13_ui_without_browser_cannot_be_integral(self) -> None:
        old = (
            "| BDD-009 | catalog_indexing | lacuna | "
            "e2e/robot/x.robot — Case (bdd00x) | ausente | n/a | — | "
            "motivo de teste |"
        )
        new = (
            "| BDD-009 | ui | coberto-integral | e2e/robot/ui.robot — BDD-009 | "
            "tests/bdd/test_query_services.py | nao | — | — |"
        )
        text = _valid_matrix_text().replace(old, new, 1)
        with self.assertRaises(AssertionError) as ctx:
            validate_coverage_inventory(text)
        self.assertIn("browser", str(ctx.exception).lower())

    def test_ut_p14_valid_minimal_fixture_passes(self) -> None:
        rows = validate_coverage_inventory(_valid_matrix_text())
        self.assertEqual(len(rows), 23)


class TestUTACanonicalArtifact(unittest.TestCase):
    """UT-A01..A04 — path canônico (RED até a matriz existir)."""

    def test_ut_a01_canonical_path_exists(self) -> None:
        self.assertTrue(
            INVENTORY_PATH.is_file(),
            f"artefato ausente: {INVENTORY_PATH}",
        )

    def test_ut_a02_canonical_passes_schema_validation(self) -> None:
        text = read_canonical_inventory()
        rows = validate_coverage_inventory(text)
        self.assertEqual(len(rows), 23)

    def test_ut_a03_t21_denylist_is_lacuna_with_nota(self) -> None:
        text = read_canonical_inventory()
        rows = validate_coverage_inventory(text)
        by_id = {r["bdd_id"]: r for r in rows}
        for bdd_id in T21_KNOWN_PARTIAL_OR_SMOKE:
            self.assertEqual(by_id[bdd_id]["status"], "lacuna")
            self.assertNotEqual(
                by_id[bdd_id]["nota_parcial_t21"].strip(), "—"
            )

    def test_ut_a04_no_audit_closed_by_green_path(self) -> None:
        text = read_canonical_inventory().lower()
        for phrase in (
            "auditoria encerrada",
            "mvp entregue",
            "green path basta",
        ):
            self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
