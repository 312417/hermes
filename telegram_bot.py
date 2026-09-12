#!/usr/bin/env python3
"""Minimal Telegram transport for Hermes, using only the Python stdlib."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from hermes_store import default_store
from model_provider import ModelNotConfigured, provider_from_env
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

    if text in {"/start", "/help"}:
        send_message(
            chat_id,
            "Hermes ativo.\n\n"
            "/status — estado do serviço\n"
            "/task título — criar tarefa\n"
            "/tasks — listar tarefas\n"
            "/teach título | conteúdo — salvar conhecimento\n"
            "/ask termos — pesquisar conhecimento\n"
            "/tools — listar ferramentas",
        )
    elif text == "/tools":
        send_message(chat_id, "Ferramentas: " + ", ".join(registry.names()))
    elif text.startswith("/"):
        command, _, argument = text[1:].partition(" ")
        send_message(chat_id, registry.run(command, argument))
    else:
        store.add_memory(chat_id, "user", text)
        try:
            provider = provider_from_env()
            if provider is None:
                send_message(chat_id, "Modelo ainda não configurado. Use /teach título | conteúdo ou configure HERMES_MODEL_PROVIDER e OPENAI_API_KEY no celular.")
                return
            response = provider.respond(store.recent_memories(chat_id), store.search_knowledge(text))
        except (ModelNotConfigured, RuntimeError) as error:
            print(f"model error: {error}", flush=True)
            send_message(chat_id, "Não consegui consultar o modelo agora; tente novamente.")
            return
        store.add_memory(chat_id, "assistant", response)
        send_message(chat_id, response)


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
        except (urllib.error.URLError, TimeoutError, OSError, RuntimeError, json.JSONDecodeError) as error:
            print(f"Telegram transport error: {error}", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
