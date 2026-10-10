// Único lugar do front-end que sabe falar HTTP com a API.
// Os componentes chamam api.algumaCoisa() e recebem dados já tipados.

import type {
  Categoria,
  ChamadoDetalhe,
  ChamadoResumo,
  Filtros,
  Indicadores,
  NovoChamado,
  Prioridade,
  Saude,
  Status,
  SugestaoResposta,
} from "./tipos";

export class ErroAPI extends Error {
  constructor(
    public codigo: number,
    mensagem: string,
  ) {
    super(mensagem);
  }
}

// <T> é um tipo genérico: quem chama diz qual formato espera receber.
async function requisitar<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(`/api${caminho}`, {
      ...opcoes,
      headers: { "Content-Type": "application/json", ...opcoes.headers },
    });
  } catch {
    throw new ErroAPI(0, "Sem conexão com a API. Confira se o back-end está ligado.");
  }
  if (!resposta.ok) {
    throw new ErroAPI(resposta.status, await lerMensagemDeErro(resposta));
  }
  return (await resposta.json()) as T;
}

async function lerMensagemDeErro(resposta: Response): Promise<string> {
  try {
    const corpo: unknown = await resposta.json();
    if (typeof corpo === "object" && corpo !== null && "detail" in corpo) {
      const detalhe = corpo.detail;
      if (typeof detalhe === "string") return detalhe;
      // Erro de validação (422): a API devolve uma lista de campos com problema.
      if (Array.isArray(detalhe)) {
        return detalhe.map((item: { msg?: string }) => item.msg ?? "").join(" ");
      }
    }
  } catch {
    // corpo não era JSON; cai na mensagem genérica abaixo
  }
  return `A API respondeu com erro ${resposta.status}.`;
}

function enviar(metodo: "POST" | "PATCH", corpo?: unknown): RequestInit {
  return { method: metodo, body: corpo === undefined ? undefined : JSON.stringify(corpo) };
}

export const api = {
  saude: () => requisitar<Saude>("/saude"),

  indicadores: () => requisitar<Indicadores>("/indicadores"),

  listarChamados: (filtros: Filtros) => {
    const parametros = new URLSearchParams();
    if (filtros.status) parametros.set("status", filtros.status);
    if (filtros.prioridade) parametros.set("prioridade", filtros.prioridade);
    const consulta = parametros.toString();
    return requisitar<ChamadoResumo[]>(`/chamados${consulta ? `?${consulta}` : ""}`);
  },

  obterChamado: (id: number) => requisitar<ChamadoDetalhe>(`/chamados/${id}`),

  criarChamado: (dados: NovoChamado) =>
    requisitar<ChamadoDetalhe>("/chamados", enviar("POST", dados)),

  alterarStatus: (id: number, status: Status) =>
    requisitar<ChamadoDetalhe>(`/chamados/${id}/status`, enviar("PATCH", { status })),

  corrigirClassificacao: (id: number, categoria: Categoria, prioridade: Prioridade) =>
    requisitar<ChamadoDetalhe>(
      `/chamados/${id}/classificacao`,
      enviar("PATCH", { categoria, prioridade }),
    ),

  sugerirResposta: (id: number) =>
    requisitar<SugestaoResposta>(`/chamados/${id}/sugestao-resposta`, enviar("POST")),

  sincronizar: (id: number) =>
    requisitar<ChamadoDetalhe>(`/chamados/${id}/sincronizar`, enviar("POST")),
};
