# 002: Falha de integração não impede a operação

## Contexto

Todo chamado precisa existir também no ITSM da empresa. O ITSM é um sistema
externo: pode estar lento, em manutenção ou fora do ar.

## Decisão

1. O chamado é gravado no banco antes da chamada ao ITSM.
2. O resultado da integração fica no próprio chamado, em `situacao_integracao`
   (`pendente`, `sincronizado`, `falhou`) e `erro_integracao`.
3. Cada chamada ao ITSM é tentada 2 vezes para erros de rede e 5xx.
4. A criação envia `Idempotency-Key: chamado-{id}`, para que uma repetição não
   crie incidente duplicado.
5. A rota `POST /api/chamados/{id}/sincronizar` refaz a integração sob demanda.

## Alternativas descartadas

- Uma única transação que só confirma se o ITSM responder: simples de
  raciocinar, mas o ITSM fora do ar derrubaria a abertura de chamados, e a
  transação do banco ficaria aberta esperando a rede.
- Fila de mensagens com tentativas automáticas em segundo plano: é a solução
  mais robusta, mas exige outro serviço rodando. Fica como evolução.

## Consequências

- O usuário sempre consegue abrir o chamado.
- Os dois sistemas podem ficar temporariamente diferentes. A tela mostra isso e
  o indicador "com falha de integração" permite acompanhar.
- A nova tentativa depende de alguém clicar. Com mais volume, o próximo passo é
  um processo em segundo plano que refaz as pendências.
