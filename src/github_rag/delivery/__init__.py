"""Composition root de entrega (T19).

Responsabilidade
    Reexportar a superfície estável consumida por CMD, BDD e unitários.

Motivo da separação
    CD-10 exige ``ContainerRuntime``, ``DefaultContainerRuntime``,
    ``run_container_boot`` importáveis de ``github_rag.delivery``.
"""

from github_rag.delivery.ports import ContainerRuntime
from github_rag.delivery.runtime import DefaultContainerRuntime, run_container_boot

__all__ = [
    "ContainerRuntime",
    "DefaultContainerRuntime",
    "run_container_boot",
]
