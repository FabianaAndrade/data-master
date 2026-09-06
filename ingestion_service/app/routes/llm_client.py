import json
import os

import httpx


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


async def generate_dictionary(table: str, columns: list[str]) -> dict:
	prompt = f"""Voce e especialista em governanca de dados.
            Gere descricoes curtas, objetivas e em portugues para a tabela e suas colunas.

            Nao invente regras de negocio e nao inclua dados que nao estejam nos nomes.
            Retorne somente JSON valido, sem markdown, neste formato:
            {{
            \"descricaoTabela\": \"...\",
            \"colunas\": [
                {{\"nome\": \"nome_da_coluna\", \"descricao\": \"...\"}}
            ]
            }}

            Tabela: {table}
            Colunas: {", ".join(columns)}"""

	async with httpx.AsyncClient(timeout=90.0) as client:
		response = await client.post(
			f"{OLLAMA_URL}/api/generate",
			json={
				"model": OLLAMA_MODEL,
				"prompt": prompt,
				"format": "json",
				"stream": False,
			},
		)
		response.raise_for_status()

	result = response.json().get("response", "")
	try:
		data = json.loads(result)
	except json.JSONDecodeError as exc:
		raise ValueError("Ollama retornou uma resposta que nao e JSON valido") from exc

	generated_columns = data.get("colunas")
	if not isinstance(data.get("descricaoTabela"), str) or not isinstance(generated_columns, list):
		raise ValueError("Resposta do Ollama fora do formato esperado")

	return data
