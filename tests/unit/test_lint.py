"""O repo passa no `ruff check` (só regras F; exceções em ruff.toml)."""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_repo_passa_no_ruff():
    res = subprocess.run([sys.executable, '-m', 'ruff', 'check'], cwd=RAIZ, capture_output=True, text=True,
                         encoding='utf-8', timeout=120)
    assert res.returncode == 0, res.stdout + res.stderr
