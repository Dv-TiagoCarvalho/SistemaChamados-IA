"""Tabelas do banco. Cada classe equivale a uma @Entity do JPA."""

from datetime import UTC, datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.banco import Base, DataHoraUTC
from app.dominio import (
    Categoria,
    OrigemClassificacao,
    Prioridade,
    SituacaoIntegracao,
    Status,
)
from app.servicos import regras


def agora() -> datetime:
    return datetime.now(UTC)


class Chamado(Base):
    __tablename__ = "chamados"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(Text)
    solicitante_email: Mapped[str] = mapped_column(String(254))

    status: Mapped[Status] = mapped_column(String(20), default=Status.ABERTO)
    categoria: Mapped[Categoria] = mapped_column(String(20))
    prioridade: Mapped[Prioridade] = mapped_column(String(20))

    # Resultado da classificação automática
    resumo: Mapped[str] = mapped_column(String(300))
    justificativa: Mapped[str] = mapped_column(String(500))
    origem_classificacao: Mapped[OrigemClassificacao] = mapped_column(String(20))

    prazo_sla: Mapped[datetime] = mapped_column(DataHoraUTC)

    # Espelho no sistema corporativo externo (ITSM)
    id_externo: Mapped[str | None] = mapped_column(String(40), index=True)
    situacao_integracao: Mapped[SituacaoIntegracao] = mapped_column(
        String(20), default=SituacaoIntegracao.PENDENTE
    )
    erro_integracao: Mapped[str | None] = mapped_column(String(300))

    criado_em: Mapped[datetime] = mapped_column(DataHoraUTC, default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(
        DataHoraUTC, default=agora, onupdate=agora
    )

    eventos: Mapped[list["Evento"]] = relationship(
        back_populates="chamado",
        cascade="all, delete-orphan",
        order_by="Evento.id",
    )

    # Campos calculados: não existem no banco, mas aparecem na resposta da API.
    @property
    def sla_vencido(self) -> bool:
        return regras.sla_vencido(self.status, self.prazo_sla, agora())

    @property
    def proximos_status(self) -> list[Status]:
        return regras.proximos_status(self.status)

    def registrar_evento(self, tipo: str, descricao: str) -> None:
        self.eventos.append(Evento(tipo=tipo, descricao=descricao[:400]))


class Evento(Base):
    """Histórico do chamado: quem fez o quê e quando (trilha de auditoria)."""

    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(primary_key=True)
    chamado_id: Mapped[int] = mapped_column(ForeignKey("chamados.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(40))
    descricao: Mapped[str] = mapped_column(String(400))
    criado_em: Mapped[datetime] = mapped_column(DataHoraUTC, default=agora)

    chamado: Mapped[Chamado] = relationship(back_populates="eventos")
