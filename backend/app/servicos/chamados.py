"""Casos de uso dos chamados. É a camada @Service: orquestra banco, regras,
IA e integração. As rotas HTTP só chamam os métodos daqui.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominio import (
    Categoria,
    OrigemClassificacao,
    Prioridade,
    SituacaoIntegracao,
    Status,
)
from app.esquemas import ChamadoCriar, Indicadores
from app.integracoes.itsm import ESTADO_PARA_STATUS, ClienteITSM, ErroIntegracao
from app.modelos import Chamado, agora
from app.servicos import regras
from app.servicos.ia import ServicoIA


class ChamadoNaoEncontrado(Exception):
    pass


class EstadoExternoDesconhecido(Exception):
    pass


class ServicoChamados:
    def __init__(self, sessao: Session, ia: ServicoIA, itsm: ClienteITSM):
        self._sessao = sessao
        self._ia = ia
        self._itsm = itsm

    # ----------------------------------------------------------- consultas

    def obter(self, chamado_id: int) -> Chamado:
        chamado = self._sessao.get(Chamado, chamado_id)
        if chamado is None:
            raise ChamadoNaoEncontrado(f"Chamado {chamado_id} não encontrado.")
        return chamado

    def listar(
        self,
        status: Status | None = None,
        prioridade: Prioridade | None = None,
        categoria: Categoria | None = None,
    ) -> list[Chamado]:
        # Chamados em andamento primeiro; dentro de cada grupo, prazo mais próximo.
        encerrado = Chamado.status.in_(regras.STATUS_ENCERRADOS)
        consulta = select(Chamado).order_by(encerrado, Chamado.prazo_sla)
        if status:
            consulta = consulta.where(Chamado.status == status)
        if prioridade:
            consulta = consulta.where(Chamado.prioridade == prioridade)
        if categoria:
            consulta = consulta.where(Chamado.categoria == categoria)
        return list(self._sessao.scalars(consulta))

    def indicadores(self) -> Indicadores:
        def contar_por(coluna) -> dict:
            linhas = self._sessao.execute(
                select(coluna, func.count()).group_by(coluna)
            ).all()
            return dict(linhas)

        por_status = contar_por(Chamado.status)
        por_prioridade = contar_por(Chamado.prioridade)

        vencidos = self._sessao.scalar(
            select(func.count())
            .select_from(Chamado)
            .where(Chamado.prazo_sla < agora())
            .where(Chamado.status.not_in(regras.STATUS_ENCERRADOS))
        )
        falhas = self._sessao.scalar(
            select(func.count())
            .select_from(Chamado)
            .where(Chamado.situacao_integracao == SituacaoIntegracao.FALHOU)
        )
        return Indicadores(
            total=sum(por_status.values()),
            por_status={s: por_status.get(s, 0) for s in Status},
            por_prioridade={p: por_prioridade.get(p, 0) for p in Prioridade},
            sla_vencido=vencidos or 0,
            falhas_integracao=falhas or 0,
        )

    # ------------------------------------------------------------ comandos

    def criar(self, dados: ChamadoCriar) -> Chamado:
        # 1. IA classifica (com plano B embutido: nunca impede a abertura).
        classificacao, origem = self._ia.classificar(dados.titulo, dados.descricao)

        # 2. Regra de negócio: o prazo depende da prioridade.
        criado_em = agora()
        chamado = Chamado(
            titulo=dados.titulo.strip(),
            descricao=dados.descricao.strip(),
            solicitante_email=dados.solicitante_email,
            status=Status.ABERTO,
            categoria=classificacao.categoria,
            prioridade=classificacao.prioridade,
            resumo=classificacao.resumo,
            justificativa=classificacao.justificativa,
            origem_classificacao=origem,
            prazo_sla=regras.calcular_prazo_sla(classificacao.prioridade, criado_em),
            criado_em=criado_em,
        )
        chamado.registrar_evento(
            "abertura",
            f"Chamado aberto. Classificado por {origem} como "
            f"{classificacao.categoria}/{classificacao.prioridade}.",
        )
        # 3. Grava antes de falar com o sistema externo: o chamado existe
        #    mesmo que a integração caia, e nenhuma transação fica aberta
        #    esperando a rede.
        self._sessao.add(chamado)
        self._sessao.commit()

        # 4. Integração.
        self._sincronizar(chamado)
        return chamado

    def alterar_status(self, chamado_id: int, novo: Status) -> Chamado:
        chamado = self.obter(chamado_id)
        regras.validar_transicao(chamado.status, novo)
        anterior = chamado.status
        chamado.status = novo
        chamado.registrar_evento("status", f"Status: {anterior} → {novo}.")
        self._sessao.commit()
        self._sincronizar(chamado)
        return chamado

    def corrigir_classificacao(
        self, chamado_id: int, categoria: Categoria, prioridade: Prioridade
    ) -> Chamado:
        """Um atendente discorda da IA e corrige (humano no controle)."""
        chamado = self.obter(chamado_id)
        chamado.categoria = categoria
        chamado.prioridade = prioridade
        chamado.origem_classificacao = OrigemClassificacao.HUMANO
        chamado.prazo_sla = regras.calcular_prazo_sla(prioridade, chamado.criado_em)
        chamado.registrar_evento(
            "classificacao", f"Classificação corrigida para {categoria}/{prioridade}."
        )
        self._sessao.commit()
        self._sincronizar(chamado)
        return chamado

    def sugerir_resposta(self, chamado_id: int) -> tuple[str, OrigemClassificacao]:
        chamado = self.obter(chamado_id)
        texto, origem = self._ia.sugerir_resposta(
            chamado.titulo, chamado.descricao, chamado.categoria
        )
        chamado.registrar_evento("sugestao", f"Sugestão de resposta gerada ({origem}).")
        self._sessao.commit()
        return texto, origem

    def sincronizar(self, chamado_id: int) -> Chamado:
        """Nova tentativa manual depois de uma falha de integração."""
        chamado = self.obter(chamado_id)
        self._sincronizar(chamado)
        return chamado

    def aplicar_webhook(self, id_externo: str, estado: str) -> Chamado:
        """O sistema externo avisou que o incidente mudou por lá."""
        novo = ESTADO_PARA_STATUS.get(estado)
        if novo is None:
            raise EstadoExternoDesconhecido(f"Estado externo desconhecido: {estado}")
        chamado = self._sessao.scalar(
            select(Chamado).where(Chamado.id_externo == id_externo)
        )
        if chamado is None:
            raise ChamadoNaoEncontrado(f"Nenhum chamado com id externo {id_externo}.")

        # Idempotência: o mesmo aviso pode chegar repetido; repetir não muda nada.
        if chamado.status != novo:
            anterior = chamado.status
            chamado.status = novo
            chamado.registrar_evento(
                "webhook", f"Status alterado pelo ITSM: {anterior} → {novo}."
            )
            # Aqui NÃO chamamos _sincronizar: devolver a mudança para quem
            # acabou de avisar criaria um vai-e-volta infinito entre os sistemas.
            self._sessao.commit()
        return chamado

    # ------------------------------------------------------------- interno

    def _sincronizar(self, chamado: Chamado) -> None:
        """Leva o estado atual do chamado ao ITSM. Falha não derruba a operação:
        fica registrada e pode ser refeita depois."""
        try:
            if chamado.id_externo is None:
                chamado.id_externo = self._itsm.registrar_chamado(
                    chamado.id, chamado.titulo, chamado.descricao, chamado.prioridade
                )
                chamado.registrar_evento(
                    "integracao", f"Registrado no ITSM como {chamado.id_externo}."
                )
                precisa_atualizar = chamado.status != Status.ABERTO
            else:
                precisa_atualizar = True
            if precisa_atualizar:
                self._itsm.atualizar_incidente(
                    chamado.id_externo, chamado.status, chamado.prioridade
                )
            chamado.situacao_integracao = SituacaoIntegracao.SINCRONIZADO
            chamado.erro_integracao = None
        except ErroIntegracao as erro:
            chamado.situacao_integracao = SituacaoIntegracao.FALHOU
            chamado.erro_integracao = str(erro)[:300]
            chamado.registrar_evento("integracao", f"Falha ao sincronizar: {erro}.")
        self._sessao.commit()
