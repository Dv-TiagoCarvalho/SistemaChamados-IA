# Decisões de arquitetura

Cada arquivo registra uma decisão: o problema, o que foi escolhido, o que foi
descartado e o preço da escolha. O formato é conhecido como ADR (Architecture
Decision Record).

| Nº | Decisão |
|---|---|
| [001](001-ia-atras-de-interface.md) | A IA fica atrás de uma interface, com validação e plano B |
| [002](002-integracao-nao-bloqueia.md) | Falha de integração não impede a operação |
| [003](003-webhook-assinado.md) | Webhooks são autenticados com HMAC e são idempotentes |
| [004](004-regras-em-funcoes-puras.md) | Regras de negócio ficam em funções puras |
