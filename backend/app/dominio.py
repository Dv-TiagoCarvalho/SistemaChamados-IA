"""Vocabulário do domínio: os valores fixos que um chamado pode assumir.

StrEnum faz cada valor ser também uma string, então ele vai para o JSON e para
o banco como texto legível ("alta"), e não como número.
"""

from enum import StrEnum


class Status(StrEnum):
    ABERTO = "aberto"
    EM_ATENDIMENTO = "em_atendimento"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"


class Prioridade(StrEnum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class Categoria(StrEnum):
    ACESSO = "acesso"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    REDE = "rede"
    OUTROS = "outros"


class OrigemClassificacao(StrEnum):
    IA = "ia"  # um modelo de linguagem classificou
    REGRA = "regra"  # classificador por palavras-chave (simulado ou plano B)
    HUMANO = "humano"  # um atendente corrigiu


class SituacaoIntegracao(StrEnum):
    PENDENTE = "pendente"
    SINCRONIZADO = "sincronizado"
    FALHOU = "falhou"
