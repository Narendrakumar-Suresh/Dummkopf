import json
from pathlib import Path
import typer
from typing import List
import uuid
from datetime import datetime
import tools

app = typer.Typer()
FOB_DIR = '.fob'
BRANCHES_FILE = "branches.json"  # File to store branch mappings

# Initialize the repository
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
    (fob_path / BRANCHES_FILE).write_text("{}")  # Initialize empty branches mapping

    # Initialize main branch
    branch("main")  # This will create the main branch with a commit_id and parent.

    typer.echo("Initialized empty fob repository in .fob/")

# Stage the files
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

# Commit the staged changes with a message
@app.command()
def commit(message: str):
    """
    Commit the staged changes with a message.
    """
    fob_path = Path.cwd() / FOB_DIR
    index_path = fob_path / "index.json"

    if not fob_path.exists():
        typer.echo("Not a fob repository. Run `fob init` first.")
        raise typer.Exit()

    try:
        index = json.loads(index_path.read_text())
    except json.JSONDecodeError:
        index = {}

    commit_id = str(uuid.uuid4())
    commit_time = datetime.now().isoformat()
    commit = {
        'commit_id': commit_id,
        "message": message,
        'commit_time': commit_time,
        "files": index
    }

    commit_dir = fob_path / "commits"
    commit_file = commit_dir / f"{commit_id}.json"
    commit_file.write_text(json.dumps(commit, indent=2))

    # Clear index
    index_path.write_text("{}")

    typer.echo(f"Committed changes: {commit_id}")

    # Update HEAD
    head_path = fob_path / 'HEAD'
    current_branch = head_path.read_text().strip()

    if not current_branch:
        typer.echo("HEAD does not point to any branch.")
        return

    # Update branch's commit_id in branches.json
    branches_path = fob_path / BRANCHES_FILE
    if branches_path.exists():
        branches = json.loads(branches_path.read_text())
        if current_branch in branches:
            branches[current_branch]["commit_id"] = commit_id
            with open(branches_path, "w") as f:
                json.dump(branches, f, indent=2)
        else:
            typer.echo(f"Branch '{current_branch}' not found in branches.json")
    else:
        typer.echo("branches.json not found.")


@app.command()
def log():
    """
    Show commit history.
    """
    fob_path = Path.cwd() / FOB_DIR
    commits_path = fob_path / "commits"

    if not commits_path.exists():
        typer.echo("No commits")
        raise typer.Exit()

    commits = []

    for file in commits_path.glob("*.json"):
        try:
            data = json.loads(file.read_text())
            commit_time = data.get("commit_time")
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

@app.command()
def branch(name: str = typer.Argument(None, help="Name of the branch to create or switch to")):
    """
    Create or switch to a branch.
    If no branch name is provided, show the current branch.
    """
    fob_path = Path.cwd() / FOB_DIR
    branches_path = fob_path / BRANCHES_FILE

    if not fob_path.exists():
        typer.echo("Not a fob repository. Run `fob init` first.")
        raise typer.Exit()

    # Load the branches mapping
    if branches_path.exists():
        with open(branches_path, "r") as file:
            branches = json.load(file)
    else:
        branches = {}

    head_path = fob_path / "HEAD"

    # Show current branch if no branch name is provided
    if name is None:
        if head_path.exists():
            current_branch = head_path.read_text().strip()
            if current_branch:
                typer.echo(f"Current branch: {current_branch}")
            else:
                typer.echo("No branch selected.")
        else:
            typer.echo("No branch selected.")
        return

    # Handle creating or switching to a branch
    if name in branches:
        # Switching branch
        current_commit = branches[name]["commit_id"]
        parent_branch = branches[name]["parent"]
        typer.echo(f"Switched to existing branch '{name}' pointing to commit {current_commit}")
        typer.echo(f"Parent branch: {parent_branch}")
    else:
        # Creating a new branch
        current_branch = head_path.read_text().strip() if head_path.exists() else ""
        current_commit = branches.get(current_branch, {}).get("commit_id", "")
        branches[name] = {
            "commit_id": current_commit,
            "parent": current_branch
        }
        typer.echo(f"Created and switched to new branch '{name}'")

    # Update HEAD to the new branch name
    head_path.write_text(name)

    # Save the branches mapping back to the JSON file
    with open(branches_path, "w") as file:
        json.dump(branches, file, indent=2)


@app.command()
def push(remote_path: str = ".fob_remote"):
    """
    Push current branch commits to a remote FOB repository (simulated via local folder).
    """
    local_fob = Path.cwd() / FOB_DIR
    remote_fob = Path(remote_path)

    if not local_fob.exists():
        typer.echo("Not a FOB repository.")
        raise typer.Exit()

    # Ensure remote exists
    (remote_fob / "commits").mkdir(parents=True, exist_ok=True)

    # Load branches
    local_branches = json.loads((local_fob / BRANCHES_FILE).read_text())
    head_branch = (local_fob / "HEAD").read_text().strip()

    if head_branch not in local_branches:
        typer.echo(f"Current branch '{head_branch}' not found.")
        raise typer.Exit()

    # Copy commits
    local_commits_dir = local_fob / "commits"
    remote_commits_dir = remote_fob / "commits"

    for commit_file in local_commits_dir.glob("*.json"):
        dest = remote_commits_dir / commit_file.name
        if not dest.exists():
            dest.write_text(commit_file.read_text())

    # Update remote branches
    remote_branches_path = remote_fob / BRANCHES_FILE
    if remote_branches_path.exists():
        remote_branches = json.loads(remote_branches_path.read_text())
    else:
        remote_branches = {}

    remote_branches[head_branch] = local_branches[head_branch]
    remote_fob.mkdir(exist_ok=True)
    remote_branches_path.write_text(json.dumps(remote_branches, indent=2))

    typer.echo(f"Pushed branch '{head_branch}' to remote at '{remote_path}'")



if __name__ == "__main__":
    app()
