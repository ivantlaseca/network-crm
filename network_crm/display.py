"""Plain-text rendering for terminal output."""

from __future__ import annotations

from datetime import date

from . import analysis
from .models import Contact, Conversation


def header(title: str) -> None:
    print("=" * 50)
    print(title)
    print("=" * 50)


def stars(value: float) -> str:
    filled = max(0, min(5, round(value)))
    return "★" * filled + "☆" * (5 - filled)


def value(text: str) -> str:
    return text.strip() or "Not recorded"


def last_spoke_text(contact: Contact, today: date | None = None) -> str:
    spoke = analysis.last_spoke(contact)
    elapsed = analysis.days_since_last_spoke(contact, today)
    if spoke is None or elapsed is None:
        return "No conversations yet"
    return f"{spoke.isoformat()} ({elapsed} days ago)"


def summary(contact: Contact, today: date | None = None) -> None:
    header(contact.name)
    print(f"Company: {value(contact.company)}")
    print(f"Role: {value(contact.role)}")
    print(f"Last Spoke: {last_spoke_text(contact, today)}")
    print(f"Average Helpfulness: {analysis.average_helpfulness(contact):.1f}/5 {stars(analysis.average_helpfulness(contact))}")
    print(f"Current Referral Willingness: {analysis.current_referral_willingness(contact)}/5")
    print(f"Relationship State: {analysis.relationship_state(contact, today)}")
    print(f"Repeated Themes: {analysis.themes_text(contact)}")
    print(f"Latest Advice: {value(analysis.latest_advice(contact))}")
    print(f"Outstanding Commitments / Next Steps: {value(analysis.outstanding_commitments(contact))}")
    print(f"Possible Reason to Reconnect: {analysis.reconnect_reason(contact)}")


def conversation(conversation_item: Conversation) -> None:
    print(f"Date: {conversation_item.date}")
    print(f"Learned: {value(conversation_item.learned)}")
    print(f"Suggested: {value(conversation_item.suggested)}")
    print(f"Next Steps: {value(conversation_item.next_steps)}")
    print(f"Miscellaneous Notes: {value(conversation_item.misc_notes)}")
    print(f"Helpfulness: {stars(conversation_item.helpfulness)} ({conversation_item.helpfulness}/5)")
    print(f"Referral Willingness: {conversation_item.referral_willingness}/5")


def today_contact(contact: Contact, today: date | None = None) -> None:
    print(f"\n{contact.name} — {value(contact.company)}, {value(contact.role)}")
    print(f"Helpfulness: {stars(analysis.average_helpfulness(contact))} ({analysis.average_helpfulness(contact):.1f}/5)")
    print(f"Referral Willingness: {analysis.current_referral_willingness(contact)}/5")
    print(f"Last Spoke: {last_spoke_text(contact, today)}")
    print(f"Repeated Themes: {analysis.themes_text(contact)}")
    print(f"Latest Advice: {value(analysis.latest_advice(contact))}")
    print(f"Outstanding Commitments / Next Steps: {value(analysis.outstanding_commitments(contact))}")
    print(f"Why Surfaced: {analysis.why_surfaced(contact, today)}")
    print(f"Possible Reason to Reconnect: {analysis.reconnect_reason(contact)}")

