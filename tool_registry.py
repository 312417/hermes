"""Explicit, low-risk tools exposed to Hermes clients."""

from __future__ import annotations

from collections.abc import Callable

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
        }

    def names(self) -> list[str]:
        return sorted(self._tools)

    def run(self, name: str, argument: str = "") -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Ferramenta desconhecida. Disponíveis: {', '.join(self.names())}"
        return tool(argument.strip())

    def status(self, _argument: str) -> str:
        return f"tarefas={len(self.store.tasks())} conhecimento={len(self.store.knowledge())}"

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
