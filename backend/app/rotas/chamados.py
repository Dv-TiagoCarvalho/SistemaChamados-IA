"""Rotas HTTP dos chamados (a camada @RestController).

Cada função só traduz HTTP <-> serviço. Nenhuma regra de negócio mora aqui.
"""

from fastapi import APIRouter, Depends, status

from app.dependencias import obter_servico_chamados, obter_servico_ia
from app.dominio import Categoria, Prioridade, Status
from app.esquemas import (
    ChamadoCriar,
    ChamadoDetalhe,
    ChamadoResumo,
    ClassificacaoCorrigir,
    Erro,
    Indicadores,
    Saude,
    StatusAlterar,
    SugestaoResposta,
)
from app.servicos.chamados import ServicoChamados
from app.servicos.ia import ServicoIA

router = APIRouter(prefix="/api")

NAO_ENCONTRADO = {404: {"model": Erro, "description": "Chamado não encontrado"}}


@router.get("/saude", response_model=Saude, tags=["sistema"])
def saude(ia: ServicoIA = Depends(obter_servico_ia)):
    """Usado por monitoramento para saber se a API está de pé."""
    return Saude(
        status="ok", provedor_ia=ia.provedor.nome, modelo_ia=ia.provedor.modelo
    )


@router.get("/indicadores", response_model=Indicadores, tags=["chamados"])
def indicadores(servico: ServicoChamados = Depends(obter_servico_chamados)):
    return servico.indicadores()


@router.post(
    "/chamados",
    response_model=ChamadoDetalhe,
    status_code=status.HTTP_201_CREATED,
    tags=["chamados"],
)
def criar_chamado(
    dados: ChamadoCriar, servico: ServicoChamados = Depends(obter_servico_chamados)
):
    """Abre um chamado: classifica com IA, calcula o prazo e registra no ITSM."""
    return servico.criar(dados)


@router.get("/chamados", response_model=list[ChamadoResumo], tags=["chamados"])
def listar_chamados(
    status: Status | None = None,
    prioridade: Prioridade | None = None,
    categoria: Categoria | None = None,
    servico: ServicoChamados = Depends(obter_servico_chamados),
):
    """Lista os chamados: em andamento primeiro, do prazo mais próximo ao mais distante."""
    return servico.listar(status, prioridade, categoria)


@router.get(
    "/chamados/{chamado_id}",
    response_model=ChamadoDetalhe,
    responses=NAO_ENCONTRADO,
    tags=["chamados"],
)
def obter_chamado(
    chamado_id: int, servico: ServicoChamados = Depends(obter_servico_chamados)
):
    return servico.obter(chamado_id)


@router.patch(
    "/chamados/{chamado_id}/status",
    response_model=ChamadoDetalhe,
    responses={**NAO_ENCONTRADO, 409: {"model": Erro, "description": "Transição não permitida"}},
    tags=["chamados"],
)
def alterar_status(
    chamado_id: int,
    dados: StatusAlterar,
    servico: ServicoChamados = Depends(obter_servico_chamados),
):
    return servico.alterar_status(chamado_id, dados.status)


@router.patch(
    "/chamados/{chamado_id}/classificacao",
    response_model=ChamadoDetalhe,
    responses=NAO_ENCONTRADO,
    tags=["chamados"],
)
def corrigir_classificacao(
    chamado_id: int,
    dados: ClassificacaoCorrigir,
    servico: ServicoChamados = Depends(obter_servico_chamados),
):
    """Correção humana da classificação feita pela IA. Recalcula o prazo."""
    return servico.corrigir_classificacao(chamado_id, dados.categoria, dados.prioridade)


@router.post(
    "/chamados/{chamado_id}/sugestao-resposta",
    response_model=SugestaoResposta,
    responses=NAO_ENCONTRADO,
    tags=["ia"],
)
def sugerir_resposta(
    chamado_id: int, servico: ServicoChamados = Depends(obter_servico_chamados)
):
    """Gera um rascunho de resposta. Nada é enviado: o atendente revisa antes."""
    texto, origem = servico.sugerir_resposta(chamado_id)
    return SugestaoResposta(texto=texto, origem=origem)


@router.post(
    "/chamados/{chamado_id}/sincronizar",
    response_model=ChamadoDetalhe,
    responses=NAO_ENCONTRADO,
    tags=["integracao"],
)
def sincronizar(
    chamado_id: int, servico: ServicoChamados = Depends(obter_servico_chamados)
):
    """Tenta de novo a integração com o ITSM depois de uma falha."""
    return servico.sincronizar(chamado_id)
