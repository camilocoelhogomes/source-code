"""Regras de tipo para elegibilidade de arquivos (T09).

Responsabilidade deste módulo
    Centralizar denylists de CSV/imagens e a política de arquivos sem
    extensão usadas pelo filtro de elegibilidade.

Motivo da separação
    Isolar política de tipo (D-T09-004 / D-T09-005) da porta pura e do
    motor pathspec, evitando allowlist acidental de linguagens e permitindo
    estender denylists sem alterar o contrato ``FileEligibilityFilter``.
"""

from __future__ import annotations

from dataclasses import dataclass

CSV_DENYLIST: frozenset[str] = frozenset({".csv"})
"""Extensões CSV excluídas (case-insensitive na aplicação).

Responsabilidade: denylist mínima fechada D-T09-004 para CSV.
Motivo da separação: literal versionado distinto da lista de imagens.
Invariantes: cada item começa com ``.``; matching case-insensitive no filter.
Erros: nenhum nesta constante.
"""

IMAGE_DENYLIST: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".webp",
        ".ico",
        ".tif",
        ".tiff",
        ".heic",
        ".avif",
        ".svg",
    }
)
"""Extensões de imagem excluídas (raster, ícones e SVG).

Responsabilidade: denylist mínima fechada D-T09-004 / REQ-015.
Motivo da separação: evolui independentemente do CSV e do matching gitignore.
Invariantes: cada item começa com ``.``; matching case-insensitive no filter.
Erros: nenhum nesta constante.
"""


@dataclass(frozen=True)
class EligibilityRules:
    """Política de elegibilidade por tipo de arquivo.

    Responsabilidade
        Agrupar denylists CSV/imagens e a flag de inclusão de arquivos sem
        extensão (D-T09-005 include-by-default).

    Motivo da separação
        Permite injetar regras em testes/unitários e trocar listas sem mudar
        a assinatura da porta ``FileEligibilityFilter``.

    Invariantes
        Extensões com ponto leading; ``include_extensionless`` default True;
        sem allowlist de linguagens.

    Erros
        Nenhum na construção; o filter aplica as regras.
    """

    csv_extensions: frozenset[str] = CSV_DENYLIST
    image_extensions: frozenset[str] = IMAGE_DENYLIST
    include_extensionless: bool = True


DEFAULT_ELIGIBILITY_RULES = EligibilityRules()
"""Instância default alinhada a D-T09-004 e D-T09-005.

Responsabilidade: defaults únicos para ``PathspecFileEligibilityFilter``.
Motivo da separação: callers não recriam frozensets; testes podem override.
Invariantes: denylists fechadas da task; ``include_extensionless=True``.
Erros: nenhum.
"""
