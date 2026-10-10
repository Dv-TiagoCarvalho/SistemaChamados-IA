"""Ponto de entrada da API. Rode com: uvicorn app.main:app --reload"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.banco import Base, engine
from app.config import obter_configuracoes
from app.rotas import chamados, webhooks
from app.servicos.chamados import ChamadoNaoEncontrado, EstadoExternoDesconhecido
from app.servicos.regras import TransicaoInvalida


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Cria as tabelas se não existirem. Em um projeto real, a evolução do
    # banco seria feita com migrações (Alembic, o "Flyway" do Python).
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Central de Chamados com IA",
    version="1.0.0",
    description=(
        "API de chamados de suporte de TI com classificação por IA generativa "
        "e integração com um sistema corporativo (ITSM)."
    ),
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=obter_configuracoes().origens_permitidas,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chamados.router)
app.include_router(webhooks.router)


# Tradução de erros de negócio para códigos HTTP (como um @ControllerAdvice).
def _responder(codigo: int):
    def tratar(_: Request, erro: Exception) -> JSONResponse:
        return JSONResponse(status_code=codigo, content={"detail": str(erro)})

    return tratar


app.add_exception_handler(ChamadoNaoEncontrado, _responder(404))
app.add_exception_handler(TransicaoInvalida, _responder(409))
app.add_exception_handler(EstadoExternoDesconhecido, _responder(422))
