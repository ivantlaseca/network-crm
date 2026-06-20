from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

from network_crm import analysis, commands, menu
from network_crm.models import Contact, Conversation
from network_crm.prompts import PromptCancelled
from network_crm.storage import ContactStore, StorageError


def conversation(day: str, helpfulness: int = 4, referral: int = 3, **values: str) -> Conversation:
    return Conversation(
        id=day, date=day, learned=values.get("learned", "career strategy career"),
        suggested=values.get("suggested", "share progress"),
        next_steps=values.get("next_steps", "send update"),
        misc_notes=values.get("misc_notes", ""), helpfulness=helpfulness,
        referral_willingness=referral,
    )


def contact(day: str = "2026-05-01", helpfulness: int = 4, referral: int = 3) -> Contact:
    return Contact(
        id="c1", name="Ada Lovelace", company="Analytical Engines", role="Engineer",
        conversations=[conversation(day, helpfulness, referral)],
        created_at="2026-01-01T00:00:00+00:00", updated_at="2026-01-01T00:00:00+00:00",
    )


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "data" / "contacts.json"
        self.store = ContactStore(self.path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_creates_and_round_trips_storage(self) -> None:
        self.assertEqual(self.store.load(), [])
        self.store.save([contact()])
        loaded = self.store.load()
        self.assertEqual(loaded[0].name, "Ada Lovelace")
        self.assertEqual(json.loads(self.path.read_text())[0]["conversations"][0]["helpfulness"], 4)

    def test_empty_file_is_empty_storage(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text("")
        self.assertEqual(self.store.load(), [])

    def test_malformed_or_invalid_storage_is_not_changed(self) -> None:
        self.path.parent.mkdir(parents=True)
        invalid_date = json.dumps([contact().to_dict()]).replace("2026-05-01", "not-a-date")
        for bad in ("{oops", '{"not": "a list"}', '[{"name": "Missing fields"}]', invalid_date):
            self.path.write_text(bad)
            with self.assertRaises(StorageError):
                self.store.load()
            self.assertEqual(self.path.read_text(), bad)


class AnalysisTests(unittest.TestCase):
    def test_state_boundaries_without_value_adjustment(self) -> None:
        today = date(2026, 6, 19)
        self.assertEqual(analysis.relationship_state(contact("2026-06-05", 3, 2), today), "Active")
        self.assertEqual(analysis.relationship_state(contact("2026-05-20", 3, 2), today), "Warm")
        self.assertEqual(analysis.relationship_state(contact("2026-04-20", 3, 2), today), "Cooling")
        self.assertEqual(analysis.relationship_state(contact("2026-04-19", 3, 2), today), "Dormant")

    def test_valuable_contact_moves_one_level_warmer(self) -> None:
        self.assertEqual(analysis.relationship_state(contact("2026-04-01"), date(2026, 6, 19)), "Cooling")

    def test_latest_average_and_themes(self) -> None:
        item = contact("2026-05-01", 3, 2)
        item.conversations.append(conversation("2026-06-01", 5, 5, learned="career planning career"))
        self.assertEqual(analysis.average_helpfulness(item), 4.0)
        self.assertEqual(analysis.current_referral_willingness(item), 5)
        self.assertEqual(analysis.latest_advice(item), "share progress")
        self.assertIn("career", analysis.repeated_themes(item))

    def test_theme_fallback_and_today_sections(self) -> None:
        item = contact("2026-06-01", 4, 4)
        item.conversations[0].learned = "unique"
        item.conversations[0].suggested = "different"
        item.conversations[0].next_steps = ""
        self.assertEqual(analysis.themes_text(item), "No repeated themes yet.")
        self.assertEqual(analysis.today_section(item, date(2026, 6, 19)), "Warming Up")
        dormant = contact("2026-01-01", 3, 3)
        self.assertEqual(analysis.today_section(dormant, date(2026, 6, 19)), "Dormant But Valuable")
        low_value = contact("2026-01-01", 2, 2)
        low_value.conversations[0].next_steps = ""
        self.assertIsNone(analysis.today_section(low_value, date(2026, 6, 19)))


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = ContactStore(Path(self.temp.name) / "contacts.json")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def capture(self, func, *args) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            func(*args)
        return output.getvalue()

    def test_note_creates_contact_and_reprompts_rating(self) -> None:
        answers = iter(["Grace Hopper", "Navy", "Computer Scientist", "2026-04-02", "Compilers", "Keep building", "Build demo", "", "bad", "5", "4"])
        with patch("builtins.input", side_effect=lambda _: next(answers)):
            output = self.capture(commands.note, self.store)
        saved = self.store.load()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].conversations[0].date, "2026-04-02")
        self.assertEqual(saved[0].conversations[0].helpfulness, 5)
        self.assertIn("Conversation saved", output)

    def test_list_search_company_and_show(self) -> None:
        self.store.save([contact()])
        self.assertIn("Analytical Engines", self.capture(commands.list_contacts, self.store))
        self.assertIn("Ada Lovelace", self.capture(commands.search, self.store, "strategy"))
        self.assertIn("Strongest Connections", self.capture(commands.company, self.store, "analytical"))
        self.assertIn("Conversation History", self.capture(commands.show, self.store, "ada"))

    def test_edit_conversation(self) -> None:
        self.store.save([contact()])
        answers = iter(["Ada", "1", "1", "2026-03-15", "New learning", "", "", "", "", ""])
        with patch("builtins.input", side_effect=lambda _: next(answers)):
            self.capture(commands.edit, self.store)
        saved = self.store.load()[0].conversations[0]
        self.assertEqual(saved.date, "2026-03-15")
        self.assertEqual(saved.learned, "New learning")

    def test_delete_cancel_and_confirm(self) -> None:
        self.store.save([contact()])
        with patch("builtins.input", side_effect=["Ada", "1", "n"]):
            self.capture(commands.delete, self.store)
        self.assertEqual(len(self.store.load()), 1)
        with patch("builtins.input", side_effect=["Ada", "1", "yes"]):
            self.capture(commands.delete, self.store)
        self.assertEqual(self.store.load(), [])

    def test_today_language(self) -> None:
        self.store.save([contact("2025-01-01", 3, 3)])
        output = self.capture(commands.today, self.store)
        self.assertIn("Dormant But Valuable", output)
        self.assertNotIn("over" + "due", output.casefold())

    def test_interactive_menu_browses_and_returns_until_exit(self) -> None:
        self.store.save([contact()])
        with patch("builtins.input", side_effect=["3", "1", "", "8"]):
            output = self.capture(menu.run, self.store)
        self.assertIn("NETWORK — RELATIONSHIP MEMORY", output)
        self.assertIn("Conversation History", output)
        self.assertGreaterEqual(output.count("NETWORK — RELATIONSHIP MEMORY"), 2)
        self.assertIn("notes are saved", output)

    def test_interactive_menu_reprompts_invalid_choice(self) -> None:
        with patch("builtins.input", side_effect=["nope", "9", "8"]):
            output = self.capture(menu.run, self.store)
        self.assertEqual(output.count("Please choose a number from 1 to 8."), 2)

    def test_note_can_cancel_mid_workflow_without_saving(self) -> None:
        answers = ["Grace Hopper", "Navy", "Computer Scientist", "", "Compilers", "0"]
        with patch("builtins.input", side_effect=answers):
            with self.assertRaises(PromptCancelled):
                self.capture(commands.note, self.store)
        self.assertEqual(self.store.load(), [])

    def test_edit_can_cancel_without_saving_partial_changes(self) -> None:
        self.store.save([contact()])
        answers = ["Ada", "1", "1", "", "Changed in memory", "0"]
        with patch("builtins.input", side_effect=answers):
            with self.assertRaises(PromptCancelled):
                self.capture(commands.edit, self.store)
        saved = self.store.load()[0].conversations[0]
        self.assertEqual(saved.learned, "career strategy career")
        self.assertEqual(saved.suggested, "share progress")

    def test_note_reprompts_invalid_conversation_date(self) -> None:
        answers = [
            "Katherine Johnson", "NASA", "Mathematician", "last Tuesday", "2026-06-01",
            "Orbital mechanics", "Keep learning", "Read notes", "", "5", "3",
        ]
        with patch("builtins.input", side_effect=answers):
            output = self.capture(commands.note, self.store)
        self.assertIn("Please enter a valid date", output)
        self.assertEqual(self.store.load()[0].conversations[0].date, "2026-06-01")

    def test_single_contact_selection_can_be_cancelled(self) -> None:
        self.store.save([contact()])
        with patch("builtins.input", side_effect=["Ada", "0"]):
            with self.assertRaises(PromptCancelled):
                self.capture(commands.delete, self.store)
        self.assertEqual(len(self.store.load()), 1)

    def test_menu_handles_cancel_and_returns_immediately(self) -> None:
        with patch("builtins.input", side_effect=["2", "0", "8"]):
            output = self.capture(menu.run, self.store)
        self.assertIn("Action cancelled. No changes were saved.", output)
        self.assertEqual(self.store.load(), [])


if __name__ == "__main__":
    unittest.main()
