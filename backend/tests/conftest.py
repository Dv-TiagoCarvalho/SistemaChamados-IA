"""Preparação comum dos testes.

Cada teste recebe um banco em memória novinho e um ITSM falso, então nada
depende de rede, de arquivo ou da ordem em que os testes rodam.
"""

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.banco import Base, obter_sessao
from app.dependencias import (
    obter_cliente_itsm,
    obter_segredo_webhook,
    obter_servico_ia,
)
from app.integracoes.itsm import ClienteITSM
from app.main import app
from app.servicos.ia import ProvedorSimulado, ServicoIA

SEGREDO_TESTE = "segredo-de-teste"


class ITSMFalso:
    """Responde como o sistema externo e anota tudo o que recebeu."""

    def __init__(self):
        self.fora_do_ar = False
        self.requisicoes: list[httpx.Request] = []
        self.total_incidentes = 0

    def responder(self, requisicao: httpx.Request) -> httpx.Response:
        self.requisicoes.append(requisicao)
        if self.fora_do_ar:
            return httpx.Response(503)
        if requisicao.method == "POST":
            self.total_incidentes += 1
            return httpx.Response(201, json={"number": f"INC-{self.total_incidentes:04d}"})
        return httpx.Response(200, json={})


@pytest.fixture
def itsm() -> ITSMFalso:
    return ITSMFalso()


@pytest.fixture
def cliente(itsm: ITSMFalso):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    fabrica = sessionmaker(bind=engine, expire_on_commit=False)

    def sessao_de_teste():
        with fabrica() as sessao:
            yield sessao

    cliente_itsm = ClienteITSM(
        "http://itsm.teste",
        transporte=httpx.MockTransport(itsm.responder),
        espera_entre_tentativas=0,
    )
    app.dependency_overrides[obter_sessao] = sessao_de_teste
    app.dependency_overrides[obter_cliente_itsm] = lambda: cliente_itsm
    app.dependency_overrides[obter_servico_ia] = lambda: ServicoIA(ProvedorSimulado())
    app.dependency_overrides[obter_segredo_webhook] = lambda: SEGREDO_TESTE
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def novo_chamado(cliente: TestClient):
    """Atalho para abrir um chamado válido."""

    def criar(**campos) -> dict:
        dados = {
            "titulo": "VPN não conecta",
            "descricao": "Desde cedo a VPN não conecta e não consigo trabalhar.",
            "solicitante_email": "ana@empresa.com",
            **campos,
        }
        resposta = cliente.post("/api/chamados", json=dados)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return criar
