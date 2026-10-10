"""Conexão com o banco de dados (SQLAlchemy 2).

O SQLAlchemy faz aqui o papel que o JPA/Hibernate faz no Java:
mapeia classes Python para tabelas.
"""

from collections.abc import Iterator
from datetime import UTC, datetime

from sqlalchemy import DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator

from app.config import obter_configuracoes


class DataHoraUTC(TypeDecorator):
    """Garante que toda data lida do banco venha com fuso UTC.

    O SQLite não guarda o fuso horário. Sem isto, a data voltaria "ingênua"
    (sem fuso) e comparações como `prazo < agora` quebrariam.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, valor: datetime | None, dialect):
        if valor is None:
            return None
        return valor.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, valor: datetime | None, dialect):
        if valor is None:
            return None
        return valor.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    """Classe-mãe de todas as tabelas."""


def criar_engine(url: str):
    # check_same_thread=False: o FastAPI atende requisições em várias threads,
    # e o SQLite por padrão só aceita a thread que abriu a conexão.
    argumentos = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=argumentos)


engine = criar_engine(obter_configuracoes().database_url)
FabricaDeSessao = sessionmaker(bind=engine, expire_on_commit=False)


def obter_sessao() -> Iterator[Session]:
    """Entrega uma sessão por requisição e fecha ao final (como um @Transactional)."""
    with FabricaDeSessao() as sessao:
        yield sessao
