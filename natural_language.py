"""Deterministic Portuguese intent parsing for common Hermes actions."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class NaturalAction:
    kind: str
    values: dict[str, str] = field(default_factory=dict)


def local_timezone():
    try:
        return ZoneInfo(os.environ.get("HERMES_TIMEZONE", "America/Sao_Paulo"))
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=-3))


def parse_natural_action(text: str, now: datetime | None = None) -> NaturalAction | None:
    normalized = " ".join(text.strip().split())
    lowered = normalized.casefold().rstrip(".!?")

    if re.fullmatch(r"(?:quais|liste|mostre)(?: são)? (?:as )?minhas tarefas", lowered):
        return NaturalAction("tasks_list")
    if re.fullmatch(r"(?:quais|liste|mostre)(?: são)? (?:os )?meus lembretes", lowered):
        return NaturalAction("reminders_list")
    if lowered in {"quem sou eu", "o que você sabe sobre mim", "o que voce sabe sobre mim", "mostre meu perfil", "meu perfil"}:
        return NaturalAction("profile")

    task = re.match(
        r"^(?:(?:crie|adicione|anote|registre)(?: uma)? (?:tarefa|task)|(?:eu )?preciso fazer|tenho que)\s*[:\-]?\s*(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if task:
        body = task.group(1).strip()
        title, separator, description = body.partition("|")
        if not separator and ":" in body:
            title, description = (part.strip() for part in body.split(":", 1))
        return NaturalAction("task_create", {"title": title.strip(), "description": description.strip()})

    completed = re.match(
        r"^(?:conclua|finalize|marque como conclu[ií]da)(?: a)? (?:tarefa|task)\s+([0-9a-f-]{4,})$",
        lowered,
    )
    if completed:
        return NaturalAction("task_complete", {"reference": completed.group(1)})

    reminder = re.match(
        r"^(?:me (?:lembre|avise)|crie(?: um)? lembrete|lembrete)\s*[:\-]?\s*(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if reminder:
        body = re.sub(r"^de\s+", "", reminder.group(1).strip(), flags=re.IGNORECASE)
        due_at, reminder_text = parse_due_time(body, now=now)
        if due_at is None:
            return NaturalAction("reminder_needs_time", {"text": reminder_text})
        return NaturalAction(
            "reminder_create",
            {"text": reminder_text, "due_at": due_at.astimezone(timezone.utc).isoformat()},
        )
    return None


def parse_due_time(text: str, now: datetime | None = None) -> tuple[datetime | None, str]:
    zone = local_timezone()
    current = now.astimezone(zone) if now else datetime.now(zone)

    relative = re.search(
        r"\b(?:daqui a|em)\s+(\d+)\s*(minutos?|mins?|horas?|dias?)\b",
        text,
        flags=re.IGNORECASE,
    )
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2).casefold()
        delta = timedelta(minutes=amount) if unit.startswith(("minuto", "min")) else timedelta(hours=amount) if unit.startswith("hora") else timedelta(days=amount)
        return current + delta, _remove_time_expression(text, relative)

    day = re.search(
        r"\b(hoje|amanh[ãa])(?:\s+(?:à|a|às|as)\s*(\d{1,2})(?::(\d{2}))?\s*(?:h|horas?)?)?\b",
        text,
        flags=re.IGNORECASE,
    )
    if day:
        days = 1 if day.group(1).casefold().startswith("amanh") else 0
        hour = int(day.group(2) or 9)
        minute = int(day.group(3) or 0)
        due = (current + timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due <= current:
            due += timedelta(days=1)
        return due, _remove_time_expression(text, day)

    clock = re.search(
        r"\b(?:à|a|às|as)\s*(\d{1,2})(?::(\d{2}))?\s*(?:h|horas?)?\b",
        text,
        flags=re.IGNORECASE,
    )
    if clock:
        due = current.replace(hour=int(clock.group(1)), minute=int(clock.group(2) or 0), second=0, microsecond=0)
        if due <= current:
            due += timedelta(days=1)
        return due, _remove_time_expression(text, clock)
    return None, text.strip()


def _remove_time_expression(text: str, match: re.Match[str]) -> str:
    cleaned = (text[: match.start()] + " " + text[match.end() :]).strip(" ,.-")
    return re.sub(r"\s+", " ", cleaned)
