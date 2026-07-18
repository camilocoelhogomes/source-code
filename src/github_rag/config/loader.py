"""Carga e validação do arquivo de conexões (T02).

Responsabilidade deste módulo
    Declarar ``ConfigLoader`` e ``ConfigLoadError``: ler o path fornecido pelo
    caller (tipicamente ``AppSettings.config_path``), validar o JSON
    Sourcebot-like, resolver segredos e devolver ``AppConfig`` completo ou
    falhar totalmente.

Motivo da separação
    Orquestra schema + secrets + I/O de arquivo sem reimplementar bootstrap
    T01 e sem descoberta de repositórios (T05/T06). Único ponto de falha
    total / sucesso completo (BR-021).
"""

from __future__ import annotations

from pathlib import Path

from github_rag.config.schema import AppConfig
from github_rag.config.secrets import SecretResolver


class ConfigLoadError(Exception):
    """Falha total ao carregar/validar/resolver o arquivo de conexões.

    Responsabilidade
        Sinalizar qualquer rejeição do loader (path, I/O, JSON, schema,
        type, url, revisions, env) sem retornar ``AppConfig`` parcial.

    Motivo da separação
        Distinto de ``SettingsBootstrapError`` (T01) e de
        ``SecretResolutionError`` (nível resolver). Callers/BDD tratam um
        único tipo na borda de ``load``.

    Invariantes
        Mensagem cita path/conexão/campo/nome de env; nunca o valor do
        token; sem dump integral do arquivo como segredo.
    """


class ConfigLoader:
    """Porta de carga do arquivo de config de conexões.

    Responsabilidade
        ``load(path)`` → ``AppConfig`` completo ou ``ConfigLoadError``.
        Não relê ``CONFIG_PATH``/workers; não chama GitHub; não varre disco
        além do arquivo de config.

    Motivo da separação
        Superfície única alinhada ao BDD (``ConfigLoader().load(path)``);
        injeta ``SecretResolver`` opcional para testes unitários futuros.
    """

    def __init__(
        self,
        secret_resolver: SecretResolver | None = None,
    ) -> None:
        """``secret_resolver is None`` ⇒ default baseado em ``os.environ``."""
        ...

    def load(self, path: Path | None) -> AppConfig:
        """Carrega e valida o JSON em ``path``.

        Invariantes
            ``path is None`` → ``ConfigLoadError``.
            Sucesso → ``AppConfig`` com todas as conexões e segredos.
            Falha → ``ConfigLoadError`` (inclui tradução de
            ``SecretResolutionError``); nunca retorno parcial.
        """
        ...
