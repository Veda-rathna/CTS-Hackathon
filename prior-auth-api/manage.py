"""
Central CLI runner for the Prior Authorization Triage API.

Usage:
    python manage.py serve       - Start the FastAPI dev server
    python manage.py test        - Run the pytest suite (88 tests)
    python manage.py test-live   - Run the live API verification suite
    python manage.py setup-db    - Full DB setup: init pgvector, seed data, ingest RAG embeddings
    python manage.py validate-db - Check PostgreSQL table counts and vector status
"""
from __future__ import annotations
import sys
import subprocess
import os

def get_python_exe() -> str:
    venv_py = os.path.join(".venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(".venv", "bin", "python")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable

def run_cmd(cmd: list[str]) -> int:
    py = get_python_exe()
    if cmd and cmd[0] == sys.executable:
        cmd[0] = py
    print(f"\n[EXEC] {' '.join(cmd)}")
    return subprocess.call(cmd)

def serve():
    """Start Uvicorn server."""
    port = os.getenv("PORT", "8001")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", port]
    run_cmd(cmd)

def test():
    """Run pytest suite."""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    sys.exit(run_cmd(cmd))

def test_live():
    """Run live API verification suite."""
    script = os.path.join("scripts", "test_live_db_combinations.py")
    if not os.path.exists(script):
        script = os.path.join("scripts", "test_live.py")
    cmd = [sys.executable, script]
    sys.exit(run_cmd(cmd))

def setup_db():
    """Full database setup: init pgvector, seed CMS data, ingest RAG embeddings."""
    print("=" * 60)
    print("  STEP 1: Running Alembic Migrations")
    print("=" * 60)
    run_cmd([sys.executable, "-m", "alembic", "upgrade", "head"])

    print("\n" + "=" * 60)
    print("  STEP 2: Initializing Vector DB (pgvector)")
    print("=" * 60)
    script_init = os.path.join("scripts", "init_vector_db.py")
    if os.path.exists(script_init):
        run_cmd([sys.executable, script_init])

    print("\n" + "=" * 60)
    print("  STEP 3: Seeding Database with CMS Policies")
    print("=" * 60)
    script_seed = os.path.join("scripts", "seed_db.py")
    if os.path.exists(script_seed):
        run_cmd([sys.executable, script_seed])

    print("\n" + "=" * 60)
    print("  STEP 4: Ingesting RAG Embeddings into pgvector")
    print("=" * 60)
    script_ingest = os.path.join("scripts", "ingest_ncds.py")
    if os.path.exists(script_ingest):
        run_cmd([sys.executable, script_ingest])

    print("\n" + "=" * 60)
    print("  DB SETUP COMPLETE!")
    print("=" * 60)

def validate_db():
    """Check database table counts."""
    script_val = os.path.join("scripts", "validate_db.py")
    if os.path.exists(script_val):
        run_cmd([sys.executable, script_val])

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    if cmd in ("serve", "server", "start"):
        serve()
    elif cmd in ("test", "pytest"):
        test()
    elif cmd in ("test-live", "live"):
        test_live()
    elif cmd in ("setup-db", "init-db", "setup"):
        setup_db()
    elif cmd in ("validate-db", "validate", "check-db"):
        validate_db()
    else:
        print(f"Unknown command: '{cmd}'\n")
        print(__doc__)

if __name__ == "__main__":
    main()
