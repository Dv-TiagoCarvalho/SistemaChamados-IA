import { useCallback, useEffect, useState } from "react";

import { api, ErroAPI } from "./api/cliente";
import type { ChamadoResumo, Filtros, Indicadores as DadosIndicadores, Saude } from "./api/tipos";
import { Ficha } from "./componentes/Ficha";
import { Fila } from "./componentes/Fila";
import { Indicadores } from "./componentes/Indicadores";
import { NovoChamado } from "./componentes/NovoChamado";

// O painel da direita mostra uma de três coisas. Este tipo ("união
// discriminada") garante que só existe `id` quando o painel é uma ficha.
type Painel = { tipo: "vazio" } | { tipo: "novo" } | { tipo: "ficha"; id: number };

const INTERVALO_ATUALIZACAO_MS = 15_000;

export default function App() {
  const [chamados, setChamados] = useState<ChamadoResumo[]>([]);
  const [indicadores, setIndicadores] = useState<DadosIndicadores | null>(null);
  const [saude, setSaude] = useState<Saude | null>(null);
  const [filtros, setFiltros] = useState<Filtros>({});
  const [painel, setPainel] = useState<Painel>({ tipo: "vazio" });
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [agora, setAgora] = useState(() => Date.now());
  const [recarga, setRecarga] = useState(0);

  const carregar = useCallback(async () => {
    try {
      // As duas chamadas saem ao mesmo tempo, em vez de uma esperar a outra.
      const [lista, numeros] = await Promise.all([
        api.listarChamados(filtros),
        api.indicadores(),
      ]);
      setChamados(lista);
      setIndicadores(numeros);
      setErro(null);
    } catch (falha) {
      setErro(falha instanceof ErroAPI ? falha.message : "Não foi possível carregar os chamados.");
    } finally {
      setCarregando(false);
      setAgora(Date.now());
      setRecarga((n) => n + 1);
    }
  }, [filtros]);

  // Carrega ao abrir, ao mudar um filtro e depois a cada 15 segundos. É assim
  // que uma mudança vinda do ITSM (webhook) aparece sem recarregar a página.
  useEffect(() => {
    void carregar();
    const temporizador = setInterval(() => void carregar(), INTERVALO_ATUALIZACAO_MS);
    return () => clearInterval(temporizador);
  }, [carregar]);

  useEffect(() => {
    api.saude().then(setSaude).catch(() => setSaude(null));
  }, []);

  const selecionado = painel.tipo === "ficha" ? painel.id : null;

  return (
    <div className="pagina">
      <header className="topo">
        <div>
          <h1>Central de Chamados</h1>
          {saude && (
            <p className="topo__ia">
              {saude.provedor_ia === "simulado"
                ? "Classificação por regras automáticas (IA simulada)"
                : `Classificação por IA generativa (${saude.modelo_ia ?? saude.provedor_ia})`}
            </p>
          )}
        </div>
        <button
          type="button"
          className="botao botao--principal"
          onClick={() => setPainel({ tipo: "novo" })}
        >
          Abrir chamado
        </button>
      </header>

      <Indicadores dados={indicadores} />

      {erro && (
        <p className="erro erro--pagina" role="alert">
          {erro}
        </p>
      )}

      <main className={painel.tipo === "vazio" ? "colunas" : "colunas colunas--com-painel"}>
        <Fila
          chamados={chamados}
          carregando={carregando}
          filtros={filtros}
          selecionado={selecionado}
          agora={agora}
          aoFiltrar={setFiltros}
          aoSelecionar={(id) => setPainel({ tipo: "ficha", id })}
        />

        <div className="painel">
          {painel.tipo === "vazio" && (
            <p className="painel__vazio">Selecione um chamado na fila para ver os detalhes.</p>
          )}
          {painel.tipo === "novo" && (
            <NovoChamado
              aoCancelar={() => setPainel({ tipo: "vazio" })}
              aoCriar={(chamado) => {
                setPainel({ tipo: "ficha", id: chamado.id });
                void carregar();
              }}
            />
          )}
          {painel.tipo === "ficha" && (
            // key: ao trocar de chamado o React cria uma ficha nova, zerando
            // rascunho e formulário de correção do chamado anterior.
            <Ficha
              key={painel.id}
              id={painel.id}
              agora={agora}
              recarga={recarga}
              aoMudar={() => void carregar()}
              aoFechar={() => setPainel({ tipo: "vazio" })}
            />
          )}
        </div>
      </main>
    </div>
  );
}
