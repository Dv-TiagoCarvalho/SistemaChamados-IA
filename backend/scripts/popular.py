"""Cria chamados de exemplo para a tela não começar vazia.

Rode com (a partir da pasta backend): python -m scripts.popular
Se o ITSM simulado estiver ligado, os chamados já nascem sincronizados.
"""

from datetime import timedelta

from app.banco import Base, FabricaDeSessao, engine
from app.dependencias import obter_cliente_itsm, obter_servico_ia
from app.dominio import Status
from app.esquemas import ChamadoCriar
from app.servicos.chamados import ServicoChamados

# (título, descrição, e-mail, horas atrás em que foi aberto, status final)
EXEMPLOS = [
    ("Sistema de vendas fora do ar", "Ninguém consegue emitir pedidos, o sistema está parado para todos da filial.", "carla@empresa.com", 5, Status.EM_ATENDIMENTO),
    ("VPN não conecta", "Desde cedo a VPN não conecta e não consigo trabalhar de casa. É urgente.", "ana@empresa.com", 2, Status.ABERTO),
    ("Senha bloqueada no ERP", "Errei a senha três vezes e meu usuário foi bloqueado.", "joao@empresa.com", 1, Status.ABERTO),
    ("Notebook não liga", "O notebook não liga mesmo na tomada. A luz do carregador acende.", "paula@empresa.com", 30, Status.EM_ATENDIMENTO),
    ("Instalar leitor de PDF", "Preciso instalar um leitor de PDF para abrir os contratos.", "rafael@empresa.com", 20, Status.RESOLVIDO),
    ("Dúvida sobre planilha", "Gostaria de saber como compartilhar uma planilha com o time, quando puder.", "bia@empresa.com", 3, Status.ABERTO),
]

CAMINHO = [Status.EM_ATENDIMENTO, Status.RESOLVIDO, Status.FECHADO]


def main() -> None:
    Base.metadata.create_all(engine)
    with FabricaDeSessao() as sessao:
        servico = ServicoChamados(sessao, obter_servico_ia(), obter_cliente_itsm())
        if servico.listar():
            print("O banco já tem chamados; nada foi criado.")
            return
        for titulo, descricao, email, horas_atras, status_final in EXEMPLOS:
            chamado = servico.criar(
                ChamadoCriar(titulo=titulo, descricao=descricao, solicitante_email=email)
            )
            # Finge que o chamado foi aberto há algumas horas, para o painel
            # mostrar prazos em andamento e um prazo vencido.
            recuo = timedelta(hours=horas_atras)
            chamado.criado_em -= recuo
            chamado.prazo_sla -= recuo
            sessao.commit()
            for status in CAMINHO:
                if chamado.status == status_final:
                    break
                servico.alterar_status(chamado.id, status)
            print(f"#{chamado.id} {chamado.titulo} -> {chamado.prioridade}, {chamado.situacao_integracao}")


if __name__ == "__main__":
    main()
