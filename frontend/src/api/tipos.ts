// Tipos que espelham o contrato da API (app/esquemas.py no back-end).
// Se o back-end mudar um campo, o TypeScript acusa erro em todo lugar que o usa.

export type Status = "aberto" | "em_atendimento" | "resolvido" | "fechado";
export type Prioridade = "baixa" | "media" | "alta" | "critica";
export type Categoria = "acesso" | "hardware" | "software" | "rede" | "outros";
export type Origem = "ia" | "regra" | "humano";
export type SituacaoIntegracao = "pendente" | "sincronizado" | "falhou";

export interface ChamadoResumo {
  id: number;
  titulo: string;
  solicitante_email: string;
  status: Status;
  categoria: Categoria;
  prioridade: Prioridade;
  resumo: string;
  origem_classificacao: Origem;
  prazo_sla: string; // data em texto ISO 8601, ex.: "2026-01-05T13:00:00Z"
  sla_vencido: boolean;
  id_externo: string | null;
  situacao_integracao: SituacaoIntegracao;
  criado_em: string;
  atualizado_em: string;
}

export interface Evento {
  id: number;
  tipo: string;
  descricao: string;
  criado_em: string;
}

// "extends" reaproveita todos os campos do resumo e acrescenta os do detalhe.
export interface ChamadoDetalhe extends ChamadoResumo {
  descricao: string;
  justificativa: string;
  erro_integracao: string | null;
  proximos_status: Status[];
  eventos: Evento[];
}

export interface NovoChamado {
  titulo: string;
  descricao: string;
  solicitante_email: string;
}

export interface Filtros {
  status?: Status;
  prioridade?: Prioridade;
}

export interface Indicadores {
  total: number;
  por_status: Record<Status, number>;
  por_prioridade: Record<Prioridade, number>;
  sla_vencido: number;
  falhas_integracao: number;
}

export interface Saude {
  status: string;
  provedor_ia: string;
  modelo_ia: string | null;
}

export interface SugestaoResposta {
  texto: string;
  origem: Origem;
}
