"""
Helper de teste — valida o contrato documental CoverageInventory (schema §6).

Não é código de produção (I-T01-003). Usado apenas por unitários T01.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
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
T21_KNOWN_PARTIAL_OR_SMOKE = frozenset(
    {"BDD-003", "BDD-006", "BDD-013"}
)
ABSENT_EVIDENCE = frozenset({"ausente", "n/a", "—", "-", ""})

_HEADER_CELL_RE = re.compile(r"^\|(.+)\|$")


def normalize_cell(cell: str) -> str:
    return " ".join(cell.strip().split())


def is_absent_evidence(value: str) -> bool:
    return normalize_cell(value).lower() in ABSENT_EVIDENCE


def split_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    match = _HEADER_CELL_RE.match(stripped)
    if match is None:
        return None
    cells = [normalize_cell(c) for c in match.group(1).split("|")]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def is_separator_row(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells)


def parse_matrix_table(text: str) -> tuple[list[str], list[dict[str, str]]]:
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        header_cells = split_row(lines[i])
        if header_cells is None:
            i += 1
            continue
        header_keys = [c.lower().replace("`", "") for c in header_cells]
        if "bdd_id" not in header_keys or "status" not in header_keys:
            i += 1
            continue
        if i + 1 >= len(lines):
            break
        sep = split_row(lines[i + 1])
        if sep is None or not is_separator_row(sep):
            i += 1
            continue
        rows: list[dict[str, str]] = []
        j = i + 2
        while j < len(lines):
            cells = split_row(lines[j])
            if cells is None or is_separator_row(cells):
                break
            if len(cells) != len(header_keys):
                raise AssertionError(
                    f"coluna count {len(cells)} != {len(header_keys)}: "
                    f"{lines[j]!r}"
                )
            rows.append(dict(zip(header_keys, cells, strict=True)))
            j += 1
        return header_keys, rows
    raise AssertionError(
        "tabela CoverageInventory não encontrada (bdd_id + status)"
    )


def validate_coverage_inventory(text: str) -> list[dict[str, str]]:
    """Valida schema §6; levanta AssertionError em qualquer violação."""
    headers, rows = parse_matrix_table(text)
    for col in REQUIRED_COLUMNS:
        if col not in headers:
            raise AssertionError(f"coluna obrigatória ausente: {col}")

    ids = [row["bdd_id"] for row in rows]
    if "BDD-015" in ids:
        raise AssertionError("BDD-015 não pode ter linha de status")
    if len(ids) != len(set(ids)):
        raise AssertionError(f"bdd_id duplicado: {ids}")
    if sorted(ids) != sorted(EXPECTED_BDD_IDS):
        raise AssertionError(
            f"conjunto bdd_id divergente; obtido={ids}"
        )

    by_id = {row["bdd_id"]: row for row in rows}
    for row in rows:
        bdd = row["bdd_id"]
        if row["superficie"] not in ALLOWED_SUPERFICIES:
            raise AssertionError(f"{bdd}: superficie inválida")
        if row["status"] not in ALLOWED_STATUS:
            raise AssertionError(f"{bdd}: status inválido")
        if row["evidencia_browser"] not in ALLOWED_BROWSER:
            raise AssertionError(f"{bdd}: evidencia_browser inválida")
        for col in (
            "evidencia_robot",
            "evidencia_pytest",
            "evidencia_browser",
        ):
            if not row[col]:
                raise AssertionError(f"{bdd}: {col} vazio")

        if row["status"] == "coberto-integral":
            robot_ok = not is_absent_evidence(row["evidencia_robot"])
            pytest_ok = not is_absent_evidence(row["evidencia_pytest"])
            if not (robot_ok or pytest_ok):
                raise AssertionError(
                    f"{bdd}: coberto-integral sem evidência real"
                )
            if (
                row["superficie"] == "ui"
                and row["evidencia_browser"] == "nao"
            ):
                raise AssertionError(
                    f"{bdd}: ui sem browser não pode ser coberto-integral"
                )

        if row["status"] == "lacuna":
            motivo = row["motivo_lacuna"].strip()
            if not motivo or motivo == "—":
                raise AssertionError(f"{bdd}: lacuna sem motivo_lacuna")

    for bdd_id in T21_KNOWN_PARTIAL_OR_SMOKE:
        row = by_id[bdd_id]
        if row["status"] != "lacuna":
            raise AssertionError(
                f"{bdd_id}: parcial/smoke T21 deve ser lacuna"
            )
        nota = row["nota_parcial_t21"].strip()
        if not nota or nota == "—":
            raise AssertionError(
                f"{bdd_id}: parcial/smoke exige nota_parcial_t21"
            )

    return rows


def read_canonical_inventory() -> str:
    if not INVENTORY_PATH.is_file():
        raise AssertionError(f"artefato ausente: {INVENTORY_PATH}")
    return INVENTORY_PATH.read_text(encoding="utf-8")
