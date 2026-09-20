# README – Frontend (Aggron)

Interface web da plataforma Data Master, responsável por criação/edição/exclusão de tabelas no data lake, fluxo de aprovação e histórico de ingestões.

## Tecnologias empregadas

| Camada | Tecnologia |
|---|---|
| Linguagem | TypeScript 5 |
| Framework | React 18 (SPA) |
| Build / dev server | Vite 5 + SWC (`@vitejs/plugin-react-swc`) |
| Estilização | Tailwind CSS 3 + `tailwindcss-animate` |
| UI components | shadcn/ui sobre Radix UI (dialog, select, toast, etc.) |
| Rotas | react-router-dom 6 |
| Server state/data fetching | @tanstack/react-query |
| Formulários e validação | react-hook-form + zod + @hookform/resolvers |
| Gráficos | recharts |
| Toasts | sonner |
| Ícones | lucide-react |
| Datas | date-fns |
| Testes | Vitest + Testing Library + jsdom |
| Lint | ESLint 9 (typescript-eslint, react-hooks) |

Containnerização: build multi-stage `Dockerfile` (node:20-alpine → build → nginx:1.27-alpine), servindo o bundle na porta **3000** com fallback SPA (`try_files ... /index.html`).

## Execução

```sh
npm ci          # instala dependências
npm run dev     # dev server na porta 8080 (vite.config.ts)
npm run build   # bundle de produção em /dist
npm run test    # testes com Vitest
npm run lint    # ESLint
```

## Integração com os backends

O frontend consome HTTP APIs REST via `fetch`, com configuração por variáveis de ambiente (arquivo `.env`, já no `.gitignore`). Os URLs padrão correspondem aos serviços publicados no `docker-compose.yaml`:

| Variável de ambiente | Padrão | Serviço | Exemplos de endpoints usados |
|---|---|---|---|
| `VITE_AUTH_SERVICE_URL` | `http://localhost:8000` | `auth_service` | `POST /auth/login` |
| `VITE_INGESTION_SERVICE_URL` | `http://localhost:8001` | `ingestion_service` | `/ingestion/siglas`, `/ingestion/fontes`, `/ingestion/tabelas/formato/{sistema}`, `/ingestion/colunas/{tabela}`, `/ingestion/coluna/particao/{tabela}`, `/ingestion/dicionario/sugerir`, `/ingestion/quality_rules/{tabela}`, `/ingestion/metadados/{tabela}`, `/ingestion/submit`, `/ingestion/list?username=`, `/ingestion/detail/{id}`, `/ingestion/edit/{id}`, `/ingestion/delete/{id}`, `/ingestion/cancel/{id}`, `/ingestion/impact-analysis/{id}`, `/ingestion/account-stats` |
| `VITE_APPROVAL_SERVICE_URL` | `http://localhost:8003` | `approval_service` | `GET /api/v1/approvals/pending`, `POST /api/v1/approvals/{id}/approve`, `POST /api/v1/approvals/{id}/reject` |

### Autenticação

- Login via `auth_service` (que valida credenciais no servidor **LDAP**); o token JWT retornado é persistido em `localStorage` (`auth_user`) pelo contexto `AuthProvider` (`src/hooks/use-auth.tsx`).
- Todas as chamadas autenticadas enviam `Authorization: Bearer <token>`.
- Rotas protegidas pelo componente `ProtectedRoute`; respostas `401` limpam a sessão e redirecionam para `/login`.
- Usuários visualizam apenas dados das suas siglas (owners definidos no LDAP).

### Resumo do fluxo

1. Usuário faz login e cria uma solicitação de tabela (wizard com etapas: sigla, fonte, colunas, dicionarização, qualidade, metadados).
2. A solicitação fica `PENDING_APPROVAL` e pode ser cancelada pelo solicitante.
3. Owner da sigla aprova/reprova pelo `approval_service` (com parecer), visualizando metadados completos vindos do `ingestion_service`.
4. Após aprovação, o `cdc_consumer` (Kafka/Debezium) orquestra a criação real da tabela; status e histórico são refletidos na UI.