from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from hermes_store import HermesStore
from natural_language import parse_natural_action
from telegram_bot import deliver_due_reminders, handle_update, memory_intent, memory_request_without_content
from tool_registry import ToolRegistry


class NaturalLanguageTests(unittest.TestCase):
    def test_identity_with_trailing_memory_command(self) -> None:
        self.assertEqual(memory_intent("eu sou o Caio anote na memória"), ("identidade", "eu sou o Caio"))

    def test_profile_block_with_trailing_memory_command(self) -> None:
        result = memory_intent("tenho 35 anos\ntrabalho com tecnologia\nanote na memória")
        self.assertEqual(result, ("perfil", "tenho 35 anos\ntrabalho com tecnologia"))

    def test_empty_memory_request(self) -> None:
        self.assertTrue(memory_request_without_content("anote na memória"))
        self.assertIsNone(memory_intent("anote na memória"))

    def test_natural_task(self) -> None:
        action = parse_natural_action("crie uma tarefa Publicar Hermes | revisar os testes")
        self.assertEqual(action.kind, "task_create")
        self.assertEqual(action.values["title"], "Publicar Hermes")
        self.assertEqual(action.values["description"], "revisar os testes")

    def test_relative_reminder(self) -> None:
        now = datetime(2026, 9, 12, 18, 0, tzinfo=timezone.utc)
        action = parse_natural_action("me lembre de beber água em 10 minutos", now=now)
        self.assertEqual(action.kind, "reminder_create")
        self.assertEqual(action.values["text"], "beber água")
        self.assertEqual(datetime.fromisoformat(action.values["due_at"]), now + timedelta(minutes=10))

    def test_tomorrow_reminder(self) -> None:
        now = datetime(2026, 9, 12, 18, 0, tzinfo=timezone.utc)
        action = parse_natural_action("me avise de ligar para João amanhã às 9", now=now)
        self.assertEqual(action.kind, "reminder_create")
        self.assertEqual(action.values["text"], "ligar para João")


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = HermesStore(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_profile_context_is_always_injected(self) -> None:
        self.store.remember_fact("identidade", "eu sou o Caio")
        context = self.store.context_knowledge("assunto sem relação")
        self.assertEqual(context[0]["content"], "eu sou o Caio")

    def test_identity_replaces_previous_identity(self) -> None:
        self.store.remember_fact("identidade", "eu sou o nome errado")
        self.store.remember_fact("identidade", "eu sou o Caio")
        identities = [item for item in self.store.knowledge() if item["title"] == "identidade"]
        self.assertEqual([item["content"] for item in identities], ["eu sou o Caio"])

    def test_task_lifecycle(self) -> None:
        task = self.store.add_task("Publicar", "revisar")
        completed = self.store.complete_task(task["id"][:8])
        self.assertEqual(completed["state"], "done")

    def test_due_reminder(self) -> None:
        self.store.add_reminder(123, "teste", "2026-09-12T18:00:00+00:00")
        due = self.store.due_reminders("2026-09-12T18:01:00+00:00")
        self.assertEqual(due[0]["text"], "teste")
        self.store.mark_reminder_delivered(due[0]["id"])
        self.assertEqual(self.store.due_reminders("2026-09-12T18:02:00+00:00"), [])

    def test_commands_include_session_and_reminders(self) -> None:
        self.store.pair_chat(123)
        registry = ToolRegistry(self.store)
        self.assertIn("Lembrete criado", registry.run("remind", "5 | teste"))
        self.assertIn("teste", registry.run("reminders"))

    @patch("telegram_bot.send_message")
    def test_telegram_natural_task_end_to_end(self, send_message) -> None:
        self.store.pair_chat(123)
        update = {"message": {"chat": {"id": 123}, "text": "crie uma tarefa Publicar | revisar"}}
        handle_update(update, self.store, ToolRegistry(self.store))
        self.assertEqual(self.store.tasks()[0]["title"], "Publicar")
        self.assertIn("Tarefa criada", send_message.call_args.args[1])

    @patch("telegram_bot.send_message")
    def test_reminder_delivery_end_to_end(self, send_message) -> None:
        reminder = self.store.add_reminder(123, "beber água", "2026-09-12T18:00:00+00:00")
        deliver_due_reminders(self.store)
        send_message.assert_called_once_with(123, "⏰ Lembrete: beber água")
        self.assertNotIn(reminder["id"], {item["id"] for item in self.store.due_reminders("2999-01-01T00:00:00+00:00")})


if __name__ == "__main__":
    unittest.main()
