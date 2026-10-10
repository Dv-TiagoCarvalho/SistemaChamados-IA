import { type FormEvent, useState } from "react";

import { api, ErroAPI } from "../api/cliente";
import type { ChamadoDetalhe } from "../api/tipos";

interface Props {
  aoCriar: (chamado: ChamadoDetalhe) => void;
  aoCancelar: () => void;
}

export function NovoChamado({ aoCriar, aoCancelar }: Props) {
  const [titulo, setTitulo] = useState("");
  const [descricao, setDescricao] = useState("");
  const [email, setEmail] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function abrir(evento: FormEvent) {
    evento.preventDefault(); // impede o navegador de recarregar a página
    setEnviando(true);
    setErro(null);
    try {
      const chamado = await api.criarChamado({
        titulo,
        descricao,
        solicitante_email: email,
      });
      aoCriar(chamado);
    } catch (falha) {
      setErro(falha instanceof ErroAPI ? falha.message : "Não foi possível abrir o chamado.");
      setEnviando(false);
    }
  }

  return (
    <form className="ficha formulario" onSubmit={abrir}>
      <h2>Abrir chamado</h2>
      <p className="formulario__ajuda">
        Categoria, prioridade e prazo são definidos automaticamente a partir do texto. Você pode
        corrigir depois.
      </p>

      <label>
        Título
        <input
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          required
          minLength={3}
          maxLength={120}
          placeholder="Ex.: VPN não conecta"
        />
      </label>

      <label>
        O que está acontecendo
        <textarea
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          required
          minLength={10}
          maxLength={4000}
          rows={6}
          placeholder="Descreva o problema, desde quando ocorre e quem é afetado."
        />
      </label>

      <label>
        E-mail de quem pediu
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          placeholder="nome@empresa.com"
        />
      </label>

      {erro && (
        <p className="erro" role="alert">
          {erro}
        </p>
      )}

      <div className="acoes">
        <button type="submit" className="botao botao--principal" disabled={enviando}>
          {enviando ? "Abrindo…" : "Abrir chamado"}
        </button>
        <button type="button" className="botao" onClick={aoCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  );
}
