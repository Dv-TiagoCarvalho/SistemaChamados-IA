"""Integração com o sistema corporativo de chamados (ITSM).

Este arquivo é a única parte do projeto que conhece o "idioma" do sistema
externo: suas URLs, seus nomes de campo e seus códigos de estado. O resto da
aplicação só enxerga os métodos de ClienteITSM.
"""

import hashlib
import hmac
import time

import httpx

from app.dominio import Prioridade, Status

# Tradução entre o vocabulário da nossa plataforma e o do sistema externo.
STATUS_PARA_ESTADO: dict[Status, str] = {
    Status.ABERTO: "NEW",
    Status.EM_ATENDIMENTO: "IN_PROGRESS",
    Status.RESOLVIDO: "RESOLVED",
    Status.FECHADO: "CLOSED",
}
ESTADO_PARA_STATUS: dict[str, Status] = {v: k for k, v in STATUS_PARA_ESTADO.items()}

PRIORIDADE_PARA_URGENCIA: dict[Prioridade, int] = {
    Prioridade.CRITICA: 1,
    Prioridade.ALTA: 2,
    Prioridade.MEDIA: 3,
    Prioridade.BAIXA: 4,
}


class ErroIntegracao(Exception):
    """O sistema externo não respondeu ou recusou a operação."""


class ClienteITSM:
    TENTATIVAS = 2

    def __init__(
        self,
        base_url: str,
        timeout: float = 3.0,
        transporte: httpx.BaseTransport | None = None,
        espera_entre_tentativas: float = 0.3,
    ):
        # `transporte` permite simular o sistema externo nos testes, sem rede.
        self._http = httpx.Client(base_url=base_url, timeout=timeout, transport=transporte)
        self._espera = espera_entre_tentativas

    def registrar_chamado(
        self, chamado_id: int, titulo: str, descricao: str, prioridade: Prioridade
    ) -> str:
        """Cria o incidente no sistema externo e devolve o identificador de lá."""
        corpo = {
            "short_description": titulo,
            "description": descricao,
            "urgency": PRIORIDADE_PARA_URGENCIA[Prioridade(prioridade)],
        }
        # Chave de idempotência: se a mesma requisição chegar duas vezes (por
        # causa de uma nova tentativa), o sistema externo não cria duplicado.
        cabecalhos = {"Idempotency-Key": f"chamado-{chamado_id}"}
        dados = self._enviar("POST", "/incidentes", corpo, cabecalhos)
        return dados["number"]

    def atualizar_incidente(
        self, id_externo: str, status: Status, prioridade: Prioridade
    ) -> None:
        corpo = {
            "state": STATUS_PARA_ESTADO[Status(status)],
            "urgency": PRIORIDADE_PARA_URGENCIA[Prioridade(prioridade)],
        }
        self._enviar("PATCH", f"/incidentes/{id_externo}", corpo)

    def _enviar(
        self, metodo: str, caminho: str, corpo: dict, cabecalhos: dict | None = None
    ) -> dict:
        ultimo_erro = "erro desconhecido"
        for tentativa in range(1, self.TENTATIVAS + 1):
            try:
                resposta = self._http.request(
                    metodo, caminho, json=corpo, headers=cabecalhos
                )
            except httpx.HTTPError as erro:  # sem conexão, tempo esgotado...
                ultimo_erro = f"sem resposta do sistema externo ({type(erro).__name__})"
            else:
                if resposta.status_code < 400:
                    return resposta.json()
                ultimo_erro = f"sistema externo respondeu HTTP {resposta.status_code}"
                if resposta.status_code < 500:
                    break  # erro 4xx é culpa da requisição: tentar de novo não resolve
            if tentativa < self.TENTATIVAS:
                time.sleep(self._espera * tentativa)
        raise ErroIntegracao(ultimo_erro)


def assinar(corpo: bytes, segredo: str) -> str:
    """Assinatura HMAC-SHA256 usada para autenticar webhooks."""
    resumo = hmac.new(segredo.encode(), corpo, hashlib.sha256).hexdigest()
    return f"sha256={resumo}"


def assinatura_valida(corpo: bytes, assinatura: str | None, segredo: str) -> bool:
    if not assinatura:
        return False
    # compare_digest compara em tempo constante, o que evita ataques de tempo.
    return hmac.compare_digest(assinar(corpo, segredo), assinatura)
