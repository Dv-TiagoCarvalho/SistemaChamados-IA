# Contrato da API

Base: `http://localhost:8000`. Todas as respostas são JSON em UTF-8. Datas vêm
em ISO 8601 no fuso UTC, por exemplo `2026-10-10T16:09:26Z`.

A especificação completa no formato OpenAPI está em [`openapi.json`](openapi.json)
e pode ser explorada em `http://localhost:8000/docs` com a API ligada. Para
gerar o arquivo de novo depois de mudar a API:

```bash
cd backend
python -c "import json; from app.main import app; open('../docs/openapi.json','w').write(json.dumps(app.openapi(), ensure_ascii=False, indent=2))"
```

## Valores fixos

| Campo | Valores |
|---|---|
| `status` | `aberto`, `em_atendimento`, `resolvido`, `fechado` |
| `prioridade` | `baixa`, `media`, `alta`, `critica` |
| `categoria` | `acesso`, `hardware`, `software`, `rede`, `outros` |
| `origem_classificacao` | `ia` (modelo de linguagem), `regra` (palavras-chave), `humano` (corrigido por atendente) |
| `situacao_integracao` | `pendente`, `sincronizado`, `falhou` |

## Rotas

| Método | Caminho | O que faz | Sucesso |
|---|---|---|---|
| GET | `/api/saude` | Diz se a API está de pé e qual provedor de IA está ativo | 200 |
| GET | `/api/indicadores` | Totais por status e prioridade, prazos vencidos e falhas de integração | 200 |
| POST | `/api/chamados` | Abre um chamado | 201 |
| GET | `/api/chamados` | Lista chamados. Filtros opcionais: `status`, `prioridade`, `categoria` | 200 |
| GET | `/api/chamados/{id}` | Detalhe com histórico | 200 |
| PATCH | `/api/chamados/{id}/status` | Muda o status | 200 |
| PATCH | `/api/chamados/{id}/classificacao` | Corrige categoria e prioridade; recalcula o prazo | 200 |
| POST | `/api/chamados/{id}/sugestao-resposta` | Gera um rascunho de resposta ao solicitante | 200 |
| POST | `/api/chamados/{id}/sincronizar` | Tenta de novo a integração com o ITSM | 200 |
| POST | `/api/webhooks/itsm` | Recebe mudança de estado vinda do ITSM | 200 |

## Erros

Todo erro tem o campo `detail`.

| Código | Quando |
|---|---|
| 401 | Webhook sem assinatura ou com assinatura inválida |
| 404 | Chamado não encontrado |
| 409 | Mudança de status não permitida |
| 422 | Dados de entrada inválidos, ou estado desconhecido no webhook |

```json
{ "detail": "Não é possível ir de 'aberto' para 'fechado'. Permitidos: em_atendimento." }
```

## Abrir chamado

`POST /api/chamados`

```json
{
  "titulo": "VPN não conecta",
  "descricao": "Desde cedo a VPN não conecta e não consigo trabalhar de casa. É urgente.",
  "solicitante_email": "ana@empresa.com"
}
```

Limites: `titulo` de 3 a 120 caracteres, `descricao` de 10 a 4000,
`solicitante_email` em formato de e-mail.

Resposta `201`:

```json
{
  "id": 2,
  "titulo": "VPN não conecta",
  "solicitante_email": "ana@empresa.com",
  "status": "aberto",
  "categoria": "rede",
  "prioridade": "alta",
  "resumo": "VPN não conecta",
  "origem_classificacao": "regra",
  "prazo_sla": "2026-10-10T18:09:26.822449Z",
  "sla_vencido": false,
  "id_externo": "INC-0002",
  "situacao_integracao": "sincronizado",
  "criado_em": "2026-10-10T10:09:26.822449Z",
  "atualizado_em": "2026-10-10T10:09:26.828248Z",
  "descricao": "Desde cedo a VPN não conecta e não consigo trabalhar de casa. É urgente.",
  "justificativa": "Classificado por palavras-chave: categoria pelo termo 'vpn' e prioridade pelo termo 'urgente'.",
  "erro_integracao": null,
  "proximos_status": ["em_atendimento"],
  "eventos": [
    { "id": 4, "tipo": "abertura", "descricao": "Chamado aberto. Classificado por regra como rede/alta.", "criado_em": "2026-10-10T10:09:26.823297Z" },
    { "id": 5, "tipo": "integracao", "descricao": "Registrado no ITSM como INC-0002.", "criado_em": "2026-10-10T10:09:26.826641Z" }
  ]
}
```

Se o ITSM estiver fora do ar, a resposta continua sendo `201`, com
`situacao_integracao: "falhou"`, `id_externo: null` e o motivo em
`erro_integracao`.

A listagem (`GET /api/chamados`) devolve os mesmos campos, menos `descricao`,
`justificativa`, `erro_integracao`, `proximos_status` e `eventos`.

## Mudar status

`PATCH /api/chamados/{id}/status` com `{ "status": "em_atendimento" }`.

Mudanças permitidas:

| De | Para |
|---|---|
| `aberto` | `em_atendimento` |
| `em_atendimento` | `resolvido`, `aberto` |
| `resolvido` | `fechado`, `em_atendimento` (reabertura) |
| `fechado` | nenhuma |

O campo `proximos_status` do chamado já traz a lista válida para o status
atual, com o passo natural do fluxo em primeiro lugar.

## Prazo de atendimento

| Prioridade | Prazo a partir da abertura |
|---|---|
| `critica` | 4 horas |
| `alta` | 8 horas |
| `media` | 24 horas |
| `baixa` | 72 horas |

`sla_vencido` é `true` quando o prazo passou e o chamado ainda não está
`resolvido` nem `fechado`.

## Integração com o ITSM

### O que a API envia

| Situação | Chamada ao ITSM |
|---|---|
| Chamado aberto | `POST /incidentes` com cabeçalho `Idempotency-Key: chamado-{id}` |
| Status ou classificação alterados | `PATCH /incidentes/{number}` |

Tradução de campos:

| Central de Chamados | ITSM |
|---|---|
| `titulo` | `short_description` |
| `descricao` | `description` |
| `prioridade` `critica` / `alta` / `media` / `baixa` | `urgency` 1 / 2 / 3 / 4 |
| `status` `aberto` / `em_atendimento` / `resolvido` / `fechado` | `state` `NEW` / `IN_PROGRESS` / `RESOLVED` / `CLOSED` |
| `id_externo` | `number` |

Cada chamada é tentada até 2 vezes quando o ITSM não responde ou devolve erro
5xx. Erros 4xx não são repetidos.

### O que a API recebe (webhook)

`POST /api/webhooks/itsm`

```json
{ "evento": "incidente.atualizado", "id_externo": "INC-0002", "estado": "RESOLVED" }
```

Cabeçalho obrigatório: `X-Assinatura: sha256=<hex>`, onde `<hex>` é o
HMAC-SHA256 dos bytes exatos do corpo, calculado com o segredo compartilhado
(`ITSM_SEGREDO_WEBHOOK`).

Regras:

- O status do chamado passa a ser o correspondente ao `estado` recebido.
- Receber o mesmo aviso duas vezes não altera nada na segunda vez.
- A mudança recebida não é reenviada ao ITSM.
