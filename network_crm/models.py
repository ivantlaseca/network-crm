"""Persistent data models for contacts and conversations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


class ModelValidationError(ValueError):
    """Raised when stored data does not match the expected model."""


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ModelValidationError(f"'{key}' must be a string")
    return value


def _rating(data: dict[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
        raise ModelValidationError(f"'{key}' must be an integer from 1 to 5")
    return value


def _iso_date(data: dict[str, Any], key: str) -> str:
    value = _required_string(data, key)
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ModelValidationError(f"'{key}' must be an ISO date") from exc
    return value


def _iso_datetime(data: dict[str, Any], key: str) -> str:
    value = _required_string(data, key)
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ModelValidationError(f"'{key}' must be an ISO datetime") from exc
    return value


@dataclass
class Conversation:
    id: str
    date: str
    learned: str
    suggested: str
    next_steps: str
    misc_notes: str
    helpfulness: int
    referral_willingness: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "Conversation":
        if not isinstance(data, dict):
            raise ModelValidationError("each conversation must be an object")
        return cls(
            id=_required_string(data, "id"),
            date=_iso_date(data, "date"),
            learned=_required_string(data, "learned"),
            suggested=_required_string(data, "suggested"),
            next_steps=_required_string(data, "next_steps"),
            misc_notes=_required_string(data, "misc_notes"),
            helpfulness=_rating(data, "helpfulness"),
            referral_willingness=_rating(data, "referral_willingness"),
        )


@dataclass
class Contact:
    id: str
    name: str
    company: str
    role: str
    conversations: list[Conversation] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
            "role": self.role,
            "conversations": [conversation.to_dict() for conversation in self.conversations],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Any) -> "Contact":
        if not isinstance(data, dict):
            raise ModelValidationError("each contact must be an object")
        conversations = data.get("conversations")
        if not isinstance(conversations, list):
            raise ModelValidationError("'conversations' must be a list")
        name = _required_string(data, "name")
        if not name.strip():
            raise ModelValidationError("'name' cannot be empty")
        return cls(
            id=_required_string(data, "id"),
            name=name,
            company=_required_string(data, "company"),
            role=_required_string(data, "role"),
            conversations=[Conversation.from_dict(item) for item in conversations],
            created_at=_iso_datetime(data, "created_at"),
            updated_at=_iso_datetime(data, "updated_at"),
        )
