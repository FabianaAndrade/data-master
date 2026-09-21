"""
Load test da plataforma Aggron (Data Master).

Cenários simulam usuários reais da plataforma:
  - AuthUser  : login e consultas de sigla -> estressa o LDAP (bind por chamada)
  - ReaderUser: navegação read-heavy -> ingestion -> metadata -> Postgres / DCM
  - WriterUser: cria solicitações de ingestão (escrita leve) -> Postgres + Kafka

Como rodar (web UI interativa):
  docker compose -f docker-compose.yaml -f docker-compose.observability.yml up -d
  Abrir http://localhost:8089, definir nº de usuários e spawn rate, Start swarming.
  Acompanhar em http://localhost:3001 (painel "data-master").

Os serviços são alcançados pelo hostname interno da rede docker, mesmo caminho
que o Prometheus usa.
"""
import random
import uuid

from locust import HttpUser, between, task


AUTH_URL = "http://auth_service:8000"
INGESTION_URL = "http://ingestion_service:8001"
APPROVAL_URL = "http://approval_service:8003"

# Usuários LDAP seedados no servidor (ldap/50-bootstrap.ldif)
# (username, senha, sigla, gestor aprovador da sigla)
USERS = [
    ("jsilva", "senha123", "MKTI", "jsilva"),
    ("amoreira", "senha123", "MKTI", "jsilva"),
    ("rsantana", "senha123", "FIN", "rsantana"),
    ("cgarcia", "senha123", "FIN", "rsantana"),
]

FONTES = ["SAP", "Oracle", "Salesforce", "MySQL", "SQLServer", "Postgres"]
FORMATOS = ["csv", "parquet", "json"]

# ids de ingestão criados pelo WriterUser e reutilizados pelo ReaderUser
SHARED_INGESTION_IDS: list[int] = []


def _login(client, username: str, password: str) -> str | None:
    """Autentica contra o auth_service e retorna o JWT."""
    resp = client.post(
        f"{AUTH_URL}/auth/login",
        json={"username": username, "password": password},
    )
    if resp.status_code == 200:
        return resp.json().get("token")
    return None


def _build_ingestion_payload(username: str, sigla: str, gestor: str) -> dict:
    """Monta um FullIngestionRequest válido com nomes únicos por execução."""
    table = f"loadtest_{uuid.uuid4().hex[:8]}"
    return {
        "sigla": {"sigla": sigla, "gestorAprovador": gestor},
        "fonte": {
            "sistemaOrigem": random.choice(FONTES),
            "formatoArquivo": random.choice(FORMATOS),
        },
        "metadados": {
            "nomeTabela": table,
            "periodicidade": random.choice(["Diária", "Semanal", "Mensal"]),
            "tipoIngestao": random.choice(["Batch", "Micro-Batch"]),
            "camada": "RAW",
        },
        "colunas": {
            "numColunas": "2",
            "colunas": [
                {"nome": "id", "dataType": "bigint", "chavePrimaria": "Sim", "pii": "Não", "piiType": ""},
                {"nome": "nome", "dataType": "varchar", "chavePrimaria": "Não", "pii": "Não", "piiType": ""},
            ],
            "colunaParticao": "",
        },
        "dicionarizacao": {
            "descricaoTabela": f"Tabela gerada pelo load test ({table})",
            "colunas": [
                {"coluna": "id", "descricao": "Identificador único"},
                {"coluna": "nome", "descricao": "Nome do registro"},
            ],
        },
        "qualidade": {"configurar": "Não", "colunas": []},
    }


class AuthUser(HttpUser):
    wait_time = between(0.5, 2)
    weight = 2

    def on_start(self):
        self.username, self.password, *_ = random.choice(USERS)

    @task(3)
    def login(self):
        token = _login(self.client, self.username, self.password)
        if token is None:
            self.client.post(  # registra falha de forma explícita no report
                f"{AUTH_URL}/auth/login",
                json={"username": self.username, "password": self.password},
                name="auth/login (falha)",
            )

    @task(1)
    def get_siglas(self):
        self.client.get(f"{AUTH_URL}/auth/siglas", name="/auth/siglas")

    @task(1)
    def get_user_siglas(self):
        self.client.get(f"{AUTH_URL}/auth/siglas/{self.username}", name="/auth/siglas/{username}")


class ReaderUser(HttpUser):
    wait_time = between(0.5, 2)
    weight = 5

    def on_start(self):
        self.username, self.password, *_ = random.choice(USERS)
        self.token = _login(self.client, self.username, self.password)
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _random_ingestion_id(self) -> int | None:
        if SHARED_INGESTION_IDS:
            return random.choice(SHARED_INGESTION_IDS)
        # fallback: pega o primeiro id da listagem
        resp = self.client.get(f"{INGESTION_URL}/ingestion/list", headers=self.headers)
        ingestions = (resp.json().get("ingestions") or []) if resp.status_code == 200 else []
        return ingestions[0].get("ingestion_id") if ingestions else None

    @task(3)
    def list_ingestions(self):
        self.client.get(f"{INGESTION_URL}/ingestion/list", headers=self.headers)

    @task(2)
    def account_stats(self):
        self.client.get(f"{INGESTION_URL}/ingestion/account-stats", headers=self.headers)

    @task(2)
    def detail(self):
        ingestion_id = self._random_ingestion_id()
        if ingestion_id is not None:
            self.client.get(
                f"{INGESTION_URL}/ingestion/detail/{ingestion_id}",
                headers=self.headers,
                name="/ingestion/detail/{id}",
            )

    @task(1)
    def impact_analysis(self):
        # pesado: ingestion -> DCM (data products / acessos)
        ingestion_id = self._random_ingestion_id()
        if ingestion_id is not None:
            self.client.get(
                f"{INGESTION_URL}/ingestion/impact-analysis/{ingestion_id}",
                headers=self.headers,
                name="/ingestion/impact-analysis/{id}",
            )

    @task(1)
    def reference_siglas(self):
        self.client.get(f"{INGESTION_URL}/ingestion/siglas", headers=self.headers)

    @task(1)
    def reference_fontes(self):
        self.client.get(f"{INGESTION_URL}/ingestion/fontes", headers=self.headers)

    @task(1)
    def reference_tabelas(self):
        fonte = random.choice(FONTES)
        self.client.get(
            f"{INGESTION_URL}/ingestion/tabelas/{fonte}",
            headers=self.headers,
            name="/ingestion/tabelas/{fonte}",
        )

    @task(1)
    def reference_metadados(self):
        self.client.get(
            f"{INGESTION_URL}/ingestion/metadados/tabela_teste",
            headers=self.headers,
            name="/ingestion/metadados/{tabela}",
        )

    @task(1)
    def approvals_pending(self):
        if self.username in ("jsilva", "rsantana"):  # apenas owners têm pendências
            self.client.get(
                f"{APPROVAL_URL}/api/v1/approvals/pending",
                headers=self.headers,
                name="approvals/pending",
            )


class WriterUser(HttpUser):
    wait_time = between(1, 3)
    weight = 1

    def on_start(self):
        self.username, self.password, self.sigla, self.gestor = random.choice(USERS)
        self.token = _login(self.client, self.username, self.password)
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(4)
    def submit_ingestion(self):
        payload = _build_ingestion_payload(self.username, self.sigla, self.gestor)
        resp = self.client.post(
            f"{INGESTION_URL}/ingestion/submit",
            json=payload,
            headers=self.headers,
        )
        if resp.status_code == 200:
            ingestion_id = resp.json().get("ingestion_id")
            if ingestion_id:
                SHARED_INGESTION_IDS.append(ingestion_id)

    @task(1)
    def list_ingestions(self):
        self.client.get(f"{INGESTION_URL}/ingestion/list", headers=self.headers)