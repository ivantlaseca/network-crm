"""Small reusable terminal prompts."""

from __future__ import annotations

from datetime import date
from typing import Callable, TypeVar

from .models import Contact

T = TypeVar("T")


class PromptCancelled(Exception):
    """Raised when the user backs out of an interactive workflow."""


def ask_text(label: str, *, required: bool = False, default: str | None = None) -> str:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input(f"{label}{suffix} (or 0 to cancel): ").strip()
        if value == "0":
            raise PromptCancelled
        if value:
            return value
        if default is not None:
            return default
        if not required:
            return ""
        print("Please enter a value.")


def ask_rating(label: str, default: int | None = None) -> int:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input(f"{label} (1-5){suffix}, or 0 to cancel: ").strip()
        if value == "0":
            raise PromptCancelled
        if not value and default is not None:
            return default
        try:
            rating = int(value)
        except ValueError:
            rating = 0
        if 1 <= rating <= 5:
            return rating
        print("Please enter a whole number from 1 to 5.")


def ask_date(label: str, default: str) -> str:
    while True:
        value = input(f"{label} [{default}] (YYYY-MM-DD, or 0 to cancel): ").strip()
        if value == "0":
            raise PromptCancelled
        candidate = value or default
        try:
            date.fromisoformat(candidate)
        except ValueError:
            print("Please enter a valid date in YYYY-MM-DD format.")
            continue
        return candidate


def ask_number(label: str, minimum: int, maximum: int) -> int:
    while True:
        value = input(label).strip()
        try:
            number = int(value)
        except ValueError:
            number = 0
        if minimum <= number <= maximum:
            return number
        print(f"Please choose a number from {minimum} to {maximum}.")


def choose(items: list[T], label: Callable[[T], str], prompt: str) -> T | None:
    if not items:
        return None
    for index, item in enumerate(items, 1):
        print(f"{index}. {label(item)}")
    while True:
        value = input(f"{prompt} (1-{len(items)}, or 0 to cancel): ").strip().lower()
        if value in {"0", "q"}:
            raise PromptCancelled
        if value.isdigit() and 1 <= int(value) <= len(items):
            return items[int(value) - 1]
        print("Please choose a listed number or 0.")


def select_contact(
    contacts: list[Contact], query: str | None = None, *, confirm_single: bool = True
) -> Contact | None:
    if query is None:
        query = ask_text("Search contact", required=True)
    matches = [contact for contact in contacts if query.casefold() in contact.name.casefold()]
    if not matches:
        print(f'No contacts found matching "{query}".')
        return None
    if len(matches) == 1 and not confirm_single:
        return matches[0]
    return choose(matches, lambda c: f"{c.name} — {c.role or 'No role'}, {c.company or 'No company'}", "Choose contact")


def confirm(label: str) -> bool:
    return input(f"{label} [y/N]: ").strip().casefold() in {"y", "yes"}
