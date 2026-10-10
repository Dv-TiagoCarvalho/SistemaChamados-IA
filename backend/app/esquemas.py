"""Formato dos dados que entram e saem da API (o contrato).

Equivalem aos DTOs do Java. O Pydantic valida a entrada automaticamente e
devolve erro 422 quando algo vem errado, como o Bean Validation faz.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.dominio import (
    Categoria,
    OrigemClassificacao,
    Prioridade,
    SituacaoIntegracao,
    Status,
)


class ChamadoCriar(BaseModel):
    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(min_length=10, max_length=4000)
    solicitante_email: EmailStr


class ClassificacaoCorrigir(BaseModel):
    categoria: Categoria
    prioridade: Prioridade


class StatusAlterar(BaseModel):
    status: Status


class EventoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    descricao: str
    criado_em: datetime


class ChamadoResumo(BaseModel):
    """Versão enxuta, usada na listagem."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    solicitante_email: str
    status: Status
    categoria: Categoria
    prioridade: Prioridade
    resumo: str
    origem_classificacao: OrigemClassificacao
    prazo_sla: datetime
    sla_vencido: bool
    id_externo: str | None
    situacao_integracao: SituacaoIntegracao
    criado_em: datetime
    atualizado_em: datetime


class ChamadoDetalhe(ChamadoResumo):
    """Versão completa, usada na tela de detalhe."""

    descricao: str
    justificativa: str
    erro_integracao: str | None
    proximos_status: list[Status]
    eventos: list[EventoSaida]


class SugestaoResposta(BaseModel):
    texto: str
    origem: OrigemClassificacao


class Indicadores(BaseModel):
    total: int
    por_status: dict[Status, int]
    por_prioridade: dict[Prioridade, int]
    sla_vencido: int
    falhas_integracao: int


class Saude(BaseModel):
    status: str
    provedor_ia: str
    modelo_ia: str | None


class WebhookITSM(BaseModel):
    evento: str
    id_externo: str
    estado: str


class Erro(BaseModel):
    detail: str
