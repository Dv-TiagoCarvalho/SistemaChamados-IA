from datetime import UTC, datetime, timedelta

import pytest

from app.dominio import Prioridade, Status
from app.servicos import regras

INICIO = datetime(2026, 1, 5, 9, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    "prioridade, horas",
    [
        (Prioridade.CRITICA, 4),
        (Prioridade.ALTA, 8),
        (Prioridade.MEDIA, 24),
        (Prioridade.BAIXA, 72),
    ],
)
def test_prazo_depende_da_prioridade(prioridade, horas):
    assert regras.calcular_prazo_sla(prioridade, INICIO) == INICIO + timedelta(hours=horas)


def test_fluxo_normal_e_permitido():
    regras.validar_transicao(Status.ABERTO, Status.EM_ATENDIMENTO)
    regras.validar_transicao(Status.EM_ATENDIMENTO, Status.RESOLVIDO)
    regras.validar_transicao(Status.RESOLVIDO, Status.FECHADO)


def test_resolvido_pode_ser_reaberto():
    regras.validar_transicao(Status.RESOLVIDO, Status.EM_ATENDIMENTO)


@pytest.mark.parametrize(
    "atual, novo",
    [
        (Status.ABERTO, Status.RESOLVIDO),  # não pode pular o atendimento
        (Status.ABERTO, Status.FECHADO),
        (Status.FECHADO, Status.ABERTO),  # fechado é final
        (Status.ABERTO, Status.ABERTO),
    ],
)
def test_transicoes_proibidas(atual, novo):
    with pytest.raises(regras.TransicaoInvalida):
        regras.validar_transicao(atual, novo)


def test_sla_vence_so_em_chamado_ainda_aberto():
    prazo = INICIO
    depois = INICIO + timedelta(minutes=1)
    assert regras.sla_vencido(Status.ABERTO, prazo, depois) is True
    assert regras.sla_vencido(Status.EM_ATENDIMENTO, prazo, depois) is True
    assert regras.sla_vencido(Status.RESOLVIDO, prazo, depois) is False
    assert regras.sla_vencido(Status.ABERTO, prazo, INICIO - timedelta(minutes=1)) is False


def test_proximo_passo_natural_vem_primeiro():
    assert regras.proximos_status(Status.EM_ATENDIMENTO) == [Status.RESOLVIDO, Status.ABERTO]
    assert regras.proximos_status(Status.FECHADO) == []
