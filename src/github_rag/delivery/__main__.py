"""Entry ``python -m github_rag.delivery``.

Responsabilidade
    Chamar ``run_container_boot()`` e encerrar com o código de ``SystemExit``.

Motivo da separação
    Alinha CMD do Dockerfile ao composition root (I-T19-010 / CD-10) sem
    lógica adicional.
"""

from github_rag.delivery.runtime import run_container_boot


def main() -> None:
    run_container_boot()


if __name__ == "__main__":
    main()
