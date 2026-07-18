"""Erros tipados da descoberta GitHub (T05).

Responsabilidade deste módulo
    Declarar ``GitHubDiscoveryError`` sem acoplar a HTTP ou orquestração.

Motivo da separação
    Evita import circular entre ``client`` e ``discovery``; mensagens nunca
    contêm valor do token (BDD-014).
"""


class GitHubDiscoveryError(Exception):
    """Falha na descoberta de repositórios GitHub.

    Responsabilidade
        Sinalizar erros de auth, rede, rate limit ou org inacessível.

    Motivo da separação
        Distinto de ``ConfigLoadError`` (T02); mensagens nunca contêm o token
        (BDD-014 / BR-008).
    """
