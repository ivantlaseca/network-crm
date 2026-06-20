"""Safe local JSON persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .models import Contact, ModelValidationError


class StorageError(RuntimeError):
    """A readable error caused by unavailable or invalid storage."""


class ContactStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def ensure_exists(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def load(self) -> list[Contact]:
        self.ensure_exists()
        try:
            raw = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Could not read {self.path}: {exc}") from exc
        if not raw.strip():
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"Storage file is malformed near line {exc.lineno}. Fix {self.path}; it was not changed."
            ) from exc
        if not isinstance(data, list):
            raise StorageError(f"Storage file must contain a JSON list: {self.path}")
        try:
            return [Contact.from_dict(item) for item in data]
        except ModelValidationError as exc:
            raise StorageError(f"Storage data is invalid: {exc}. The file was not changed.") from exc

    def save(self, contacts: list[Contact]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps([contact.to_dict() for contact in contacts], indent=2) + "\n"
        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as handle:
                temp_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        except OSError as exc:
            if temp_name:
                Path(temp_name).unlink(missing_ok=True)
            raise StorageError(f"Could not save {self.path}: {exc}") from exc

