"""Pacote raiz ``github_rag`` (D-T01-001).

Responsabilidade
    Marcador do pacote instalável sob ``src/``; fronteira raiz do layout T01.

Motivo da separação
    Isola imports do cwd (src layout) e agrupa módulos por fronteira do plano.

Invariantes
    Em T01 não exporta API de domínio; bootstrap vive em ``settings``.

Erros
    Nenhum.

Compatibilidade — Windows / macOS / Linux = primeira classe
    Pacote Python puro; utilizável no venv de dev local em Windows (PowerShell
    ou cmd), macOS e Linux. Entrega Docker/T19 não depende do ``.venv`` do host
    e usa o mesmo pacote no runtime da imagem. Paths de aplicação via
    ``pathlib`` nos módulos (não separadores de shell).
"""
