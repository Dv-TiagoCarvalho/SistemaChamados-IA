"""Entrada de avisos vindos do sistema externo (webhooks).

Webhook é uma integração "ao contrário": em vez de nós perguntarmos ao ITSM
se algo mudou, ele nos chama quando muda.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import ValidationError

from app.dependencias import corpo_bruto, obter_segredo_webhook, obter_servico_chamados
from app.esquemas import ChamadoResumo, Erro, WebhookITSM
from app.integracoes.itsm import assinatura_valida
from app.servicos.chamados import ServicoChamados

router = APIRouter(prefix="/api/webhooks", tags=["integracao"])


@router.post(
    "/itsm",
    response_model=ChamadoResumo,
    responses={
        401: {"model": Erro, "description": "Assinatura ausente ou inválida"},
        404: {"model": Erro, "description": "Nenhum chamado com esse id externo"},
        422: {"model": Erro, "description": "Corpo ou estado inválido"},
    },
)
def receber_webhook_itsm(
    corpo: bytes = Depends(corpo_bruto),
    x_assinatura: str | None = Header(default=None),
    segredo: str = Depends(obter_segredo_webhook),
    servico: ServicoChamados = Depends(obter_servico_chamados),
):
    """Recebe a mudança de estado de um incidente.

    O cabeçalho `X-Assinatura` deve conter `sha256=<HMAC-SHA256 do corpo>`
    calculado com o segredo compartilhado. Sem isso, qualquer pessoa que
    descobrisse a URL poderia alterar chamados.
    """
    if not assinatura_valida(corpo, x_assinatura, segredo):
        raise HTTPException(status_code=401, detail="Assinatura inválida.")
    try:
        dados = WebhookITSM.model_validate_json(corpo)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Corpo do webhook inválido.")
    return servico.aplicar_webhook(dados.id_externo, dados.estado)
