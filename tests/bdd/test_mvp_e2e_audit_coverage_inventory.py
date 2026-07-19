"""
BDD executável — T01-coverage-inventory (artefato CoverageInventory).

Valida existência/estrutura de
    spec/features/mvp-e2e-audit-hardening/audit/coverage-inventory.md
conforme design §6 (schema da matriz). Não roda Robot/e2e.

Cenários: INV-01..INV-08 — ver
    spec/features/mvp-e2e-audit-hardening/tasks/T01-coverage-inventory/bdd.md

Execução:
    python -m pytest tests/bdd/test_mvp_e2e_audit_coverage_inventory.py -q

TDD: artefato ausente → falha esperada até a implementação documental.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    REPO_ROOT
    / "spec"
    / "features"
    / "mvp-e2e-audit-hardening"
    / "audit"
    / "coverage-inventory.md"
)

EXPECTED_BDD_IDS = tuple(
    f"BDD-{n:03d}" for n in (*range(1, 15), *range(16, 25))
)
REQUIRED_COLUMNS = (
    "bdd_id",
    "superficie",
    "status",
    "evidencia_robot",
    "evidencia_pytest",
    "evidencia_browser",
    "nota_parcial_t21",
    "motivo_lacuna",
)
ALLOWED_SUPERFICIES = frozenset(
    {
        "health",
        "catalog_indexing",
        "ui",
        "mcp",
        "negative",
        "tooling-e2e",
        "sdk",
    }
)
ALLOWED_STATUS = frozenset({"coberto-integral", "lacuna"})
ALLOWED_BROWSER = frozenset({"sim", "nao", "n/a"})
# T21 design §3.5 — fatias explícitas "parcial" / "smoke" (≠ cobertura integral).
T21_KNOWN_PARTIAL_OR_SMOKE = frozenset(
    {
        "BDD-003",  # cron ativo; não espera ciclo 24h
        "BDD-006",  # hits via busca; exclusão CSV/binários não integral
        "BDD-013",  # paralelo MCP sob limite; sem SLO rígido
        "BDD-024",  # smoke imagem; pin DEC-015 é gate unitário
    }
)
ABSENT_EVIDENCE = frozenset({"ausente", "n/a", "—", "-", ""})

_HEADER_CELL_RE = re.compile(r"^\|(.+)\|$")


def _read_inventory() -> str:
    if not INVENTORY_PATH.is_file():
        raise AssertionError(f"artefato ausente: {INVENTORY_PATH}")
    return INVENTORY_PATH.read_text(encoding="utf-8")


def _normalize_cell(cell: str) -> str:
    return " ".join(cell.strip().split())


def _is_absent_evidence(value: str) -> bool:
    return _normalize_cell(value).lower() in ABSENT_EVIDENCE


def _split_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    match = _HEADER_CELL_RE.match(stripped)
    if match is None:
        return None
    cells = [_normalize_cell(c) for c in match.group(1).split("|")]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def _is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells)


def _parse_matrix_table(text: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse first markdown table whose header includes bdd_id + status."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        header_cells = _split_row(lines[i])
        if header_cells is None:
            i += 1
            continue
        header_keys = [c.lower().replace("`", "") for c in header_cells]
        if "bdd_id" not in header_keys or "status" not in header_keys:
            i += 1
            continue
        if i + 1 >= len(lines):
            break
        sep = _split_row(lines[i + 1])
        if sep is None or not _is_separator_row(sep):
            i += 1
            continue
        rows: list[dict[str, str]] = []
        j = i + 2
        while j < len(lines):
            cells = _split_row(lines[j])
            if cells is None:
                break
            if _is_separator_row(cells):
                break
            if len(cells) != len(header_keys):
                raise AssertionError(
                    f"linha da matriz com {len(cells)} colunas; "
                    f"esperado {len(header_keys)}: {lines[j]!r}"
                )
            rows.append(dict(zip(header_keys, cells, strict=True)))
            j += 1
        return header_keys, rows
    raise AssertionError(
        "tabela da matriz CoverageInventory não encontrada "
        "(cabeçalho com bdd_id e status)"
    )


def _load_matrix() -> tuple[str, list[str], list[dict[str, str]]]:
    text = _read_inventory()
    headers, rows = _parse_matrix_table(text)
    return text, headers, rows


def _preamble_before_matrix(text: str) -> str:
    """Texto antes da tabela da matriz (cabeçalho do artefato)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cells = _split_row(line)
        if cells is None:
            continue
        keys = [c.lower().replace("`", "") for c in cells]
        if "bdd_id" in keys and "status" in keys:
            return "\n".join(lines[:i])
    return text


def _rows_by_id(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["bdd_id"]: row for row in rows}


# ---------------------------------------------------------------------------
# INV-01 — artefato canônico
# ---------------------------------------------------------------------------


class TestINV01ArtifactExists(unittest.TestCase):
    """INV-01 — coverage-inventory.md no path canônico."""

    def test_inventory_file_exists(self) -> None:
        self.assertTrue(
            INVENTORY_PATH.is_file(),
            f"artefato ausente: {INVENTORY_PATH}",
        )


# ---------------------------------------------------------------------------
# INV-02 — cabeçalho / metadados
# ---------------------------------------------------------------------------


class TestINV02HeaderMetadata(unittest.TestCase):
    """INV-02 — feature, data, critério integral, exclusão 015, inspeção estática."""

    def test_header_declares_required_metadata(self) -> None:
        text = _read_inventory()
        preamble = _preamble_before_matrix(text)
        lower = preamble.lower()

        self.assertIn("mvp-e2e-audit-hardening", lower)
        self.assertRegex(
            preamble,
            r"(?i)\b(data|date)\b",
            "cabeçalho deve declarar data do inventário",
        )
        self.assertTrue(
            "integral" in lower or "texto integral" in lower,
            "cabeçalho deve declarar critério = texto integral do pai",
        )
        self.assertIn("bdd-015", lower)
        self.assertTrue(
            re.search(r"bdd-015[^\n]{0,160}(exclu|fora)", lower)
            or re.search(r"(exclu|fora)[^\n]{0,160}bdd-015", lower),
            "cabeçalho deve declarar exclusão/fora de BDD-015 (não só citar o id)",
        )
        self.assertTrue(
            "inspeção estática" in lower
            or "inspecao estatica" in lower
            or "static inspection" in lower
            or ("sem run" in lower and "estática" in lower)
            or ("sem run" in lower and "estatica" in lower),
            "cabeçalho deve declarar método = inspeção estática (sem run)",
        )


# ---------------------------------------------------------------------------
# INV-03 — nota BDD-015
# ---------------------------------------------------------------------------


class TestINV03Bdd015ExclusionNote(unittest.TestCase):
    """INV-03 — nota fixa: BDD-015 fora do inventário automatizado."""

    def test_bdd015_exclusion_note_present(self) -> None:
        text = _read_inventory()
        lower = text.lower()
        self.assertIn("bdd-015", lower)
        self.assertTrue(
            "fora do inventário" in lower
            or "fora do inventario" in lower
            or "fora do inventário automatizado" in lower
            or "req-010" in lower,
            "nota de exclusão BDD-015 ausente ou incompleta",
        )
        self.assertTrue(
            "humana" in lower or "humano" in lower or "human" in lower,
            "nota BDD-015 deve indicar validação humana",
        )


# ---------------------------------------------------------------------------
# INV-04 — linhas BDD esperadas
# ---------------------------------------------------------------------------


class TestINV04BddRowCoverage(unittest.TestCase):
    """INV-04 — 23 linhas (001–014, 016–024); sem BDD-015."""

    def test_matrix_rows_match_expected_bdd_ids(self) -> None:
        _, _, rows = _load_matrix()
        ids = [row["bdd_id"] for row in rows]
        self.assertEqual(
            sorted(ids),
            sorted(EXPECTED_BDD_IDS),
            f"bdd_ids da matriz divergem do esperado; obtido={ids}",
        )
        self.assertNotIn("BDD-015", ids)
        self.assertEqual(len(ids), 23)
        self.assertEqual(len(set(ids)), 23, "bdd_id duplicado na matriz")


# ---------------------------------------------------------------------------
# INV-05 — colunas do schema
# ---------------------------------------------------------------------------


class TestINV05SchemaColumns(unittest.TestCase):
    """INV-05 — colunas obrigatórias do schema §6."""

    def test_required_columns_present(self) -> None:
        _, headers, _ = _load_matrix()
        for col in REQUIRED_COLUMNS:
            self.assertIn(col, headers, f"coluna obrigatória ausente: {col}")


# ---------------------------------------------------------------------------
# INV-06 — domínio dos valores
# ---------------------------------------------------------------------------


class TestINV06RowValueDomains(unittest.TestCase):
    """INV-06 — superficie/status/evidências com domínio válido (REQ-009)."""

    def test_each_row_has_valid_domain_values(self) -> None:
        _, _, rows = _load_matrix()
        self.assertTrue(rows, "matriz sem linhas")
        for row in rows:
            bdd = row["bdd_id"]
            self.assertIn(
                row["superficie"],
                ALLOWED_SUPERFICIES,
                f"{bdd}: superficie inválida {row['superficie']!r}",
            )
            self.assertIn(
                row["status"],
                ALLOWED_STATUS,
                f"{bdd}: status inválido {row['status']!r}",
            )
            for col in (
                "evidencia_robot",
                "evidencia_pytest",
                "evidencia_browser",
            ):
                self.assertTrue(
                    row[col],
                    f"{bdd}: {col} vazio",
                )
            self.assertIn(
                row["evidencia_browser"],
                ALLOWED_BROWSER,
                f"{bdd}: evidencia_browser inválida "
                f"{row['evidencia_browser']!r}",
            )

    def test_coberto_integral_requires_real_robot_or_pytest_evidence(self) -> None:
        """M-02 / REQ-009: coberto-integral não admite evidências ausente/n/a."""
        _, _, rows = _load_matrix()
        for row in rows:
            if row["status"] != "coberto-integral":
                continue
            bdd = row["bdd_id"]
            robot_ok = not _is_absent_evidence(row["evidencia_robot"])
            pytest_ok = not _is_absent_evidence(row["evidencia_pytest"])
            self.assertTrue(
                robot_ok or pytest_ok,
                f"{bdd}: coberto-integral exige evidencia_robot ou "
                f"evidencia_pytest real (≠ ausente/n/a); "
                f"robot={row['evidencia_robot']!r} "
                f"pytest={row['evidencia_pytest']!r}",
            )


# ---------------------------------------------------------------------------
# INV-07 — lacunas documentadas + anti-parcial T21
# ---------------------------------------------------------------------------


class TestINV07LacunaDocumentation(unittest.TestCase):
    """INV-07 — lacuna exige motivo; parciais T21 não podem ser integral."""

    def test_lacuna_rows_have_motivo(self) -> None:
        _, _, rows = _load_matrix()
        lacunas = [r for r in rows if r["status"] == "lacuna"]
        for row in lacunas:
            motivo = row["motivo_lacuna"].strip()
            self.assertTrue(
                motivo and motivo != "—",
                f"{row['bdd_id']}: lacuna sem motivo_lacuna",
            )

    def test_t21_known_partial_or_smoke_must_be_lacuna_with_nota(self) -> None:
        """M-01 / BR-001: BDD-003/006/013/024 (T21 parcial/smoke) ⇒ lacuna + nota."""
        _, _, rows = _load_matrix()
        by_id = _rows_by_id(rows)
        for bdd_id in sorted(T21_KNOWN_PARTIAL_OR_SMOKE):
            self.assertIn(
                bdd_id,
                by_id,
                f"{bdd_id}: linha ausente na matriz",
            )
            row = by_id[bdd_id]
            self.assertEqual(
                row["status"],
                "lacuna",
                f"{bdd_id}: fatia T21 parcial/smoke não pode ser "
                f"coberto-integral (status={row['status']!r})",
            )
            nota = row["nota_parcial_t21"].strip()
            self.assertTrue(
                nota and nota != "—",
                f"{bdd_id}: lacuna por parcial/smoke T21 exige "
                f"nota_parcial_t21 (obtido={row['nota_parcial_t21']!r})",
            )

    def test_ui_without_browser_cannot_be_coberto_integral(self) -> None:
        """D-T01-005: superficie=ui + evidencia_browser=nao ⇒ não integral."""
        _, _, rows = _load_matrix()
        for row in rows:
            if row["superficie"] != "ui":
                continue
            if row["evidencia_browser"] != "nao":
                continue
            self.assertNotEqual(
                row["status"],
                "coberto-integral",
                f"{row['bdd_id']}: UI sem browser não pode ser "
                f"coberto-integral (D-T01-005)",
            )


# ---------------------------------------------------------------------------
# INV-08 — SoT para T06 / BDD-008 parcial
# ---------------------------------------------------------------------------


class TestINV08SotForGapFill(unittest.TestCase):
    """INV-08 — lacunas rastreáveis; não encerra auditoria só com green path."""

    def test_lacuna_rows_are_traceable(self) -> None:
        _, _, rows = _load_matrix()
        lacunas = [r for r in rows if r["status"] == "lacuna"]
        for row in lacunas:
            self.assertTrue(row["bdd_id"])
            self.assertIn(row["superficie"], ALLOWED_SUPERFICIES)
            self.assertTrue(
                row["motivo_lacuna"].strip()
                and row["motivo_lacuna"].strip() != "—",
                f"{row['bdd_id']}: lacuna não rastreável sem motivo",
            )

    def test_does_not_declare_audit_closed_by_green_path_alone(self) -> None:
        text = _read_inventory().lower()
        forbidden = (
            "auditoria encerrada",
            "auditoria concluída só com green",
            "mvp entregue",
            "green path basta",
        )
        for phrase in forbidden:
            self.assertNotIn(
                phrase,
                text,
                f"artefato não deve declarar encerramento por green path: "
                f"{phrase!r}",
            )


if __name__ == "__main__":
    unittest.main()
