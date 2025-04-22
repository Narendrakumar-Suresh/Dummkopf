import json
from pathlib import Path

FOB_DIR = ".fob"

def add_file(file: Path):
    """
    Adds a single text file to the staging area.
    Skips binary files or files that can't be decoded as UTF-8.
    """
    fob_path = Path.cwd() / FOB_DIR
    index_path = fob_path / "index.json"

    index = json.loads(index_path.read_text())

    try:
        content = file.read_text()
    except UnicodeDecodeError:
        return

    index[str(file)] = content
    index_path.write_text(json.dumps(index, indent=2))
