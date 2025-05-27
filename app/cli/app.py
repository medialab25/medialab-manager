import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="MediaVault Manager CLI")
console = Console()

@app.command()
def hello(name: str = typer.Argument("World", help="Name to greet")):
    """Say hello to someone."""
    console.print(Panel(f"Hello {name}! 👋", title="Greeting"))

@app.command()
def version():
    """Show the current version."""
    console.print("MediaVault Manager v0.1.0")

if __name__ == "__main__":
    app()
