#!/usr/bin/env python3
"""Simple alarm clock CLI: add / list / remove / run."""

import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

STORE_FILE = Path(__file__).parent / "alarms.json"
console = Console()


# ---- storage ----

def load_alarms():
    if not STORE_FILE.exists():
        return []
    return json.loads(STORE_FILE.read_text())


def save_alarms(alarms):
    STORE_FILE.write_text(json.dumps(alarms, indent=2))


# ---- setup clock (add / list / remove) ----
# These do the actual work; cmd_* below just unpack argparse args and call them,
# so the interactive menu can call the same functions directly.

def add_alarm(time_str, label):
    datetime.strptime(time_str, "%H:%M")  # validates HH:MM, raises on bad input

    alarms = load_alarms()
    new_id = max((a["id"] for a in alarms), default=0) + 1
    alarms.append({
        "id": new_id,
        "time": time_str,
        "label": label,
        "status": "pending",
    })
    save_alarms(alarms)
    console.print(f"[bold green]✓ Alarm #{new_id} set for {time_str} — \"{label}\"[/bold green]")


def list_alarms():
    alarms = load_alarms()
    table = Table(title="Alarms")
    table.add_column("ID")
    table.add_column("Time")
    table.add_column("Label")
    table.add_column("Status")

    for a in alarms:
        status_text = "[yellow]pending[/yellow]" if a["status"] == "pending" else "[dim]done[/dim]"
        table.add_row(str(a["id"]), a["time"], a["label"], status_text)

    console.print(table)


def remove_alarm(alarm_id):
    alarms = load_alarms()
    remaining = [a for a in alarms if a["id"] != alarm_id]

    if len(remaining) == len(alarms):
        console.print(f"[bold red]✗ No alarm with id {alarm_id}[/bold red]")
        return

    save_alarms(remaining)
    console.print(f"[bold green]✓ Alarm #{alarm_id} removed[/bold green]")


def cmd_add(args):
    add_alarm(args.time, args.label)


def cmd_list(args):
    list_alarms()


def cmd_remove(args):
    remove_alarm(args.id)


# ---- run the clock (watch loop + trigger) ----

def trigger(alarm):
    """Ring the alarm until the user snoozes or dismisses it."""
    while True:
        console.print("\a", end="")  # terminal bell
        console.print(Panel(
            f"[bold white]{alarm['time']}[/bold white]\n\n\\[s] snooze 5m   \\[any key] dismiss",
            title=f"🔔 ALARM — {alarm['label']} 🔔",
            border_style="bold red",
        ))
        key = input().strip().lower()
        if key == "s":
            snoozed = (datetime.strptime(alarm["time"], "%H:%M") + timedelta(minutes=5)).strftime("%H:%M")
            alarm["time"] = snoozed
            console.print(f"[yellow]⏰ snoozed to {snoozed}[/yellow]")
            return
        else:
            alarm["status"] = "done"
            console.print("[dim]alarm dismissed[/dim]")
            return


def clock_face(pending):
    now = datetime.now().strftime("%H:%M:%S")
    next_alarm = min(pending, key=lambda a: a["time"], default=None)
    body = f"[bold white]{now}[/bold white]"
    if next_alarm:
        body += f"\n[dim]next: {next_alarm['time']} \"{next_alarm['label']}\"[/dim]"
    else:
        body += "\n[dim]no pending alarms[/dim]"
    return Panel(body, title="🕐 live clock", border_style="cyan")


def cmd_run(args):
    console.print("[bold cyan]◉ watching — Ctrl+C to stop[/bold cyan]")
    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                alarms = load_alarms()
                pending = [a for a in alarms if a["status"] == "pending"]
                live.update(clock_face(pending))

                now_hhmm = datetime.now().strftime("%H:%M")
                for alarm in pending:
                    if alarm["time"] == now_hhmm:
                        live.stop()  # pause the live clock so the trigger prompt renders cleanly
                        trigger(alarm)
                        save_alarms(alarms)
                        live.start()

                time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[cyan]stopped.[/cyan]")


# ---- interactive menu (the "hand made clock" mode) ----

def interactive():
    console.print(Panel("🕐  ALARM CLOCK  🕐", border_style="bold cyan"))
    while True:
        console.print(
            "\n[bold]\\[a][/bold]dd alarm   "
            "[bold]\\[l][/bold]ist alarms   "
            "[bold]\\[r][/bold]emove alarm   "
            "[bold]\\[s][/bold]tart watching   "
            "[bold]\\[q][/bold]uit"
        )
        choice = input("> ").strip().lower()

        if choice == "a":
            time_str = input("Time (HH:MM): ").strip()
            label = input("Label: ").strip() or "Alarm"
            try:
                add_alarm(time_str, label)
            except ValueError:
                console.print("[bold red]✗ invalid time, use HH:MM (24h)[/bold red]")

        elif choice == "l":
            list_alarms()

        elif choice == "r":
            raw_id = input("ID to remove: ").strip()
            if raw_id.isdigit():
                remove_alarm(int(raw_id))
            else:
                console.print("[bold red]✗ enter a numeric id[/bold red]")

        elif choice == "s":
            cmd_run(None)  # blocks here watching alarms; Ctrl+C returns to this menu

        elif choice == "q":
            console.print("[cyan]bye[/cyan]")
            break

        else:
            console.print("[bold red]✗ unknown option[/bold red]")


# ---- wire up CLI ----

def main():
    parser = argparse.ArgumentParser(description="Simple alarm clock CLI")
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add", help="set a new alarm")
    add_p.add_argument("time", help="HH:MM, 24-hour format")
    add_p.add_argument("--label", default="Alarm")
    add_p.set_defaults(func=cmd_add)

    list_p = sub.add_parser("list", help="show all alarms")
    list_p.set_defaults(func=cmd_list)

    remove_p = sub.add_parser("remove", help="remove an alarm by id")
    remove_p.add_argument("id", type=int)
    remove_p.set_defaults(func=cmd_remove)

    run_p = sub.add_parser("run", help="start watching for alarms")
    run_p.set_defaults(func=cmd_run)

    args = parser.parse_args()
    if args.command is None:
        interactive()  # no subcommand given -> drop into the interactive menu
    else:
        args.func(args)


if __name__ == "__main__":
    main()
