import typer
from sentinel import main as sentinelcli

app = typer.Typer()
app.add_typer(sentinelcli.app, name="sentinel")

if __name__ == "__main__":
    app()
