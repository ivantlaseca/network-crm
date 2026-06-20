"""Rule-based relationship intelligence derived from stored facts."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from .models import Contact, Conversation

STOP_WORDS = {
    "about", "after", "again", "also", "and", "are", "because", "been", "before",
    "being", "but", "can", "could", "did", "does", "doing", "for", "from", "have",
    "into", "just", "more", "next", "not", "our", "out", "should", "some", "than",
    "that", "the", "their", "them", "then", "there", "they", "this", "through", "to",
    "very", "was", "were", "what", "when", "where", "which", "while", "with", "would",
    "you", "your", "will", "said", "suggested", "talked", "asked", "need", "follow",
}
STATE_ORDER = ["Dormant", "Cooling", "Warm", "Active"]


def sorted_conversations(contact: Contact) -> list[Conversation]:
    return sorted(contact.conversations, key=lambda item: item.date, reverse=True)


def latest_conversation(contact: Contact) -> Conversation | None:
    conversations = sorted_conversations(contact)
    return conversations[0] if conversations else None


def last_spoke(contact: Contact) -> date | None:
    latest = latest_conversation(contact)
    if not latest:
        return None
    try:
        return date.fromisoformat(latest.date)
    except ValueError:
        return None


def days_since_last_spoke(contact: Contact, today: date | None = None) -> int | None:
    spoke = last_spoke(contact)
    return ((today or date.today()) - spoke).days if spoke else None


def average_helpfulness(contact: Contact) -> float:
    if not contact.conversations:
        return 0.0
    return round(sum(item.helpfulness for item in contact.conversations) / len(contact.conversations), 1)


def current_referral_willingness(contact: Contact) -> int:
    latest = latest_conversation(contact)
    return latest.referral_willingness if latest else 0


def latest_advice(contact: Contact) -> str:
    latest = latest_conversation(contact)
    return latest.suggested if latest else ""


def outstanding_commitments(contact: Contact) -> str:
    latest = latest_conversation(contact)
    return latest.next_steps if latest else ""


def extract_repeated_themes(conversations: list[Conversation]) -> list[str]:
    text = " ".join(
        value
        for conversation in conversations
        for value in (conversation.learned, conversation.suggested, conversation.next_steps, conversation.misc_notes)
    ).lower()
    words = re.findall(r"[a-z][a-z'-]{2,}", text)
    counts = Counter(word for word in words if word not in STOP_WORDS)
    themes = [word for word, count in counts.most_common() if count >= 2]
    return themes[:5]


def repeated_themes(contact: Contact) -> list[str]:
    return extract_repeated_themes(contact.conversations)


def themes_text(contact: Contact) -> str:
    themes = repeated_themes(contact)
    return ", ".join(themes) if themes else "No repeated themes yet."


def relationship_state(contact: Contact, today: date | None = None) -> str:
    elapsed = days_since_last_spoke(contact, today)
    if elapsed is None:
        return "Dormant"
    if elapsed <= 14:
        state = "Active"
    elif elapsed <= 30:
        state = "Warm"
    elif elapsed <= 60:
        state = "Cooling"
    else:
        state = "Dormant"
    if average_helpfulness(contact) >= 4 and current_referral_willingness(contact) >= 3:
        state = STATE_ORDER[min(STATE_ORDER.index(state) + 1, len(STATE_ORDER) - 1)]
    return state


def surface_reasons(contact: Contact, today: date | None = None) -> list[str]:
    elapsed = days_since_last_spoke(contact, today)
    if elapsed is None:
        return []
    helpfulness = average_helpfulness(contact)
    referral = current_referral_willingness(contact)
    dormant = relationship_state(contact, today) == "Dormant"
    reasons: list[str] = []
    if helpfulness >= 4 and elapsed >= 21:
        reasons.append("helpful")
    if referral >= 4 and elapsed >= 14:
        reasons.append("referral")
    if outstanding_commitments(contact).strip() and elapsed >= 10:
        reasons.append("next_steps")
    if dormant and (helpfulness >= 4 or referral >= 3):
        reasons.append("dormant_value")
    return reasons


def today_section(contact: Contact, today: date | None = None) -> str | None:
    reasons = surface_reasons(contact, today)
    if not reasons:
        return None
    state = relationship_state(contact, today)
    if state == "Dormant":
        return "Dormant But Valuable"
    if state in {"Active", "Warm"} and (latest_advice(contact).strip() or outstanding_commitments(contact).strip()):
        return "Warming Up"
    return "Worth Nurturing Now"


def why_surfaced(contact: Contact, today: date | None = None) -> str:
    reasons = surface_reasons(contact, today)
    if "dormant_value" in reasons:
        return "This was a valuable connection that has gone quiet."
    if "next_steps" in reasons:
        return "You recorded next steps from the last conversation."
    if "referral" in reasons:
        return "They showed referral willingness, and this relationship is worth keeping warm."
    return "They gave highly useful advice and enough time has passed to share progress."


def reconnect_reason(contact: Contact) -> str:
    if outstanding_commitments(contact).strip():
        return "Share progress on the next steps they suggested."
    if latest_advice(contact).strip():
        return "Thank them again and mention one concrete thing you applied."
    if current_referral_willingness(contact) >= 4:
        return "Share a brief career update if something meaningful changed."
    return "Ask one thoughtful follow-up question if you have a real reason."


def strongest_sort_key(contact: Contact) -> tuple[int, float, str]:
    latest = latest_conversation(contact)
    return (current_referral_willingness(contact), average_helpfulness(contact), latest.date if latest else "")
