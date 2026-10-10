# 001: A IA fica atrás de uma interface, com validação e plano B

## Contexto

O sistema usa um modelo de linguagem para classificar chamados. Modelos de
linguagem trocam de versão e de preço com frequência, podem ficar indisponíveis
e não garantem o formato da resposta.

## Decisão

1. O resto do sistema fala com a classe abstrata `ProvedorIA`. Cada fornecedor
   é uma implementação (`ProvedorAnthropic`, `ProvedorSimulado`).
2. A resposta do modelo passa pelo esquema `Classificacao` (Pydantic). Categoria
   ou prioridade fora da lista conhecida é rejeitada.
3. Se o modelo falhar ou responder fora do formato, `ServicoIA` usa o
   classificador por palavras-chave e grava `origem_classificacao = "regra"`.
4. O texto do chamado vai para o modelo entre tags `<chamado>`, com instrução de
   tratá-lo como dado.
5. Um atendente pode corrigir a classificação; a origem passa a ser `"humano"`.

## Alternativas descartadas

- Chamar o SDK do fornecedor direto no serviço de chamados: mais curto, mas
  trocar de fornecedor exigiria mexer na regra de negócio, e os testes
  dependeriam de rede.
- Recusar a abertura do chamado quando a IA falha: o usuário ficaria sem
  atendimento por causa de um componente auxiliar.

## Consequências

- Trocar de modelo é mudar uma variável de ambiente; trocar de fornecedor é
  escrever uma classe.
- Os testes rodam sem chave de API e sem custo.
- O classificador por palavras-chave é fraco. Ele existe para o sistema não
  parar, não para substituir o modelo.
- A instrução contra texto malicioso reduz o risco, mas não o elimina. Por isso
  a IA só classifica e sugere: nenhuma ação é executada a partir do que ela
  escreve sem passar por validação ou por uma pessoa.
