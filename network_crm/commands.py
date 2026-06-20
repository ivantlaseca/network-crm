"""Implementations of the network CLI commands."""

from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from . import analysis, display, prompts
from .models import Contact, Conversation
from .storage import ContactStore


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _contact_matches(contacts: list[Contact], query: str) -> list[Contact]:
    return [contact for contact in contacts if query.casefold() in contact.name.casefold()]


def _show_contact(contact: Contact) -> None:
    display.summary(contact)
    conversations = analysis.sorted_conversations(contact)
    if conversations:
        print()
        display.header("Conversation History")
        for index, item in enumerate(conversations, 1):
            print(f"\nConversation {index}")
            display.conversation(item)


def note(store: ContactStore) -> None:
    contacts = store.load()
    name = prompts.ask_text("Who did you speak with?", required=True)
    matches = _contact_matches(contacts, name)
    contact = prompts.choose(matches, lambda c: f"{c.name} — {c.company or 'No company'}", "Choose contact") if matches else None
    if contact is None and matches:
        print("Note cancelled.")
        return
    if contact is None:
        timestamp = _now()
        contact = Contact(
            id=str(uuid4()), name=name, company=prompts.ask_text("Company"),
            role=prompts.ask_text("Role"), created_at=timestamp, updated_at=timestamp,
        )
        contacts.append(contact)
        print(f"Created contact for {contact.name}.")
    conversation = Conversation(
        id=str(uuid4()),
        date=prompts.ask_date("When did you speak?", date.today().isoformat()),
        learned=prompts.ask_text("What did you learn?", required=True),
        suggested=prompts.ask_text("What did they suggest doing?", required=True),
        next_steps=prompts.ask_text("What are your next steps?", required=True),
        misc_notes=prompts.ask_text("Miscellaneous notes? Optional"),
        helpfulness=prompts.ask_rating("How helpful were they?"),
        referral_willingness=prompts.ask_rating("Referral willingness?"),
    )
    contact.conversations.append(conversation)
    contact.updated_at = _now()
    store.save(contacts)
    print("\nConversation saved. Here is the updated relationship summary:\n")
    display.summary(contact)


def today(store: ContactStore) -> None:
    contacts = store.load()
    sections = {"Worth Nurturing Now": [], "Warming Up": [], "Dormant But Valuable": []}
    for contact in contacts:
        section = analysis.today_section(contact)
        if section:
            sections[section].append(contact)
    shown = False
    for title, items in sections.items():
        if not items:
            continue
        shown = True
        display.header(title)
        for contact in sorted(items, key=analysis.strongest_sort_key, reverse=True):
            display.today_contact(contact)
        print()
    if not shown:
        print("No relationships need particular attention today. Keep nurturing them naturally.")


def show(store: ContactStore, name: str) -> None:
    contact = prompts.select_contact(store.load(), name, confirm_single=False)
    if not contact:
        return
    _show_contact(contact)


def browse_contacts(store: ContactStore) -> None:
    contacts = sorted(store.load(), key=lambda item: (item.company.casefold(), item.name.casefold()))
    if not contacts:
        print("No contacts recorded yet. Add a conversation note after your next conversation.")
        return
    selected = prompts.choose(
        contacts,
        lambda contact: f"{contact.name} — {contact.role or 'No role'}, {contact.company or 'No company'}",
        "Choose contact",
    )
    if selected:
        print()
        _show_contact(selected)


def company(store: ContactStore, company_name: str) -> None:
    contacts = [c for c in store.load() if company_name.casefold() in c.company.casefold()]
    if not contacts:
        print(f'No contacts found at companies matching "{company_name}".')
        return
    exact_companies = sorted({c.company for c in contacts}, key=str.casefold)
    for company_value in exact_companies:
        company_contacts = [c for c in contacts if c.company == company_value]
        ranked = sorted(company_contacts, key=analysis.strongest_sort_key, reverse=True)
        display.header(company_value or "No company recorded")
        recurring = analysis.extract_repeated_themes(
            [item for contact in company_contacts for item in contact.conversations]
        )
        print(f"Recurring Themes: {', '.join(recurring) if recurring else 'No repeated themes yet.'}")
        print("Strongest Connections: " + ", ".join(c.name for c in ranked))
        dormant = [c.name for c in ranked if analysis.relationship_state(c) == "Dormant" and (analysis.average_helpfulness(c) >= 4 or analysis.current_referral_willingness(c) >= 3)]
        print("Dormant High-Value Relationships: " + (", ".join(dormant) if dormant else "None right now"))
        print("\nIndividual Contacts")
        for contact in ranked:
            print(f"\n{contact.name} — {display.value(contact.role)}")
            print(f"Helpfulness: {display.stars(analysis.average_helpfulness(contact))} ({analysis.average_helpfulness(contact):.1f}/5)")
            print(f"Referral Willingness: {analysis.current_referral_willingness(contact)}/5")
            print(f"Last Spoke: {display.last_spoke_text(contact)}")
            print(f"Possible Reason to Reconnect: {analysis.reconnect_reason(contact)}")


def edit(store: ContactStore) -> None:
    contacts = store.load()
    contact = prompts.select_contact(contacts)
    if not contact:
        return
    conversations = analysis.sorted_conversations(contact)
    if not conversations:
        print("This contact has no conversations to edit.")
        return
    selected = prompts.choose(conversations, lambda c: f"{c.date} — {c.learned[:55] or 'No learned notes'}", "Choose conversation")
    if not selected:
        print("Edit cancelled.")
        return
    selected.date = prompts.ask_date("Conversation date", selected.date)
    selected.learned = prompts.ask_text("What did you learn?", required=True, default=selected.learned)
    selected.suggested = prompts.ask_text("What did they suggest doing?", required=True, default=selected.suggested)
    selected.next_steps = prompts.ask_text("What are your next steps?", required=True, default=selected.next_steps)
    selected.misc_notes = prompts.ask_text("Miscellaneous notes? Optional", default=selected.misc_notes)
    selected.helpfulness = prompts.ask_rating("How helpful were they?", selected.helpfulness)
    selected.referral_willingness = prompts.ask_rating("Referral willingness?", selected.referral_willingness)
    contact.updated_at = _now()
    store.save(contacts)
    print("\nConversation updated.\n")
    display.summary(contact)


def list_contacts(store: ContactStore) -> None:
    contacts = store.load()
    if not contacts:
        print("No contacts recorded yet. Use 'python main.py note' after your next conversation.")
        return
    companies: dict[str, list[Contact]] = {}
    for contact in contacts:
        companies.setdefault(contact.company or "No company recorded", []).append(contact)
    for company_name in sorted(companies, key=str.casefold):
        display.header(company_name)
        for contact in sorted(companies[company_name], key=lambda item: item.name.casefold()):
            print(f"{contact.name} — {display.value(contact.role)}")
            print(f"  Last Spoke: {display.last_spoke_text(contact)}")
            print(f"  Helpfulness: {display.stars(analysis.average_helpfulness(contact))} ({analysis.average_helpfulness(contact):.1f}/5)")
            print(f"  Referral Willingness: {analysis.current_referral_willingness(contact)}/5")
            print(f"  Relationship State: {analysis.relationship_state(contact)}")
        print()


def search(store: ContactStore, keyword: str) -> None:
    query = keyword.casefold()
    found = False
    for contact in store.load():
        contact_fields = (("Name", contact.name), ("Company", contact.company), ("Role", contact.role))
        field_matches = [f"{label}: {text}" for label, text in contact_fields if query in text.casefold()]
        note_matches: list[str] = []
        for item in analysis.sorted_conversations(contact):
            for label, text in (("Learned", item.learned), ("Suggested", item.suggested), ("Next Steps", item.next_steps), ("Misc Notes", item.misc_notes)):
                if query in text.casefold():
                    note_matches.append(f"{item.date} {label}: {text[:120]}")
        if field_matches or note_matches:
            found = True
            display.header(contact.name)
            for match in field_matches + note_matches:
                print(match)
    if not found:
        print(f'No matches found for "{keyword}".')


def delete(store: ContactStore) -> None:
    contacts = store.load()
    contact = prompts.select_contact(contacts)
    if not contact:
        return
    if not prompts.confirm(f"Delete {contact.name} and all conversation history?"):
        print("Delete cancelled.")
        return
    contacts.remove(contact)
    store.save(contacts)
    print(f"Deleted {contact.name}.")
