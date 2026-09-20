# Load Test — Plataforma Aggron (Data Master)

Teste de carga com [Locust](https://locust.io) para sobrecarregar os serviços e
observar o comportamento no Grafana ao vivo.

## Subir

```bash
docker compose -f docker-compose.yaml -f docker-compose.observability.yml up -d
```

Isso sobe o stack inteiro + o serviço `loadtest` (Locust com web UI).

## Executar (web UI interativa)

1. Abrir **http://localhost:8089**
2. Definir o número de usuários e o spawn rate (ex: `50` usuários, `10/s`)
3. Clicar em **Start swarming**
4. Acompanhar em **http://localhost:3001** (painel `data-master`):
   - RPS e erros por serviço (`rate(http_requests_total[...])`)
   - Latência p95 (`histogram_quantile(0.95, ...)`)
   - CPU/memória por serviço (cAdvisor)
   - Postgres (backends, commits, blks) e Kafka (offsets/lag)

## Perfis de teste

| Perfil | Usuários | Spawn rate | Objetivo |
|---|---|---|---|
| Smoke | 5–10 | 1/s | Validar cenários, sem estresse |
| Ramp / stress | 20 → 300+ | 5–20/s | Achar o ponto de ruptura (latência/erros explodem) |
| Soak | 50 | 2/s | Rodar 10–15 min, observar degradação/latência crescente |

Estratégia: comece com 20 usuários, suba em degraus de 50 e observe
RPS/latência/erros nos painéis. O ponto onde a latência p95 dispara ou os erros
começam é o limite da stack.

## Cenários (`locustfile.py`)

- `AuthUser` — login + siglas (estressa o LDAP, bind por chamada)
- `ReaderUser` — navegação read-heavy (list, detail, referenciais, impact-analysis)
- `WriterUser` — criação de solicitações de ingestão (escrita leve → Postgres + Kafka)

Usuários rotacionam entre os 4 seedados no LDAP (`jsilva`, `amoreira`,
`rsantana`, `cgarcia` / `senha123`). O `WriterUser` publica os ids criados para
o `ReaderUser` usar no `/detail` e `/impact-analysis`.

## Observações

- Cada `POST /submit` grava uma ingestão real no Postgres e dispara eventos no
  Kafka/outbox (Debezium + cdc_consumer). Para um teste 100% sem efeito
  colateral, use apenas `AuthUser` e `ReaderUser`.
- Os serviços são alcançados pelo hostname interno da rede docker — mesmo
  caminho que o Prometheus usa para o scrape.