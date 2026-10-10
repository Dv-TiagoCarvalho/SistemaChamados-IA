// Textos e contas de data usados em mais de um componente.

import type { Categoria, Origem, Prioridade, Status } from "./api/tipos";

// Record<Status, string> obriga a ter um texto para CADA status:
// se um status novo for criado e esquecido aqui, o projeto não compila.
export const NOME_STATUS: Record<Status, string> = {
  aberto: "Aberto",
  em_atendimento: "Em atendimento",
  resolvido: "Resolvido",
  fechado: "Fechado",
};

export const NOME_PRIORIDADE: Record<Prioridade, string> = {
  critica: "Crítica",
  alta: "Alta",
  media: "Média",
  baixa: "Baixa",
};

export const NOME_CATEGORIA: Record<Categoria, string> = {
  acesso: "Acesso",
  hardware: "Hardware",
  software: "Software",
  rede: "Rede",
  outros: "Outros",
};

export const NOME_ORIGEM: Record<Origem, string> = {
  ia: "IA generativa",
  regra: "regras automáticas",
  humano: "uma pessoa",
};

export const PRIORIDADES = Object.keys(NOME_PRIORIDADE) as Prioridade[];
export const CATEGORIAS = Object.keys(NOME_CATEGORIA) as Categoria[];
export const TODOS_STATUS = Object.keys(NOME_STATUS) as Status[];

const formatoDataHora = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

export function dataHora(iso: string): string {
  return formatoDataHora.format(new Date(iso));
}

/** Transforma milissegundos em "3 h 20 min", "45 min" ou "2 d 4 h". */
export function duracao(ms: number): string {
  const minutos = Math.max(1, Math.round(Math.abs(ms) / 60_000));
  if (minutos < 60) return `${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 24) {
    const resto = minutos % 60;
    return resto ? `${horas} h ${resto} min` : `${horas} h`;
  }
  const dias = Math.floor(horas / 24);
  const restoHoras = horas % 24;
  return restoHoras ? `${dias} d ${restoHoras} h` : `${dias} d`;
}

export function chamadoEncerrado(status: Status): boolean {
  return status === "resolvido" || status === "fechado";
}
