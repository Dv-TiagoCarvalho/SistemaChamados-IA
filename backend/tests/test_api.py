import json
from datetime import datetime, timedelta

from app.integracoes.itsm import assinar
from tests.conftest import SEGREDO_TESTE


def _horas_de_prazo(chamado: dict) -> float:
    criado = datetime.fromisoformat(chamado["criado_em"])
    prazo = datetime.fromisoformat(chamado["prazo_sla"])
    return (prazo - criado) / timedelta(hours=1)


# ------------------------------------------------------------- abertura


def test_abrir_chamado_classifica_calcula_prazo_e_integra(novo_chamado, itsm):
    chamado = novo_chamado()

    assert chamado["status"] == "aberto"
    assert chamado["categoria"] == "rede"
    assert chamado["prioridade"] == "alta"
    assert chamado["origem_classificacao"] == "regra"
    assert _horas_de_prazo(chamado) == 8
    assert chamado["id_externo"] == "INC-0001"
    assert chamado["situacao_integracao"] == "sincronizado"
    assert chamado["proximos_status"] == ["em_atendimento"]

    enviado = itsm.requisicoes[0]
    assert enviado.headers["Idempotency-Key"] == f"chamado-{chamado['id']}"
    assert json.loads(enviado.content)["urgency"] == 2  # alta -> urgência 2


def test_entrada_invalida_devolve_422(cliente):
    resposta = cliente.post(
        "/api/chamados",
        json={"titulo": "oi", "descricao": "curta", "solicitante_email": "não é email"},
    )
    assert resposta.status_code == 422


def test_chamado_inexistente_devolve_404(cliente):
    assert cliente.get("/api/chamados/999").status_code == 404


# --------------------------------------------------------------- status


def test_fluxo_de_status_e_enviado_ao_itsm(cliente, novo_chamado, itsm):
    chamado = novo_chamado()
    url = f"/api/chamados/{chamado['id']}/status"

    assert cliente.patch(url, json={"status": "em_atendimento"}).status_code == 200
    resposta = cliente.patch(url, json={"status": "resolvido"})

    assert resposta.json()["status"] == "resolvido"
    ultimo = itsm.requisicoes[-1]
    assert ultimo.method == "PATCH"
    assert ultimo.url.path == "/incidentes/INC-0001"
    assert json.loads(ultimo.content)["state"] == "RESOLVED"


def test_transicao_proibida_devolve_409(cliente, novo_chamado):
    chamado = novo_chamado()
    resposta = cliente.patch(
        f"/api/chamados/{chamado['id']}/status", json={"status": "fechado"}
    )
    assert resposta.status_code == 409
    assert "Permitidos: em_atendimento" in resposta.json()["detail"]


# -------------------------------------------------------- classificação


def test_correcao_humana_recalcula_o_prazo(cliente, novo_chamado):
    chamado = novo_chamado()
    resposta = cliente.patch(
        f"/api/chamados/{chamado['id']}/classificacao",
        json={"categoria": "acesso", "prioridade": "critica"},
    )
    corrigido = resposta.json()
    assert corrigido["origem_classificacao"] == "humano"
    assert _horas_de_prazo(corrigido) == 4


def test_sugestao_de_resposta(cliente, novo_chamado):
    chamado = novo_chamado()
    resposta = cliente.post(f"/api/chamados/{chamado['id']}/sugestao-resposta")
    assert resposta.status_code == 200
    assert "conexão" in resposta.json()["texto"]


# ----------------------------------------------------------- integração


def test_itsm_fora_do_ar_nao_impede_abertura_e_permite_nova_tentativa(
    cliente, novo_chamado, itsm
):
    itsm.fora_do_ar = True
    chamado = novo_chamado()

    assert chamado["situacao_integracao"] == "falhou"
    assert chamado["id_externo"] is None
    assert "503" in chamado["erro_integracao"]
    assert len(itsm.requisicoes) == 2  # tentou duas vezes antes de desistir

    itsm.fora_do_ar = False
    resposta = cliente.post(f"/api/chamados/{chamado['id']}/sincronizar")
    assert resposta.json()["situacao_integracao"] == "sincronizado"
    assert resposta.json()["id_externo"] == "INC-0001"
    assert resposta.json()["erro_integracao"] is None


def _webhook(cliente, corpo: dict, segredo: str = SEGREDO_TESTE):
    bruto = json.dumps(corpo).encode()
    return cliente.post(
        "/api/webhooks/itsm",
        content=bruto,
        headers={"Content-Type": "application/json", "X-Assinatura": assinar(bruto, segredo)},
    )


def test_webhook_assinado_atualiza_status_sem_devolver_ao_itsm(cliente, novo_chamado, itsm):
    chamado = novo_chamado()
    antes = len(itsm.requisicoes)

    resposta = _webhook(
        cliente,
        {"evento": "incidente.atualizado", "id_externo": "INC-0001", "estado": "RESOLVED"},
    )

    assert resposta.status_code == 200
    assert cliente.get(f"/api/chamados/{chamado['id']}").json()["status"] == "resolvido"
    assert len(itsm.requisicoes) == antes  # nada de eco para o sistema externo


def test_webhook_repetido_nao_duplica_historico(cliente, novo_chamado):
    chamado = novo_chamado()
    corpo = {"evento": "incidente.atualizado", "id_externo": "INC-0001", "estado": "IN_PROGRESS"}
    _webhook(cliente, corpo)
    _webhook(cliente, corpo)

    eventos = cliente.get(f"/api/chamados/{chamado['id']}").json()["eventos"]
    assert [e["tipo"] for e in eventos].count("webhook") == 1


def test_webhook_com_assinatura_errada_e_recusado(cliente, novo_chamado):
    novo_chamado()
    corpo = {"evento": "incidente.atualizado", "id_externo": "INC-0001", "estado": "CLOSED"}
    assert _webhook(cliente, corpo, segredo="outro-segredo").status_code == 401
    assert cliente.post("/api/webhooks/itsm", json=corpo).status_code == 401


def test_webhook_com_estado_desconhecido_devolve_422(cliente, novo_chamado):
    novo_chamado()
    corpo = {"evento": "incidente.atualizado", "id_externo": "INC-0001", "estado": "BANANA"}
    assert _webhook(cliente, corpo).status_code == 422


# ----------------------------------------------------------- consultas


def test_filtros_e_indicadores(cliente, novo_chamado, itsm):
    novo_chamado()  # rede / alta
    novo_chamado(titulo="Dúvida sobre o Excel", descricao="Gostaria de saber como criar um gráfico.")
    itsm.fora_do_ar = True
    novo_chamado(titulo="Sistema parado", descricao="O sistema de vendas está fora do ar para todos.")

    altas = cliente.get("/api/chamados", params={"prioridade": "alta"}).json()
    assert [c["titulo"] for c in altas] == ["VPN não conecta"]

    todos = cliente.get("/api/chamados").json()
    assert todos[0]["prioridade"] == "critica"  # prazo mais curto vem primeiro

    indicadores = cliente.get("/api/indicadores").json()
    assert indicadores["total"] == 3
    assert indicadores["por_status"]["aberto"] == 3
    assert indicadores["por_prioridade"] == {"baixa": 1, "media": 0, "alta": 1, "critica": 1}
    assert indicadores["falhas_integracao"] == 1
    assert indicadores["sla_vencido"] == 0
