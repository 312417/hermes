#!/usr/bin/env python3
"""Minimal Telegram transport for Hermes, using only the Python stdlib."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any

from hermes_store import default_store
from model_provider import ModelNotConfigured, provider_from_env
from natural_language import NaturalAction, local_timezone, parse_natural_action
from tool_registry import ToolRegistry


API_ROOT = "https://api.telegram.org/bot"
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
PAIRING_CODE = os.environ.get("TELEGRAM_PAIRING_CODE", "").strip()
ALLOWED_IDS = {
    int(value.strip())
    for value in os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",")
    if value.strip().lstrip("-").isdigit()
}
POLL_TIMEOUT = 30


def memory_request_without_content(text: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:anote|guarde|lembre(?:-se)?|salve)(?:\s+(?:na|em|no)\s+mem[oó]ria)?[.!? ]*",
            text.strip(),
            flags=re.IGNORECASE,
        )
    )


def memory_intent(text: str) -> tuple[str, str] | None:
    """Return a durable-memory category and content for explicit memory language."""
    normalized = text.strip()
    if memory_request_without_content(normalized):
        return None
    suffix = re.search(
        r"\s+(?:anote|guarde|lembre(?:-se)?|salve)(?:\s+(?:na|em|no)\s+mem[oó]ria)?[.!? ]*$",
        normalized,
        flags=re.IGNORECASE,
    )
    if suffix:
        normalized = normalized[: suffix.start()].strip()
    explicit = re.match(
        r"^(?:anote(?:\s+na\s+mem[oó]ria)?|lembre(?:-se)?|guarde(?:\s+na\s+mem[oó]ria)?|salve(?:\s+na\s+mem[oó]ria)?)\s*(?:que\s+)?(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    identity = re.match(r"^(?:eu\s+sou|meu\s+nome\s+é|me\s+chamo)\s+(.+)$", normalized, flags=re.IGNORECASE)
    content = (explicit.group(1) if explicit else normalized if identity or suffix else "").strip()
    if not content:
        return None
    lowered = content.casefold()
    if identity or re.match(r"^(?:eu\s+sou|meu\s+nome\s+é|me\s+chamo)\b", lowered):
        category = "identidade"
    elif any(word in lowered for word in ("gosto", "prefiro", "não gosto", "nao gosto")):
        category = "preferências"
    elif any(word in lowered for word in ("meu projeto", "estou trabalhando", "trabalho com", "tenho ")):
        category = "perfil"
    else:
        category = "memória"
    return category, content.rstrip(".! ")


def format_due_at(value: str) -> str:
    from datetime import datetime

    return datetime.fromisoformat(value).astimezone(local_timezone()).strftime("%d/%m/%Y às %H:%M")


def natural_action_response(action: NaturalAction, chat_id: int, store: Any, registry: ToolRegistry) -> str:
    if action.kind == "tasks_list":
        return registry.tasks("")
    if action.kind == "reminders_list":
        return registry.reminders("")
    if action.kind == "profile":
        return registry.profile("")
    if action.kind == "task_create":
        task = store.add_task(action.values["title"], action.values.get("description", ""))
        details = f"\nDescrição: {task['description']}" if task["description"] else ""
        return f"Tarefa criada: {task['title']}{details}"
    if action.kind == "task_complete":
        task = store.complete_task(action.values["reference"])
        return f"Tarefa concluída: {task['title']}" if task else "Não encontrei essa tarefa."
    if action.kind == "reminder_needs_time":
        return "Quando devo lembrar? Exemplo: me lembre de beber água em 10 minutos."
    if action.kind == "reminder_create":
        reminder = store.add_reminder(chat_id, action.values["text"], action.values["due_at"])
        return f"Lembrete criado para {format_due_at(reminder['due_at'])}: {reminder['text']}"
    return "Não consegui interpretar essa ação."


def telegram_call(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{API_ROOT}{TOKEN}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=POLL_TIMEOUT + 15) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not body.get("ok"):
        raise RuntimeError(body.get("description", "Telegram API error"))
    return body


def send_message(chat_id: int, text: str) -> None:
    for start in range(0, len(text), 3900):
        telegram_call("sendMessage", {"chat_id": chat_id, "text": text[start : start + 3900]})


def authorized(chat_id: int, store: Any) -> bool:
    return chat_id in ALLOWED_IDS or chat_id == store.paired_chat_id()


def handle_update(update: dict[str, Any], store: Any, registry: ToolRegistry) -> None:
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    if not isinstance(chat_id, int) or not text:
        return

    if text.startswith("/pair "):
        supplied = text[6:].strip()
        if PAIRING_CODE and supplied == PAIRING_CODE and store.paired_chat_id() is None:
            store.pair_chat(chat_id)
            send_message(chat_id, "Pareamento concluído. Agora este chat pode controlar o Hermes.")
        else:
            send_message(chat_id, "Código inválido ou pareamento já concluído.")
        return

    if not authorized(chat_id, store):
        send_message(chat_id, "Este bot ainda não está autorizado para este chat.")
        return

    keep_in_session = not text.startswith("/")
    if keep_in_session:
        store.add_memory(chat_id, "user", text)

    def reply(response_text: str) -> None:
        if keep_in_session:
            store.add_memory(chat_id, "assistant", response_text)
        send_message(chat_id, response_text)

    detected_memory = memory_intent(text)
    if detected_memory:
        title, content = detected_memory
        entry = store.remember_fact(title, content)
        reply(f"Anotado na memória ({title}): {entry['content']}")
        return
    if memory_request_without_content(text):
        reply("Claro. O que você quer que eu guarde na memória?")
        return

    natural_action = parse_natural_action(text)
    if natural_action:
        reply(natural_action_response(natural_action, chat_id, store, registry))
        return

    if text in {"/start", "/help"}:
        send_message(
            chat_id,
            "Hermes ativo.\n\n"
            "/status — estado do serviço\n"
            "/task título — criar tarefa\n"
            "/tasks — listar tarefas\n"
            "/done id — concluir tarefa\n"
            "/remind minutos | texto — criar lembrete\n"
            "/reminders — listar lembretes\n"
            "/teach título | conteúdo — salvar conhecimento\n"
            "/ask termos — pesquisar conhecimento\n"
            "/remember título | conteúdo — salvar memória\n"
            "/memory — listar memórias\n"
            "/profile — mostrar perfil\n"
            "/forget id ou título — remover memória\n"
            "/clear_session — limpar conversa, preservando perfil\n"
            "/tools — listar ferramentas",
        )
    elif text == "/tools":
        send_message(chat_id, "Ferramentas: " + ", ".join(registry.names()))
    elif text.startswith("/"):
        command, _, argument = text[1:].partition(" ")
        send_message(chat_id, registry.run(command, argument))
    else:
        try:
            provider = provider_from_env()
            if provider is None:
                reply("Modelo ainda não configurado. Use /teach título | conteúdo ou configure o provedor e a chave de API no celular.")
                return
            response = provider.respond(
                store.recent_memories(chat_id), store.context_knowledge(text), prompt=text
            )
        except (ModelNotConfigured, RuntimeError) as error:
            print(f"model error: {error}", flush=True)
            reply("Não consegui consultar o modelo agora; tente novamente.")
            return
        reply(response)


def deliver_due_reminders(store: Any) -> None:
    for reminder in store.due_reminders():
        send_message(int(reminder["chat_id"]), f"⏰ Lembrete: {reminder['text']}")
        store.mark_reminder_delivered(reminder["id"])


def main() -> None:
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN não configurado")
    store = default_store()
    registry = ToolRegistry(store)
    offset = 0
    print("Hermes Telegram transport online", flush=True)
    while True:
        try:
            response = telegram_call(
                "getUpdates", {"offset": offset, "timeout": POLL_TIMEOUT, "allowed_updates": ["message"]}
            )
            for update in response.get("result", []):
                offset = max(offset, int(update["update_id"]) + 1)
                handle_update(update, store, registry)
            deliver_due_reminders(store)
        except (urllib.error.URLError, TimeoutError, OSError, RuntimeError, json.JSONDecodeError) as error:
            print(f"Telegram transport error: {error}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
