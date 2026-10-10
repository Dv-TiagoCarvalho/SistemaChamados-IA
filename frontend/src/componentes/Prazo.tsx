import type { Status } from "../api/tipos";
import { chamadoEncerrado, duracao } from "../formatos";

interface Props {
  criadoEm: string;
  prazo: string;
  status: Status;
  agora: number; // relógio vindo do App, em milissegundos
}

/** Barra que enche conforme o prazo de atendimento (SLA) é consumido. */
export function Prazo({ criadoEm, prazo, status, agora }: Props) {
  if (chamadoEncerrado(status)) {
    return <p className="prazo prazo--parado">Prazo parado: chamado resolvido</p>;
  }

  const inicio = new Date(criadoEm).getTime();
  const fim = new Date(prazo).getTime();
  const consumido = Math.min(1, Math.max(0, (agora - inicio) / (fim - inicio)));
  const vencido = agora > fim;
  const apertado = !vencido && consumido >= 0.75;

  const classe = vencido ? "prazo--vencido" : apertado ? "prazo--apertado" : "";
  const texto = vencido
    ? `Prazo vencido há ${duracao(agora - fim)}`
    : `Vence em ${duracao(fim - agora)}`;

  return (
    <div className={`prazo ${classe}`}>
      <div
        className="prazo__trilho"
        role="progressbar"
        aria-label="Prazo de atendimento consumido"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(consumido * 100)}
      >
        <div className="prazo__barra" style={{ width: `${consumido * 100}%` }} />
      </div>
      <p className="prazo__texto">{texto}</p>
    </div>
  );
}
