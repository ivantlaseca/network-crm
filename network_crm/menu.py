"""Persistent interactive menu for the networking CRM."""

from __future__ import annotations

from collections.abc import Callable

from . import commands, display, prompts
from .storage import ContactStore


def _actions(store: ContactStore) -> dict[int, Callable[[], None]]:
    return {
        1: lambda: commands.today(store),
        2: lambda: commands.note(store),
        3: lambda: commands.browse_contacts(store),
        4: lambda: commands.search(
            store, prompts.ask_text("Search keyword", required=True)
        ),
        5: lambda: commands.company(
            store, prompts.ask_text("Company", required=True)
        ),
        6: lambda: commands.edit(store),
        7: lambda: commands.delete(store),
    }


def _show_menu() -> None:
    display.header("NETWORK — RELATIONSHIP MEMORY")
    print("1. Today")
    print("2. Add Conversation Note")
    print("3. Browse Contacts")
    print("4. Search")
    print("5. Company View")
    print("6. Edit Conversation")
    print("7. Delete Contact")
    print("8. Exit")


def _pause() -> None:
    input("\nPress Enter to return to the main menu...")


def run(store: ContactStore) -> None:
    """Run until the user exits, safely handling back and interruption."""
    actions = _actions(store)
    while True:
        _show_menu()
        try:
            choice = prompts.ask_number("\nChoose an option: ", 1, 8)
        except (KeyboardInterrupt, EOFError):
            print("\n\nStopping safely. Your relationship notes are saved.")
            return

        if choice == 8:
            print("\nYour relationship notes are saved. See you next time.")
            return

        try:
            actions[choice]()
        except prompts.PromptCancelled:
            print("\nAction cancelled. No changes were saved.")
        except KeyboardInterrupt:
            print("\n\nAction cancelled. Returning to the main menu.")
        except EOFError:
            print("\n\nStopping safely. Your relationship notes are saved.")
            return
        else:
            try:
                _pause()
            except KeyboardInterrupt:
                print()
            except EOFError:
                print("\nStopping safely. Your relationship notes are saved.")
                return
        print()
