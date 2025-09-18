import typer

app = typer.Typer()


@app.command()
def main():
    """Main command for txtpack."""
    print("Hello from txtpack!")
