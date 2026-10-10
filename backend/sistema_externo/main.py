"""ITSM simulado: faz o papel do sistema corporativo de chamados da empresa
(algo como ServiceNow ou Jira Service Management).

É um programa separado, com vocabulário próprio (incidente, state, urgency),
justamente para a integração ter o que traduzir.

Rode com: uvicorn sistema_externo.main:app --port 8001
"""

import json
import os

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.integracoes.itsm import assinar

URL_WEBHOOK = os.getenv("URL_WEBHOOK", "http://localhost:8000/api/webhooks/itsm")
SEGREDO = os.getenv("ITSM_SEGREDO_WEBHOOK", "troque-este-segredo")
ESTADOS = {"NEW", "IN_PROGRESS", "RESOLVED", "CLOSED"}

app = FastAPI(title="ITSM simulado", version="1.0.0")

incidentes: dict[str, dict] = {}  # guardado só na memória
por_chave_idempotencia: dict[str, str] = {}


class IncidenteCriar(BaseModel):
    short_description: str
    description: str
    urgency: int


class IncidenteAtualizar(BaseModel):
    state: str | None = None
    urgency: int | None = None


class Simulacao(BaseModel):
    state: str


def _buscar(numero: str) -> dict:
    if numero not in incidentes:
        raise HTTPException(status_code=404, detail="Incidente não encontrado")
    return incidentes[numero]


def _validar_estado(estado: str) -> None:
    if estado not in ESTADOS:
        raise HTTPException(status_code=422, detail=f"Estado inválido: {estado}")


@app.get("/incidentes")
def listar():
    return list(incidentes.values())


@app.post("/incidentes", status_code=201)
def criar(dados: IncidenteCriar, idempotency_key: str | None = Header(default=None)):
    # Mesma chave = mesma requisição repetida: devolve o que já foi criado.
    if idempotency_key and idempotency_key in por_chave_idempotencia:
        return incidentes[por_chave_idempotencia[idempotency_key]]
    numero = f"INC-{len(incidentes) + 1:04d}"
    incidentes[numero] = {"number": numero, "state": "NEW", **dados.model_dump()}
    if idempotency_key:
        por_chave_idempotencia[idempotency_key] = numero
    return incidentes[numero]


@app.patch("/incidentes/{numero}")
def atualizar(numero: str, dados: IncidenteAtualizar):
    incidente = _buscar(numero)
    if dados.state is not None:
        _validar_estado(dados.state)
        incidente["state"] = dados.state
    if dados.urgency is not None:
        incidente["urgency"] = dados.urgency
    return incidente


@app.post("/incidentes/{numero}/simular-atualizacao")
def simular_atualizacao(numero: str, dados: Simulacao):
    """Finge que um técnico mudou o incidente dentro do ITSM e avisa a
    Central de Chamados por webhook assinado."""
    incidente = _buscar(numero)
    _validar_estado(dados.state)
    incidente["state"] = dados.state

    corpo = json.dumps(
        {"evento": "incidente.atualizado", "id_externo": numero, "estado": dados.state}
    ).encode()
    try:
        resposta = httpx.post(
            URL_WEBHOOK,
            content=corpo,
            headers={"Content-Type": "application/json", "X-Assinatura": assinar(corpo, SEGREDO)},
            timeout=5,
        )
    except httpx.HTTPError as erro:
        raise HTTPException(status_code=502, detail=f"Webhook não entregue: {erro}")
    return {"incidente": incidente, "webhook_http": resposta.status_code}
