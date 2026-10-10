"""Regras de negócio puras: sem banco, sem HTTP, sem IA.

Por serem funções simples, são fáceis de testar e de explicar em entrevista.
"""

from datetime import datetime, timedelta

from app.dominio import Prioridade, Status

# Prazo de atendimento (SLA) por prioridade, em horas corridas.
# Simplificação consciente: um sistema real contaria só horas úteis.
HORAS_SLA: dict[Prioridade, int] = {
    Prioridade.CRITICA: 4,
    Prioridade.ALTA: 8,
    Prioridade.MEDIA: 24,
    Prioridade.BAIXA: 72,
}

# Máquina de estados: de cada status, para quais outros é permitido ir.
# O primeiro de cada lista é o passo natural do fluxo; a tela o destaca.
TRANSICOES: dict[Status, tuple[Status, ...]] = {
    Status.ABERTO: (Status.EM_ATENDIMENTO,),
    Status.EM_ATENDIMENTO: (Status.RESOLVIDO, Status.ABERTO),
    Status.RESOLVIDO: (Status.FECHADO, Status.EM_ATENDIMENTO),  # reabertura
    Status.FECHADO: (),  # estado final
}

STATUS_ENCERRADOS = {Status.RESOLVIDO, Status.FECHADO}


class TransicaoInvalida(Exception):
    def __init__(self, atual: Status, novo: Status):
        permitidos = ", ".join(TRANSICOES[atual]) or "nenhum"
        super().__init__(
            f"Não é possível ir de '{atual}' para '{novo}'. Permitidos: {permitidos}."
        )


def calcular_prazo_sla(prioridade: Prioridade, inicio: datetime) -> datetime:
    return inicio + timedelta(hours=HORAS_SLA[Prioridade(prioridade)])


def proximos_status(atual: Status) -> list[Status]:
    return list(TRANSICOES[Status(atual)])


def validar_transicao(atual: Status, novo: Status) -> None:
    atual, novo = Status(atual), Status(novo)
    if novo not in TRANSICOES[atual]:
        raise TransicaoInvalida(atual, novo)


def sla_vencido(status: Status, prazo: datetime, agora: datetime) -> bool:
    """O prazo só conta como vencido enquanto o chamado ainda não foi resolvido."""
    return Status(status) not in STATUS_ENCERRADOS and prazo < agora
