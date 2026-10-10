import { useEffect, useState } from "react";

import { api, ErroAPI } from "../api/cliente";
import type { Categoria, ChamadoDetalhe, Prioridade, Status } from "../api/tipos";
import {
  CATEGORIAS,
  dataHora,
  NOME_CATEGORIA,
  NOME_ORIGEM,
  NOME_PRIORIDADE,
  NOME_STATUS,
  PRIORIDADES,
} from "../formatos";
import { Prazo } from "./Prazo";

interface Props {
  id: number;
  agora: number;
  recarga: number; // muda a cada atualização automática da tela
  aoMudar: () => void; // avisa o App para recarregar fila e indicadores
  aoFechar: () => void;
}

/** O nome do botão depende de onde o chamado está e para onde vai. */
function nomeDaAcao(atual: Status, destino: Status): string {
  switch (destino) {
    case "em_atendimento":
      return atual === "resolvido" ? "Reabrir chamado" : "Iniciar atendimento";
    case "resolvido":
      return "Marcar como resolvido";
    case "fechado":
      return "Fechar chamado";
    case "aberto":
      return "Devolver para a fila";
  }
}

export function Ficha({ id, agora, recarga, aoMudar, aoFechar }: Props) {
  const [chamado, setChamado] = useState<ChamadoDetalhe | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const [corrigindo, setCorrigindo] = useState(false);
  const [categoria, setCategoria] = useState<Categoria>("outros");
  const [prioridade, setPrioridade] = useState<Prioridade>("media");

  const [rascunho, setRascunho] = useState("");
  const [copiado, setCopiado] = useState(false);

  // Busca o chamado quando a ficha abre e a cada atualização automática.
  useEffect(() => {
    let ativo = true; // evita gravar a resposta se a ficha já foi trocada
    api
      .obterChamado(id)
      .then((dados) => ativo && setChamado(dados))
      .catch((falha: unknown) => ativo && setErro(mensagem(falha)));
    return () => {
      ativo = false;
    };
  }, [id, recarga]);

  /** Executa uma ação na API e atualiza a tela com o chamado devolvido. */
  async function executar(acao: () => Promise<ChamadoDetalhe>) {
    setOcupado(true);
    setErro(null);
    try {
      setChamado(await acao());
      aoMudar();
    } catch (falha) {
      setErro(mensagem(falha));
    } finally {
      setOcupado(false);
    }
  }

  async function gerarRascunho() {
    setOcupado(true);
    setErro(null);
    try {
      const sugestao = await api.sugerirResposta(id);
      setRascunho(sugestao.texto);
      setCopiado(false);
    } catch (falha) {
      setErro(mensagem(falha));
    } finally {
      setOcupado(false);
    }
  }

  async function copiarRascunho() {
    await navigator.clipboard.writeText(rascunho);
    setCopiado(true);
  }

  if (!chamado) {
    return (
      <article className="ficha">
        <p className={erro ? "erro" : ""} role={erro ? "alert" : undefined}>
          {erro ?? "Carregando chamado…"}
        </p>
      </article>
    );
  }

  return (
    <article className={`ficha ficha--${chamado.prioridade}`}>
      <button type="button" className="ficha__voltar" onClick={aoFechar}>
        Voltar para a fila
      </button>

      <header className="ficha__cabecalho">
        <p className="ficha__numero">
          Chamado #{chamado.id}
          <span className="selo selo--status">{NOME_STATUS[chamado.status]}</span>
        </p>
        <h2>{chamado.titulo}</h2>
        <p className="ficha__meta">
          Aberto por {chamado.solicitante_email} em {dataHora(chamado.criado_em)}
        </p>
      </header>

      <Prazo
        criadoEm={chamado.criado_em}
        prazo={chamado.prazo_sla}
        status={chamado.status}
        agora={agora}
      />

      {erro && (
        <p className="erro" role="alert">
          {erro}
        </p>
      )}

      {chamado.proximos_status.length > 0 && (
        <div className="acoes">
          {chamado.proximos_status.map((destino, indice) => (
            <button
              key={destino}
              type="button"
              className={indice === 0 ? "botao botao--principal" : "botao"}
              disabled={ocupado}
              onClick={() => executar(() => api.alterarStatus(id, destino))}
            >
              {nomeDaAcao(chamado.status, destino)}
            </button>
          ))}
        </div>
      )}

      <section>
        <h3>Descrição</h3>
        <p className="ficha__descricao">{chamado.descricao}</p>
      </section>

      <section>
        <h3>Classificação</h3>
        {corrigindo ? (
          <form
            className="correcao"
            onSubmit={(evento) => {
              evento.preventDefault();
              void executar(() => api.corrigirClassificacao(id, categoria, prioridade));
              setCorrigindo(false);
            }}
          >
            <label>
              Categoria
              <select value={categoria} onChange={(e) => setCategoria(e.target.value as Categoria)}>
                {CATEGORIAS.map((c) => (
                  <option key={c} value={c}>
                    {NOME_CATEGORIA[c]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Prioridade
              <select
                value={prioridade}
                onChange={(e) => setPrioridade(e.target.value as Prioridade)}
              >
                {PRIORIDADES.map((p) => (
                  <option key={p} value={p}>
                    {NOME_PRIORIDADE[p]}
                  </option>
                ))}
              </select>
            </label>
            <div className="acoes">
              <button type="submit" className="botao botao--principal" disabled={ocupado}>
                Salvar correção
              </button>
              <button type="button" className="botao" onClick={() => setCorrigindo(false)}>
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <>
            <p className="classificacao">
              <span className={`selo selo--${chamado.prioridade}`}>
                Prioridade {NOME_PRIORIDADE[chamado.prioridade].toLowerCase()}
              </span>
              <span className="selo">{NOME_CATEGORIA[chamado.categoria]}</span>
            </p>
            <p className="ficha__meta">
              Definida por {NOME_ORIGEM[chamado.origem_classificacao]}.
              {chamado.origem_classificacao !== "humano" && ` ${chamado.justificativa}`}
            </p>
            <button
              type="button"
              className="botao"
              onClick={() => {
                setCategoria(chamado.categoria);
                setPrioridade(chamado.prioridade);
                setCorrigindo(true);
              }}
            >
              Corrigir classificação
            </button>
          </>
        )}
      </section>

      <section>
        <h3>Sistema corporativo (ITSM)</h3>
        {chamado.situacao_integracao === "sincronizado" && (
          <p>Sincronizado como {chamado.id_externo}.</p>
        )}
        {chamado.situacao_integracao === "pendente" && <p>Aguardando envio ao ITSM.</p>}
        {chamado.situacao_integracao === "falhou" && (
          <>
            <p className="erro">
              O ITSM não recebeu a última alteração: {chamado.erro_integracao}. O chamado continua
              salvo aqui.
            </p>
            <button
              type="button"
              className="botao"
              disabled={ocupado}
              onClick={() => executar(() => api.sincronizar(id))}
            >
              Sincronizar de novo
            </button>
          </>
        )}
      </section>

      <section>
        <h3>Resposta ao solicitante</h3>
        {rascunho ? (
          <>
            <label>
              Rascunho (revise antes de enviar)
              <textarea rows={5} value={rascunho} onChange={(e) => setRascunho(e.target.value)} />
            </label>
            <div className="acoes">
              <button type="button" className="botao botao--principal" onClick={copiarRascunho}>
                {copiado ? "Rascunho copiado" : "Copiar rascunho"}
              </button>
              <button type="button" className="botao" disabled={ocupado} onClick={gerarRascunho}>
                Gerar outro rascunho
              </button>
            </div>
          </>
        ) : (
          <button type="button" className="botao" disabled={ocupado} onClick={gerarRascunho}>
            Gerar rascunho de resposta
          </button>
        )}
      </section>

      <section>
        <h3>Histórico</h3>
        <ol className="historico">
          {chamado.eventos.map((evento) => (
            <li key={evento.id}>
              <time dateTime={evento.criado_em}>{dataHora(evento.criado_em)}</time>
              <span>{evento.descricao}</span>
            </li>
          ))}
        </ol>
      </section>
    </article>
  );
}

function mensagem(falha: unknown): string {
  return falha instanceof ErroAPI ? falha.message : "Algo deu errado. Tente de novo.";
}
