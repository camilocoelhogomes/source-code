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

import json
from pathlib import Path
from typing import Any

from github_rag.config.schema import (
    AppConfig,
    _AppConfig,
    _EnvSecretRef,
    _GitConnection,
    _GitHubConnection,
    _ResolvedSecret,
    _Revisions,
)
from github_rag.config.secrets import (
    EnvironSecretResolver,
    SecretResolutionError,
    SecretResolver,
)


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
        injeta ``SecretResolver`` opcional para testes unitários.
    """

    def __init__(
        self,
        secret_resolver: SecretResolver | None = None,
    ) -> None:
        """``secret_resolver is None`` ⇒ default baseado em ``os.environ``."""
        self._secret_resolver = (
            EnvironSecretResolver()
            if secret_resolver is None
            else secret_resolver
        )

    def load(self, path: Path | None) -> AppConfig:
        """Carrega e valida o JSON em ``path``.

        Invariantes
            ``path is None`` → ``ConfigLoadError``.
            Sucesso → ``AppConfig`` com todas as conexões e segredos.
            Falha → ``ConfigLoadError`` (inclui tradução de
            ``SecretResolutionError``); nunca retorno parcial.
        """
        if path is None:
            raise ConfigLoadError("CONFIG_PATH ausente")
        if not isinstance(path, Path):
            raise ConfigLoadError("path de configuração inválido")

        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ConfigLoadError(
                f"não foi possível ler o arquivo de configuração {path}"
            ) from exc

        try:
            document = json.loads(raw)
        except (json.JSONDecodeError, RecursionError) as exc:
            raise ConfigLoadError(
                f"JSON inválido no arquivo de configuração {path}"
            ) from exc

        if not isinstance(document, dict):
            raise ConfigLoadError("raiz da configuração deve ser um objeto")
        if "connections" not in document:
            raise ConfigLoadError("campo connections obrigatório")

        raw_connections = document["connections"]
        if not isinstance(raw_connections, dict):
            raise ConfigLoadError("campo connections deve ser um objeto")

        connections: dict[str, _GitHubConnection | _GitConnection] = {}
        for name, raw_connection in raw_connections.items():
            if not isinstance(name, str) or not name.strip():
                raise ConfigLoadError("nome de conexão inválido")
            if not isinstance(raw_connection, dict):
                raise ConfigLoadError(f"conexão {name!r} deve ser um objeto")

            connection_type = raw_connection.get("type")
            if connection_type == "github":
                connection = self._load_github(name, raw_connection)
            elif connection_type == "git":
                connection = self._load_git(name, raw_connection)
            else:
                raise ConfigLoadError(
                    f"conexão {name!r} possui type ausente ou inválido"
                )
            connections[name] = connection

        return _AppConfig(connections)

    def _load_github(
        self,
        name: str,
        raw: dict[str, Any],
    ) -> _GitHubConnection:
        orgs = self._string_list(raw.get("orgs"), name, "orgs", allow_empty=False)
        repos = self._string_list(raw.get("repos"), name, "repos", allow_empty=True)
        revisions = self._revisions(raw.get("revisions"), name)

        token = raw.get("token")
        if not isinstance(token, dict) or set(token) != {"env"}:
            raise ConfigLoadError(
                f"conexão {name!r}: token deve usar somente referência env"
            )
        env_name = token.get("env")
        if not isinstance(env_name, str) or not env_name.strip():
            raise ConfigLoadError(
                f"conexão {name!r}: token.env deve ser string não-vazia"
            )

        try:
            value = self._secret_resolver.resolve(env_name)
        except SecretResolutionError as exc:
            raise ConfigLoadError(
                f"conexão {name!r}: não foi possível resolver {env_name!r}: {exc}"
            ) from exc
        if not isinstance(value, str) or not value.strip():
            raise ConfigLoadError(
                f"conexão {name!r}: segredo {env_name!r} ausente ou vazio"
            )

        return _GitHubConnection(
            orgs=orgs,
            repos=repos,
            token=_EnvSecretRef(env_name),
            secret=_ResolvedSecret(value),
            revisions=revisions,
        )

    def _load_git(
        self,
        name: str,
        raw: dict[str, Any],
    ) -> _GitConnection:
        url = raw.get("url")
        if (
            not isinstance(url, str)
            or not url.startswith("file://")
            or not url.removeprefix("file://").startswith("/")
        ):
            raise ConfigLoadError(
                f"conexão {name!r}: url deve ser file:// absoluta"
            )
        return _GitConnection(
            url=url,
            revisions=self._revisions(raw.get("revisions"), name),
        )

    @staticmethod
    def _string_list(
        value: Any,
        connection_name: str,
        field_name: str,
        *,
        allow_empty: bool,
    ) -> tuple[str, ...]:
        if not isinstance(value, list) or (not allow_empty and not value):
            raise ConfigLoadError(
                f"conexão {connection_name!r}: {field_name} inválido"
            )
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ConfigLoadError(
                f"conexão {connection_name!r}: {field_name} contém item inválido"
            )
        return tuple(value)

    def _revisions(self, value: Any, connection_name: str) -> _Revisions:
        if not isinstance(value, dict):
            raise ConfigLoadError(
                f"conexão {connection_name!r}: revisions deve ser objeto"
            )
        branches = self._string_list(
            value.get("branches"),
            connection_name,
            "revisions.branches",
            allow_empty=False,
        )
        if "main" not in branches:
            raise ConfigLoadError(
                f"conexão {connection_name!r}: revisions.branches deve conter main"
            )
        return _Revisions(branches)
