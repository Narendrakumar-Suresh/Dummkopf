import typer
from pathlib import Path
import tools
from typing import List
import json
import uuid
from datetime import datetime

app = typer.Typer()
FOB_DIR = '.fob'

# init
@app.command()
def init():
    """
    Initialize a new fob repository in the current directory.
    """
    fob_path = Path.cwd() / FOB_DIR

    if fob_path.exists():
        typer.echo("Repository already initialized.")
        raise typer.Exit()

    (fob_path / "commits").mkdir(parents=True)
    (fob_path / "index.json").write_text("{}")
    (fob_path / "HEAD").write_text("")

    typer.echo("Initialized empty fob repository in .fob/")

# stage the files
@app.command()
def add(files: List[str]):
    """
    Add one or more files to the staging area.
    Use '.' to add all files in the current directory.
    """
    fob_path = Path.cwd() / FOB_DIR
    if not fob_path.exists():
        typer.echo("Not a fob repository. Run `fob init` first.")
        raise typer.Exit()

    ignore_files = set()
    fobignore_path = Path.cwd() / ".fobignore"
    if fobignore_path.exists():
        with open(fobignore_path, "r") as fobignore:
            ignore_files = set(line.strip() for line in fobignore.readlines() if line.strip() and not line.startswith("#"))

    for file in files:
        if file == ".":
            for f in Path.cwd().rglob("*"):
                if f.is_file() and (FOB_DIR not in f.parts) and not any(ignored in f.parts for ignored in ignore_files):
                    tools.add_file(f)
                    typer.echo(f"Staged '{f}'")
        else:
            path = Path(file)
            if not path.exists():
                typer.echo(f"File '{file}' not found.")
                continue
            if path.is_file() and not any(ignored in path.parts for ignored in ignore_files):
                tools.add_file(path)
                typer.echo(f"Staged '{file}'")
            else:
                typer.echo(f"Skipped ignored or invalid file '{file}'")

# co0ommmited to the repo
@app.command()
def commit(message:str):
    """
    Commit the staged changes with a message.
    """

    fob_path=Path.cwd()/FOB_DIR
    index_path = fob_path / "index.json"

    if not fob_path.exists():
        typer.echo("Not a fob repository. Run `fob init` first.")
        raise typer.Exit()
    try:
        index=json.loads(index_path.read_text())
    except json.JSONDecodeError:
        index = {}
    
    commit_id=str(uuid.uuid4())
    commit_time = datetime.now().isoformat()
    commit={'commit_id':commit_id,
            "message": message, 
            'commit_time':commit_time,
            "files": index
            }
    commit_dir=fob_path/"commits"
    commit_file = commit_dir / f"{commit_id}.json"
    commit_file.write_text(json.dumps(commit, indent=2))

    fob_head=fob_path/'HEAD'
    fob_head.write_text(commit_id)

    index_path.write_text("{}")
    typer.echo(f"Committed changes: {commit_id}")

@app.command()
def log():
    """
    Show commit history.
    """

    fob_path = Path.cwd()/FOB_DIR
    commits_path=fob_path/"commits"

    if not commits_path.exists():
        typer.echo("No commits")
        raise typer.Exit()
    commits = []

    for file in commits_path.glob("*.json"):
        try:
            data = json.loads(file.read_text())
            commit_time = data.get("commit_time")
            # Parse time string if it's not already a datetime object
            if isinstance(commit_time, str):
                commit_time = datetime.fromisoformat(commit_time)
            data["commit_time"] = commit_time
            commits.append(data)
        except Exception as e:
            typer.echo(f"Failed to read {file.name}: {e}")
    
    commits.sort(key=lambda c: c["commit_time"], reverse=True)

    for commit in commits:
        typer.echo(f"commit_id: {commit['commit_id']}")
        typer.echo(f"message  : {commit['message']}")
        typer.echo(f"date     : {commit['commit_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        typer.echo("-" * 40)


    



if __name__ == "__main__":
    app()
