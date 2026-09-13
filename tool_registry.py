"""Explicit, low-risk tools exposed to Hermes clients."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from hermes_store import HermesStore


class ToolRegistry:
    def __init__(self, store: HermesStore) -> None:
        self.store = store
        self._tools: dict[str, Callable[[str], str]] = {
            "status": self.status,
            "task": self.task,
            "tasks": self.tasks,
            "teach": self.teach,
            "ask": self.ask,
            "remember": self.remember,
            "memory": self.memory,
            "profile": self.profile,
            "forget": self.forget,
            "remind": self.remind,
            "reminders": self.reminders,
            "done": self.done,
            "clear_session": self.clear_session,
        }

    def names(self) -> list[str]:
        return sorted(self._tools)

    def run(self, name: str, argument: str = "") -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Ferramenta desconhecida. Disponíveis: {', '.join(self.names())}"
        return tool(argument.strip())

    def status(self, _argument: str) -> str:
        chat_id = self.store.paired_chat_id()
        reminder_count = len(self.store.reminders(chat_id)) if chat_id is not None else 0
        return f"tarefas={len(self.store.tasks())} lembretes={reminder_count} conhecimento={len(self.store.knowledge())}"

    def task(self, argument: str) -> str:
        if not argument:
            return "Uso: /task título | descrição opcional"
        title, separator, description = argument.partition("|")
        title = title.strip()
        if not title:
            return "O título da tarefa é obrigatório."
        task = self.store.add_task(title, description if separator else "")
        details = f"\nDescrição: {task['description']}" if task["description"] else ""
        return f"Tarefa criada: {task['id']} — {task['title']}{details}"

    def tasks(self, _argument: str) -> str:
        tasks = self.store.tasks()
        if not tasks:
            return "Nenhuma tarefa cadastrada."
        return "\n".join(
            f"• {task['id'][:8]} [{task['state']}] {task['title']}"
            f" — {task['description']}" if task.get("description") else
            f"• {task['id'][:8]} [{task['state']}] {task['title']}"
            for task in tasks[-20:]
        )

    def teach(self, argument: str) -> str:
        if "|" not in argument:
            return "Uso: /teach título | conteúdo"
        title, content = (part.strip() for part in argument.split("|", 1))
        if not title or not content:
            return "Título e conteúdo são obrigatórios."
        entry = self.store.teach(title, content)
        return f"Conhecimento salvo: {entry['id']} — {entry['title']}"

    def ask(self, argument: str) -> str:
        if not argument:
            return "Uso: /ask termos para pesquisar"
        matches = self.store.search_knowledge(argument)
        if not matches:
            return "Ainda não encontrei isso na base de conhecimento. Use /teach para me ensinar."
        return "\n\n".join(
            f"{entry['title']}\n{entry['content']}" for entry in matches
        )

    def remember(self, argument: str) -> str:
        if "|" not in argument:
            return "Uso: /remember título | conteúdo"
        title, content = (part.strip() for part in argument.split("|", 1))
        if not title or not content:
            return "Título e conteúdo são obrigatórios."
        entry = self.store.teach(title, content)
        return f"Memória salva: {entry['id']} — {entry['title']}"

    def memory(self, _argument: str) -> str:
        entries = self.store.knowledge()
        if not entries:
            return "A memória está vazia."
        return "\n\n".join(
            f"{entry['id'][:8]} — {entry['title']}: {entry['content']}"
            for entry in entries[-30:]
        )

    def profile(self, _argument: str) -> str:
        entries = [
            entry for entry in self.store.knowledge()
            if entry["title"].casefold() in {"identidade", "perfil", "preferências", "projetos"}
        ]
        if not entries:
            return "Ainda não tenho um perfil salvo."
        return "\n\n".join(f"{entry['title']}: {entry['content']}" for entry in entries)

    def forget(self, argument: str) -> str:
        if not argument:
            return "Uso: /forget id ou título exato"
        entry = self.store.delete_knowledge(argument)
        if not entry:
            return "Não encontrei essa memória."
        return f"Memória removida: {entry['title']}"

    def remind(self, argument: str) -> str:
        if "|" not in argument:
            return "Uso: /remind minutos | texto do lembrete"
        minutes_text, reminder_text = (part.strip() for part in argument.split("|", 1))
        if not minutes_text.isdigit() or not reminder_text:
            return "Informe os minutos e o texto. Exemplo: /remind 10 | beber água"
        chat_id = self.store.paired_chat_id()
        if chat_id is None:
            return "O chat ainda não está pareado."
        due_at = (datetime.now(timezone.utc) + timedelta(minutes=int(minutes_text))).isoformat()
        reminder = self.store.add_reminder(chat_id, reminder_text, due_at)
        return f"Lembrete criado: {reminder['id'][:8]} — {reminder['text']}"

    def reminders(self, _argument: str) -> str:
        chat_id = self.store.paired_chat_id()
        if chat_id is None:
            return "O chat ainda não está pareado."
        reminders = self.store.reminders(chat_id)
        if not reminders:
            return "Nenhum lembrete pendente."
        return "\n".join(
            f"• {item['id'][:8]} — {item['due_at']} — {item['text']}" for item in reminders[-20:]
        )

    def done(self, argument: str) -> str:
        if not argument:
            return "Uso: /done id da tarefa"
        task = self.store.complete_task(argument)
        if not task:
            return "Não encontrei essa tarefa."
        return f"Tarefa concluída: {task['title']}"

    def clear_session(self, _argument: str) -> str:
        chat_id = self.store.paired_chat_id()
        if chat_id is None:
            return "O chat ainda não está pareado."
        count = self.store.clear_session(chat_id)
        return f"Sessão limpa: {count} mensagens removidas. O perfil e as memórias permanentes foram preservados."
