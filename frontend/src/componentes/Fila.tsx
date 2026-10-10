import type { ChamadoResumo, Filtros, Prioridade, Status } from "../api/tipos";
import {
  NOME_CATEGORIA,
  NOME_PRIORIDADE,
  NOME_STATUS,
  PRIORIDADES,
  TODOS_STATUS,
} from "../formatos";
import { Prazo } from "./Prazo";

interface Props {
  chamados: ChamadoResumo[];
  carregando: boolean;
  filtros: Filtros;
  selecionado: number | null;
  agora: number;
  aoFiltrar: (filtros: Filtros) => void;
  aoSelecionar: (id: number) => void;
}

export function Fila(props: Props) {
  const { chamados, carregando, filtros, selecionado, agora, aoFiltrar, aoSelecionar } = props;
  const filtrando = Boolean(filtros.status || filtros.prioridade);

  return (
    <section className="fila" aria-label="Fila de chamados">
      <div className="fila__filtros">
        <label>
          Status
          <select
            value={filtros.status ?? ""}
            onChange={(e) =>
              // "" vira undefined: filtro desligado
              aoFiltrar({ ...filtros, status: (e.target.value || undefined) as Status | undefined })
            }
          >
            <option value="">Todos</option>
            {TODOS_STATUS.map((s) => (
              <option key={s} value={s}>
                {NOME_STATUS[s]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Prioridade
          <select
            value={filtros.prioridade ?? ""}
            onChange={(e) =>
              aoFiltrar({
                ...filtros,
                prioridade: (e.target.value || undefined) as Prioridade | undefined,
              })
            }
          >
            <option value="">Todas</option>
            {PRIORIDADES.map((p) => (
              <option key={p} value={p}>
                {NOME_PRIORIDADE[p]}
              </option>
            ))}
          </select>
        </label>
      </div>

      {carregando && <p className="fila__aviso">Carregando chamados…</p>}

      {!carregando && chamados.length === 0 && (
        <p className="fila__aviso">
          {filtrando
            ? "Nenhum chamado com esses filtros."
            : "A fila está vazia. Abra um chamado para começar."}
        </p>
      )}

      <ul className="fila__lista">
        {chamados.map((chamado) => (
          <li key={chamado.id}>
            <button
              type="button"
              className={`item item--${chamado.prioridade}`}
              aria-current={chamado.id === selecionado ? "true" : undefined}
              onClick={() => aoSelecionar(chamado.id)}
            >
              <span className="item__topo">
                <span className="item__numero">#{chamado.id}</span>
                <span className="item__titulo">{chamado.titulo}</span>
                <span className={`selo selo--${chamado.prioridade}`}>
                  {NOME_PRIORIDADE[chamado.prioridade]}
                </span>
              </span>
              <span className="item__meta">
                <span>{NOME_STATUS[chamado.status]}</span>
                <span>{NOME_CATEGORIA[chamado.categoria]}</span>
                {chamado.situacao_integracao === "falhou" && (
                  <span className="item__falha">Falha de integração</span>
                )}
              </span>
              <Prazo
                criadoEm={chamado.criado_em}
                prazo={chamado.prazo_sla}
                status={chamado.status}
                agora={agora}
              />
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
