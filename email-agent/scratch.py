# %%

from load_scenarios import load_scenarios
from email_search_tools import read_email
from rich import print
from rich import box
from rich.panel import Panel
from rich.text import Text

scenarios = load_scenarios(limit=10)


def pretty_print_email(email):
    """Render an Email object in a readable, multi-line format."""
    # Build header lines
    header = Text()
    if email.subject:
        header.append("Subject: ", style="bold")
        header.append(f"{email.subject}\n")
    if email.from_address:
        header.append("From: ", style="bold")
        header.append(f"{email.from_address}\n")
    if email.to_addresses:
        header.append("To: ", style="bold")
        header.append(", ".join(email.to_addresses) + "\n")
    if email.cc_addresses:
        header.append("Cc: ", style="bold")
        header.append(", ".join(email.cc_addresses) + "\n")
    if email.bcc_addresses:
        header.append("Bcc: ", style="bold")
        header.append(", ".join(email.bcc_addresses) + "\n")
    if email.date:
        header.append("Date: ", style="bold")
        header.append(f"{email.date}\n")

    body_text = Text(email.body or "", style="none")

    panel = Panel(body_text, title=header, border_style="cyan", box=box.ROUNDED)
    print(panel)


for scenario in scenarios:
    print("\n[bold blue]Scenario:[/bold blue]", scenario)
    print("[bold green]Relevant Emails:[/bold green]")
    for msg_id in scenario.message_ids:
        email = read_email(msg_id)
        if email is not None:
            pretty_print_email(email)
        else:
            print(f"[red]Email with message_id {msg_id} not found.[/red]")
