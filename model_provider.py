"""Model adapter configured through environment variables."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class ModelNotConfigured(RuntimeError):
    pass


class OpenAIProvider:
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def respond(self, messages: list[dict], knowledge: list[dict]) -> str:
        knowledge_text = "\n\n".join(
            f"{entry['title']}: {entry['content']}" for entry in knowledge
        ) or "Nenhum conhecimento relevante foi encontrado."
        payload = {
            "model": self.model,
            "store": False,
            "instructions": (
                "Você é Hermes, um assistente privado e local-first. "
                "Use o conhecimento fornecido, seja claro e nunca invente fatos. "
                "Não execute ações sensíveis sem confirmação explícita.\n\n"
                f"Conhecimento local:\n{knowledge_text}"
            ),
            "input": [{"role": item["role"], "content": item["content"]} for item in messages],
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"falha no provedor de modelo: {error}") from error
        if body.get("output_text"):
            return str(body["output_text"]).strip()
        for output in body.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return str(content["text"]).strip()
        raise RuntimeError("o provedor retornou uma resposta sem texto")


def provider_from_env() -> OpenAIProvider | None:
    provider = os.environ.get("HERMES_MODEL_PROVIDER", "").strip().lower()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()
    if provider in {"", "none"} or not api_key:
        return None
    if provider != "openai":
        raise ModelNotConfigured(f"provedor não suportado nesta versão: {provider}")
    if not model:
        raise ModelNotConfigured("OPENAI_MODEL não configurado")
    return OpenAIProvider(api_key, model)
