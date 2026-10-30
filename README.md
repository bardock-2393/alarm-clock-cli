# Alarm Clock CLI

A simple alarm clock, built as a terminal application only (no web UI, no
database).

## Run it

```bash
pip install -r requirements.txt

python alarm.py
```

This drops you into an interactive menu — add alarms, list them, remove them,
and start watching, all in one running session (no need to retype the
command each time):

```
[a]dd alarm   [l]ist alarms   [r]emove alarm   [s]tart watching   [q]uit
>
```

The same actions are also available as one-shot subcommands, useful for
scripting/testing:

```bash
python alarm.py add 07:30 --label "Wake up"
python alarm.py list
python alarm.py run
python alarm.py remove 1
```

## Design decisions

- **Subcommands over a menu** (`add` / `list` / `remove` / `run`) — scriptable
  and easy to test one command at a time, rather than a single interactive
  menu loop.
- **Plain JSON file storage** (`alarms.json`) instead of a database — alarms
  are a handful of small records for a single user, a file is enough and
  survives restarting the program.
- **One-shot alarms only** — each alarm fires once then is marked `done`.
  Daily/weekday repeating alarms were cut to stay inside the time box; the
  data model (`status` field) leaves room to add it later.
- **Terminal bell + message** for the alert instead of playing an audio file
  — zero extra runtime dependency, works in any terminal, easy to demo on
  screen recording.
- **`rich`** for colored tables/panels — the one external dependency, used to
  get a clean colored table (`list`) and a bordered alert panel (`run`)
  without hand-rolling box-drawing and ANSI codes.
- **Snooze/dismiss** — when an alarm fires, press `s` to snooze 5 minutes, or
  any other key to dismiss it.

## Cut for time (would add next)

- Recurring alarms (daily / specific weekdays)
- Multiple snoozes with a max limit
- Custom sound files
- Timezone-aware scheduling

## Tests

A single smoke test checks that a new alarm starts `pending` and flips to
`done` after a dismiss:

```bash
python test_alarm.py
```
