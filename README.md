# network

A lightweight, terminal-based relationship memory system for professional networking.

## The problem it solves

Networking creates a trail of advice, commitments, and context that is easy to lose in scattered notes. `network` makes a conversation quick to capture and later answers a gentler question than a task manager would: **who deserves attention, and why?**

## What the tool does

- Records what you learned, what was suggested, and your next steps after a conversation.
- Keeps helpfulness and referral-willingness signals alongside factual notes.
- Derives relationship state, themes, and reconnection ideas when displayed.
- Surfaces worthwhile relationships through `today`.
- Provides contact, company, list, and keyword views of your notes.

## What it intentionally does not do

There is no web app, database, authentication, scraping, background processing, AI, message generation, or rigid follow-up scheduling. Derived relationship intelligence is never stored as fact.

## Why the terminal?

The terminal keeps capture faster than opening and organizing a notes app. It also makes the project local, inspectable, dependency-free, and easy to change.

## Design principles

Conversations are primary and contacts are secondary. Capture comes before organization. Inputs are structured while outputs are readable. The app stores facts and derives understanding. It suggests reasons to reconnect without composing messages or treating relationships like deadlines.

## Relationship states

States are computed from the latest conversation each time they are shown:

- **Active:** spoke within 14 days
- **Warm:** spoke within 30 days
- **Cooling:** spoke within 60 days
- **Dormant:** more than 60 days, or no conversations

A relationship with average helpfulness of at least 4 and current referral willingness of at least 3 moves one level warmer. It can never move above Active.

## How `today` decides what to surface

A contact appears only with a meaningful factual reason: valuable advice after enough time, a strong referral signal, recorded next steps, or a dormant but valuable relationship. Results are grouped as **Worth Nurturing Now**, **Warming Up**, and **Dormant But Valuable**. Low-value dormant contacts are not surfaced.

## Run it

Requires Python 3 and no third-party packages.

```bash
cd network
python main.py
```

Running without arguments opens a persistent numbered menu. Choose workflows, return to the main menu after each one, and select Exit when finished. Data is saved as each change is made.

Every interactive workflow displays `0` as **cancel/back**. Cancelling a multi-step note or edit discards the unfinished changes and returns directly to the main menu.

The existing one-shot commands remain available as faster shortcuts:

```bash
python main.py --help
python main.py note
```

Data is created automatically at `data/contacts.json`. The file is readable, pretty-printed JSON.

## Command examples

```bash
python main.py note
python main.py today
python main.py show "Ada"
python main.py company "Acme"
python main.py edit
python main.py list
python main.py search "product strategy"
python main.py delete
```

## Example workflow after a coffee chat

Run `python main.py note`. Enter the person's name; if they are new, add their company and role. Record what you learned, their advice, your own next steps, optional miscellaneous context, helpfulness, and their referral signal. The app saves the conversation and immediately shows the updated relationship summary. Later, use `today` to see which relationships have a genuine reason for attention.

## Project structure

```text
network/
  main.py              CLI argument routing
  network_crm/
    models.py          factual dataclasses
    storage.py         safe JSON persistence
    commands.py        command workflows
    menu.py            persistent interactive navigation
    prompts.py         terminal input and selection
    analysis.py        derived relationship rules
    display.py         calm plain-text rendering
  data/
    contacts.json      local user data (ignored by Git)
    contacts.example.json
  tests/               standard-library test suite
  README.md
```

Run tests with:

```bash
python -m unittest discover -v
```

## Future improvements

Possible Phase 2 work includes AI-assisted summaries, stronger theme extraction, export/import, company opportunity tracking, MCP integration, and optional calendar or email integrations. None is part of this MVP.

## Interview explanation

“I built a terminal-based relationship memory system to reduce the cognitive load of networking during my career transition. Instead of building a spreadsheet-style CRM, I designed it around conversations. The tool captures what I learned, what was suggested, my next steps, helpfulness, and referral willingness. It then derives relationship states and surfaces connections worth nurturing, without turning relationships into rigid deadlines or generating messages for me.”
