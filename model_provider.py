"""Model providers and a small local policy router for Hermes."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone


class ModelNotConfigured(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelRoute:
    name: str
    model: str
    reasoning_effort: str | None = None


class GroqRouter:
    """Choose a Groq model locally; no request content is routed elsewhere."""

    def __init__(self) -> None:
        self.routes = {
            "fast": ModelRoute("fast", os.environ.get("HERMES_FAST_MODEL", "openai/gpt-oss-20b"), "low"),
            "text": ModelRoute("text", os.environ.get("HERMES_TEXT_MODEL", "llama-3.3-70b-versatile")),
            "think": ModelRoute("think", os.environ.get("HERMES_THINK_MODEL", "openai/gpt-oss-120b"), "high"),
            "research": ModelRoute("research", os.environ.get("HERMES_RESEARCH_MODEL", "groq/compound")),
        }

    def choose(self, prompt: str) -> tuple[ModelRoute, str]:
        text = prompt.strip()
        lowered = text.casefold()
        for name in self.routes:
            marker = f"#{name}"
            if lowered.startswith(marker):
                return self.routes[name], text[len(marker) :].lstrip(" :,-")

        research_words = ("pesquise", "pesquisa", "na web", "internet", "notícia", "noticias", "hoje", "atual", "cotação", "cotacao")
        think_words = ("planeje", "planejar", "plano", "analise", "análise", "racioc", "estratég", "arquitet", "compare", "decida", "tarefa")
        text_words = ("escreva", "redija", "reescreva", "texto", "descrição", "descricao", "copy", "email", "mensagem", "legenda")

        if any(word in lowered for word in research_words):
            return self.routes["research"], text
        if any(word in lowered for word in think_words):
            return self.routes["think"], text
        if any(word in lowered for word in text_words):
            return self.routes["text"], text
        return self.routes["fast"], text


class OpenAIResponsesProvider:
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def respond(self, messages: list[dict], knowledge: list[dict], prompt: str | None = None) -> str:
        knowledge_text = _knowledge_text(knowledge)
        payload = {
            "model": self.model,
            "store": False,
            "instructions": _instructions(knowledge_text),
            "input": [{"role": item["role"], "content": item["content"]} for item in messages],
        }
        body = _post_json(self.endpoint, self.api_key, payload)
        if body.get("output_text"):
            return str(body["output_text"]).strip()
        for output in body.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return str(content["text"]).strip()
        raise RuntimeError("o provedor retornou uma resposta sem texto")


class GroqProvider:
    endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.router = GroqRouter()

    def respond(self, messages: list[dict], knowledge: list[dict], prompt: str | None = None) -> str:
        route, cleaned_prompt = self.router.choose(prompt or messages[-1]["content"])
        history = [{"role": item["role"], "content": item["content"]} for item in messages[:-1]]
        history.append({"role": "user", "content": cleaned_prompt})
        payload: dict = {
            "model": route.model,
            "messages": [{"role": "system", "content": _instructions(_knowledge_text(knowledge))}, *history],
            "temperature": 0.35,
        }
        if route.reasoning_effort:
            payload["reasoning_effort"] = route.reasoning_effort
            payload["reasoning_format"] = "hidden"
        body = _post_json(self.endpoint, self.api_key, payload)
        choices = body.get("choices") or []
        content = choices[0].get("message", {}).get("content") if choices else None
        if content:
            return str(content).strip()
        raise RuntimeError("o Groq retornou uma resposta sem texto")


def _knowledge_text(knowledge: list[dict]) -> str:
    return "\n\n".join(f"{entry['title']}: {entry['content']}" for entry in knowledge) or "Nenhum conhecimento relevante foi encontrado."


def _instructions(knowledge_text: str) -> str:
    return (
        "Você é Hermes, um assistente privado e local-first. "
        "Responda em português do Brasil, seja claro, útil e conciso. "
        "Use o conhecimento fornecido e não invente fatos. "
        "Você possui sessão persistente, perfil, memória permanente, tarefas e lembretes no servidor Hermes. "
        "Nunca diga que não consegue guardar memória: quando o usuário pedir para lembrar, a camada de ações do Hermes cuida disso. "
        f"Data UTC atual: {datetime.now(timezone.utc).isoformat()}. "
        "Não afirme executar ações externas ou sensíveis; peça confirmação explícita.\n\n"
        f"Conhecimento local:\n{knowledge_text}"
    )


def _post_json(endpoint: str, api_key: str, payload: dict) -> dict:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Hermes/0.2",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"falha no provedor de modelo: {error}") from error


def provider_from_env() -> OpenAIResponsesProvider | GroqProvider | None:
    provider = os.environ.get("HERMES_MODEL_PROVIDER", "").strip().lower()
    if provider in {"", "none"}:
        return None
    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        model = os.environ.get("OPENAI_MODEL", "").strip()
        if not api_key:
            return None
        if not model:
            raise ModelNotConfigured("OPENAI_MODEL não configurado")
        return OpenAIResponsesProvider(api_key, model)
    if provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            return None
        return GroqProvider(api_key)
    raise ModelNotConfigured(f"provedor não suportado nesta versão: {provider}")
