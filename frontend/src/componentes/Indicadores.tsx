import type { Indicadores as DadosIndicadores } from "../api/tipos";

interface Props {
  dados: DadosIndicadores | null;
}

export function Indicadores({ dados }: Props) {
  const itens = [
    { rotulo: "Abertos", valor: dados?.por_status.aberto, alerta: false },
    { rotulo: "Em atendimento", valor: dados?.por_status.em_atendimento, alerta: false },
    { rotulo: "Com prazo vencido", valor: dados?.sla_vencido, alerta: true },
    { rotulo: "Com falha de integração", valor: dados?.falhas_integracao, alerta: true },
  ];

  return (
    <dl className="indicadores" aria-label="Resumo da fila">
      {itens.map((item) => (
        <div
          key={item.rotulo}
          className={item.alerta && item.valor ? "indicador indicador--alerta" : "indicador"}
        >
          <dd>{item.valor ?? "–"}</dd>
          <dt>{item.rotulo}</dt>
        </div>
      ))}
    </dl>
  );
}
