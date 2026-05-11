from pathlib import Path


def test_operations_playbook_and_smoke_script_exist():
    playbook = Path("OPERATIONS_PLAYBOOK.md")
    smoke = Path("scripts/smoke_post_restart.sh")
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert playbook.exists()
    assert smoke.exists()
    assert "smoke-post-restart:" in makefile

    content = playbook.read_text(encoding="utf-8")
    assert "Smoke test post-reinicio" in content
    assert "Backup" in content or "backup" in content
