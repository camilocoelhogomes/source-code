# Interfaces — T36-fix-zoekt-index-cli-binary-e2e

Estado: `APPROVED_BY_ARCHITECT`

## Alterações em `github_rag.e2e.zoekt_bin`

### `_container_index_bin(env) -> str`

Responsabilidade: resolve binário CLI dentro do container sidecar.  
Motivo: imagem webserver não tem `zoekt-index`; sidecar expõe nome configurável.

### `_container_ps_filter(env) -> str`

Responsabilidade: filtro `podman ps` para serviço `zoekt-cli`.  
Motivo: evita exec acidental no container webserver sem CLI.

### `materialize_zoekt_index_wrapper(..., python_executable: str | None = None)`

Responsabilidade: shebang aponta para interpretador do processo materializador (`.venv`).  
Motivo: `#/usr/bin/env python3` não enxerga pacote `github_rag`.

## Compose

Serviço `zoekt-cli`: build `docker/zoekt-cli`, volume index compartilhado, `sleep infinity`.
