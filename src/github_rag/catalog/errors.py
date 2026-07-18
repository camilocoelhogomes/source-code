"""Hierarquia de erros do catálogo — contratos T03 (sem implementação).

Responsabilidade deste módulo
    Declarar os tipos de erro que a porta ``CatalogRepository`` e o domínio de
    catálogo podem levantar. Nenhuma lógica aqui: apenas a taxonomia estável
    consumida por T07/T14/T17/T18 e verificada pelo BDD/unit tests.

Motivo da separação
    Isolar a taxonomia de erros do modelo de dados (`models.py`), das regras de
    transição (`transitions.py`) e da porta (`repository.py`). Consumidores
    capturam erros de domínio (not found, transição, concorrência) sem depender
    de PostgreSQL nem do adaptador concreto — requisito de testabilidade sem PG
    (design §3.1/§3.3, §7). Erros de infraestrutura ficam separados dos de
    domínio para não confundir falha de regra com falha de conexão/transação.

Invariantes de segurança (design §8)
    Nenhuma mensagem de erro pode conter ``DATABASE_URL`` completa nem
    credenciais. Redaction é responsabilidade de quem constrói a mensagem.
"""

from __future__ import annotations


class CatalogError(Exception):
    """Raiz da hierarquia de erros do módulo de catálogo.

    Responsabilidade
        Servir de tipo-base único para captura ampla (``except CatalogError``)
        de qualquer falha originada na camada de catálogo.

    Motivo da separação
        Uma raiz dedicada evita que consumidores capturem ``Exception`` genérica
        e permite distinguir erros do catálogo de erros de outras fronteiras
        (settings T01, config T02).
    """


class RepositoryNotFoundError(CatalogError):
    """Operação sobre um repositório inexistente (corner case do aceite).

    Responsabilidade
        Sinalizar que um ``repository_id`` (ou execução) referenciado não existe
        no catálogo (BDD CP-11).

    Motivo da separação
        Distinguir "não existe" de "estado/versão inválidos"; permite ao caller
        tratar ausência (ex.: 404 na UI) sem confundir com conflito ou transição
        ilegal. Erro puramente de domínio, testável com o fake in-memory.
    """


class InvalidStateTransitionError(CatalogError):
    """Transição fora da máquina de estados fechada (REQ-020; BDD CP-10).

    Responsabilidade
        Sinalizar tentativa de sair de um estado para outro não permitido pela
        tabela de transições (`transitions.ALLOWED_TRANSITIONS`), preservando o
        estado atual (nenhuma mutação ocorre).

    Motivo da separação
        Torna a regra de estados (REQ-020) verificável de forma isolada e
        independente de PG; a violação vira erro tipado em vez de estado
        inconsistente silencioso.
    """


class ConcurrencyConflictError(CatalogError):
    """Conflito de update otimista (BDD CP-12; D-T03-008).

    Responsabilidade
        Sinalizar que o ``expected_version`` informado em ``transition_state``
        difere do ``row_version`` atual — ou seja, outro processo alterou a
        linha entre leitura e escrita.

    Motivo da separação
        Update concorrente básico (critério de aceite) precisa de um erro próprio
        para não ser mascarado como transição inválida nem como not found. A
        checagem de versão é regra de domínio (fake) e mapeia para lock otimista
        no adaptador PG (`row_version`).
    """


class CatalogPersistenceError(CatalogError):
    """Falha de infraestrutura do adaptador PostgreSQL (design §7).

    Responsabilidade
        Envolver falhas de conexão/transação/SQL do adaptador PG, encadeando a
        causa original (``raise ... from``), sem vazar credenciais.

    Motivo da separação
        Separa falha de infraestrutura (PG indisponível, deadlock) das falhas de
        regra de domínio. O fake in-memory nunca levanta este erro; ele é
        exclusivo do adaptador concreto — mantém o domínio 100% testável sem PG.

    Invariante de segurança
        A mensagem NÃO pode conter ``DATABASE_URL`` completa nem senha (design §8).
    """
