# FOB - File Object Base Version Control System

>[!NOTE]
>Well it is actually F*** O** B****, but yeah GPT gave a better name for now.
>(This is just a prototype and will port it to Go(mostly) or C.)

FOB is a lightweight version control system implemented in Python. It provides basic version control functionality similar to Git, allowing you to track changes in your files and maintain a history of your project.

## Features

- Initialize a new repository
- Stage files for commit
- Commit changes with messages
- View commit history
- Ignore files using `.fobignore`

## Installation

FOB requires Python 3.12 or higher. This project uses `uv` for dependency management.

First, install uv if you haven't already(check here):
```bash
https://docs.astral.sh/uv/getting-started/installation/
```

## Usage

### Initialize a Repository

Create a new FOB repository in your current directory:

```bash
python main.py init
```

This will create a `.fob` directory to store all version control information.

### Adding Files

Add specific files to the staging area:

```bash
python main.py add filename.txt
```

Add all files in the current directory:

```bash
python main.py add .
```

### Committing Changes

Commit staged changes with a message:

```bash
python main.py commit "Your commit message here"
```

### Viewing History

View the commit history:

```bash
python main.py log
```

### Ignoring Files

Create a `.fobignore` file in your repository root and add patterns for files you want to ignore:

```
.venv
__pycache__
.python-version
```

## How It Works

FOB stores all version control information in the `.fob` directory:
- `commits/`: Directory containing all commit data
- `index.json`: Staging area for changes
- `HEAD`: Points to the current commit

Each commit is stored as a JSON file containing:
- Commit ID (UUID)
- Commit message
- Timestamp
- File contents at the time of commit

## Requirements

- Python >= 3.12
- typer >= 0.15.2

## Contributing

Feel free to submit issues and enhancement requests!
