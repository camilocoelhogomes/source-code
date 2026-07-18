"""Pacote raiz ``github_rag`` (D-T01-001).

Responsabilidade
    Marcador do pacote instalável sob ``src/``; fronteira raiz do layout T01.

Motivo da separação
    Isola imports do cwd (src layout) e agrupa módulos por fronteira do plano.

Invariantes
    Em T01 não exporta API de domínio; bootstrap vive em ``settings``.

Erros
    Nenhum.

Compatibilidade Windows / macOS / Linux
    Pacote Python puro; paths via layout do repositório, não separadores de shell.
"""
