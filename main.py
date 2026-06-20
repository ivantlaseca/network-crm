"""Command-line entry point for network."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from network_crm import commands, menu
from network_crm.prompts import PromptCancelled
from network_crm.storage import ContactStore, StorageError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="network", description="A conversation-first networking CRM.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("note", help="Capture a conversation")
    subparsers.add_parser("today", help="See relationships worth nurturing")
    show_parser = subparsers.add_parser("show", help="Show a relationship profile")
    show_parser.add_argument("name")
    company_parser = subparsers.add_parser("company", help="Show company-level intelligence")
    company_parser.add_argument("company")
    subparsers.add_parser("edit", help="Edit a conversation")
    subparsers.add_parser("list", help="List contacts by company")
    search_parser = subparsers.add_parser("search", help="Search contacts and notes")
    search_parser.add_argument("keyword")
    subparsers.add_parser("delete", help="Delete a contact")
    return parser


def run() -> int:
    args = build_parser().parse_args()
    store = ContactStore(Path(__file__).resolve().parent / "data" / "contacts.json")
    handlers = {
        "note": lambda: commands.note(store), "today": lambda: commands.today(store),
        "show": lambda: commands.show(store, args.name),
        "company": lambda: commands.company(store, args.company),
        "edit": lambda: commands.edit(store), "list": lambda: commands.list_contacts(store),
        "search": lambda: commands.search(store, args.keyword), "delete": lambda: commands.delete(store),
    }
    try:
        if args.command is None:
            menu.run(store)
        else:
            handlers[args.command]()
    except StorageError as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1
    except PromptCancelled:
        print("\nCancelled. No changes were saved.")
        return 0
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
