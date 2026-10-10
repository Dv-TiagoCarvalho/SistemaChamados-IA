"""Injeção de dependências do FastAPI (o papel do @Autowired no Spring).

Cada função abaixo "fabrica" um objeto que as rotas pedem com Depends(...).
Nos testes, essas funções são trocadas por versões falsas.
"""

from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.banco import obter_sessao
from app.config import obter_configuracoes
from app.integracoes.itsm import ClienteITSM
from app.servicos.chamados import ServicoChamados
from app.servicos.ia import ServicoIA, criar_servico_ia


@lru_cache
def obter_servico_ia() -> ServicoIA:
    return criar_servico_ia(obter_configuracoes())


@lru_cache
def obter_cliente_itsm() -> ClienteITSM:
    config = obter_configuracoes()
    return ClienteITSM(config.itsm_base_url, config.itsm_timeout_segundos)


def obter_servico_chamados(
    sessao: Session = Depends(obter_sessao),
    ia: ServicoIA = Depends(obter_servico_ia),
    itsm: ClienteITSM = Depends(obter_cliente_itsm),
) -> ServicoChamados:
    return ServicoChamados(sessao, ia, itsm)


def obter_segredo_webhook() -> str:
    return obter_configuracoes().itsm_segredo_webhook


async def corpo_bruto(request: Request) -> bytes:
    """Bytes exatos da requisição: a assinatura do webhook é calculada sobre eles."""
    return await request.body()
