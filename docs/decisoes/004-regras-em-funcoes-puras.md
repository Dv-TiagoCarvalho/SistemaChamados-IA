# 004: Regras de negócio ficam em funções puras

## Contexto

O prazo de atendimento e as mudanças de status permitidas são o coração do
sistema e tendem a mudar com o tempo. Se ficarem espalhados entre rotas e
tela, cada mudança vira uma caça.

## Decisão

1. `servicos/regras.py` contém funções que só recebem valores e devolvem
   valores: não acessam banco, HTTP nem relógio (a hora atual é parâmetro).
2. As mudanças de status são uma tabela (`TRANSICOES`), não uma sequência de
   `if`.
3. A API devolve `proximos_status` em cada chamado. A tela mostra os botões a
   partir dessa lista e não repete a regra.
4. Camadas: rotas (HTTP) → serviços (casos de uso) → regras, banco, IA e
   integração. Rotas não contêm regra de negócio.

## Alternativas descartadas

- Validar as mudanças de status também no front-end: resposta mais rápida na
  tela, mas a regra existiria em dois lugares e em duas linguagens.

## Consequências

- As regras são testadas em milissegundos, sem subir nada.
- Mudar um prazo ou permitir uma nova transição é alterar uma linha.
- A tela precisa de uma chamada à API para saber o que pode fazer; aqui o dado
  já vem junto com o chamado, então não há chamada extra.
