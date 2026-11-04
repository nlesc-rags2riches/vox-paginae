"""Write `<dir>/book1/`: the e2e tests' synthetic book, to start a notebook on.

Usage: uv run python scripts/demo_data.py <dir>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.e2e.conftest import write_book

write_book(Path(sys.argv[1]) / "book1")
