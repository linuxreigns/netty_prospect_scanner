from pathlib import Path


def test_main_does_not_call_create_all():
    main_py = Path("app/main.py").read_text(encoding="utf-8")
    assert "create_all(" not in main_py, "No usar Base.metadata.create_all en runtime; usar Alembic."
