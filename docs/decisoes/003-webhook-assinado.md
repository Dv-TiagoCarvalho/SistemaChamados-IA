# 003: Webhooks são autenticados com HMAC e são idempotentes

## Contexto

Quando um técnico altera o incidente dentro do ITSM, a Central de Chamados
precisa saber. Perguntar ao ITSM de tempos em tempos gera muitas chamadas
inúteis; o ITSM avisar por webhook é mais eficiente. Mas a rota de webhook fica
exposta, e avisos podem chegar repetidos.

## Decisão

1. O ITSM envia `X-Assinatura: sha256=<HMAC-SHA256 do corpo>` usando um segredo
   compartilhado. A API recalcula e compara em tempo constante
   (`hmac.compare_digest`). Sem assinatura válida, responde 401.
2. A assinatura é conferida sobre os bytes brutos, antes de interpretar o JSON.
3. Se o chamado já está no status recebido, nada é alterado.
4. Uma mudança recebida por webhook não é reenviada ao ITSM.

## Alternativas descartadas

- Token fixo no cabeçalho: prova quem enviou, mas não protege o conteúdo contra
  alteração no caminho.
- Aplicar a máquina de estados local ao webhook: o ITSM é a fonte da mudança;
  recusar o aviso só deixaria os dois sistemas diferentes.

## Consequências

- Quem descobrir a URL não consegue alterar chamados sem o segredo.
- Reenvios do ITSM são inofensivos.
- Não há vai-e-volta infinito entre os sistemas.
- Não há proteção contra repetição de um aviso antigo capturado (replay). A
  evolução é incluir data e hora no corpo assinado e recusar avisos velhos.
