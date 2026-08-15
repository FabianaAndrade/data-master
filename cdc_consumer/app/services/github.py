from __future__ import annotations

import base64
import logging
import time
import requests

from ..config import Config

logger = logging.getLogger(__name__)


class GithubPushRepos:
    BASE_URL = "https://api.github.com"

    def __init__(self, org: str = None, token: str = None):
        self.org = org or Config.GITHUB_ORG
        self.token = token or Config.GITHUB_TOKEN

    def _headers(self) -> dict:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

    def create_from_template(self, name: str,
                             template_repo: str = "repo-template") -> dict:
        """
        Cria um repositório privado na organização a partir de um template.

        O template já contém a GitHub Action de validação de Data Contract,
        então o novo repo herda automaticamente o workflow.

        Args:
            name: nome do novo repositório.
            template_repo: nome do repo template na org (default: 'repo-template').

        Returns:
            Resposta da API do GitHub.
        """
        url = f"{self.BASE_URL}/repos/{self.org}/{template_repo}/generate"
        payload = {
            "owner": self.org,
            "name": name,
            "private": True,
            "include_all_branches": False,
        }
        response = requests.post(url, headers=self._headers(), json=payload)
        logger.info("GitHub create repo from template [%s] — status=%s",
                    name, response.status_code)

        if response.status_code >= 400:
            logger.error("GitHub API error: %s", response.text)
            return {"error": response.status_code, "message": response.text}

        return response.json()

    def _create_empty_repo(self, name: str) -> dict:
        """Fallback: cria um repositório vazio (sem template)."""
        url = f"{self.BASE_URL}/orgs/{self.org}/repos"
        payload = {
            "name": name,
            "private": True,
            "auto_init": True,
        }
        response = requests.post(url, headers=self._headers(), json=payload)
        logger.info("GitHub create empty repo [%s] — status=%s",
                    name, response.status_code)

        if response.status_code >= 400:
            logger.error("GitHub API error: %s", response.text)
            return {"error": response.status_code, "message": response.text}

        return response.json()

    def _get_file_sha(self, repo: str, file_path: str) -> str | None:
        """
        Obtém o SHA de um arquivo existente no repositório.
        Necessário para atualizar arquivos via Contents API.

        Returns:
            SHA do arquivo ou None se não existir.
        """
        url = f"{self.BASE_URL}/repos/{self.org}/{repo}/contents/{file_path}"
        response = requests.get(url, headers=self._headers())
        if response.status_code == 200:
            return response.json().get("sha")
        return None

    def push_file(self, repo: str, file_path: str, content: str,
                  commit_message: str = "Add data contract") -> dict:
        """
        Cria ou atualiza um arquivo no repositório via Contents API.
        Se o arquivo já existir, obtém o SHA para permitir a atualização.

        Args:
            repo: nome do repositório (já criado na org).
            file_path: caminho do arquivo dentro do repo (ex: 'datacontract.yaml').
            content: conteúdo do arquivo (texto).
            commit_message: mensagem do commit.

        Returns:
            Resposta da API do GitHub.
        """
        url = f"{self.BASE_URL}/repos/{self.org}/{repo}/contents/{file_path}"

        # A Contents API exige o conteúdo em base64
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": commit_message,
            "content": content_b64,
        }

        # Se o arquivo já existe (ex: vindo do template), inclui o SHA
        # para que a API permita a atualização
        sha = self._get_file_sha(repo, file_path)
        if sha:
            payload["sha"] = sha
            logger.info("Arquivo [%s] já existe, atualizando (sha=%s)",
                        file_path, sha[:8])

        response = requests.put(url, headers=self._headers(), json=payload)
        logger.info("GitHub push file [%s/%s] — status=%s",
                    repo, file_path, response.status_code)

        if response.status_code >= 400:
            logger.error("GitHub API error: %s", response.text)
            return {"error": response.status_code, "message": response.text}

        return response.json()

    def create_repo_with_contract(self, table_name: str, contract_yaml: str,
                                     team_slug: str = "mkti") -> dict:
        """
        Fluxo completo: cria o repo, faz push do data contract YAML
        e associa ao time da organização.

        Args:
            table_name: nome da tabela (usado como nome do repo).
            contract_yaml: conteúdo YAML do data contract.
            team_slug: slug do time para associar o repo (default: 'mkti').

        Returns:
            Dict com os resultados de cada etapa.
        """
        team_slug = team_slug.split('-')[0].strip().lower()

        # 1. Cria o repositório a partir do template (herda a action de validação)
        repo_result = self.create_from_template(table_name)
        if "error" in repo_result:
            return repo_result

        # Aguarda o GitHub finalizar a geração do repo a partir do template
        # (a API /generate é assíncrona)
        logger.info("Aguardando geração do repo a partir do template...")
        time.sleep(5)

        # 2. Sobrescreve o datacontract.yaml do template com o contrato real
        file_result = self.push_file(
            repo=table_name,
            file_path="datacontract.yaml",
            content=contract_yaml,
            commit_message=f"feat: add data contract for {table_name}",
        )

        if "error" in file_result:
            return file_result

        # 3. Associa o repo ao time da organização
        team_result = self.associate_team_repos(
            team_slug=team_slug,
            owner=self.org,
            repo=table_name,
        )

        return {
            "repo": repo_result.get("html_url", ""),
            "file": file_result.get("content", {}).get("html_url", ""),
            "team": team_result,
        }

    def list_teams_from_organization(self) -> list:
        """Lista os times da organização."""
        url = f"{self.BASE_URL}/orgs/{self.org}/teams"
        response = requests.get(url, headers=self._headers())
        if response.status_code >= 400:
            logger.error("GitHub API error: %s", response.text)
            return {"error": response.status_code, "message": response.text}
        return response.json()

    def associate_team_repos(self, team_slug: str, owner: str, repo: str) -> dict:
        """Associa um repositório a um time da organização."""
        print(team_slug)
        url = f"{self.BASE_URL}/orgs/{self.org}/teams/{team_slug}/repos/{owner}/{repo}"
        payload = {
            "permission": "pull",
        }
        response = requests.put(url, headers=self._headers(), json=payload)
        logger.info("GitHub associate team [%s] → repo [%s/%s] — status=%s",
                    team_slug, owner, repo, response.status_code)

        if response.status_code >= 400:
            logger.error("GitHub API error: %s", response.text)
            return {"error": response.status_code, "message": response.text}

        # PUT pode retornar 204 No Content (sucesso sem body)
        if response.status_code == 204:
            return {"status": "ok"}

        return response.json()
