from pathlib import Path


def test_backup_scripts_exist_and_are_documented_targets():
    backup = Path("scripts/backup_data.sh")
    verify = Path("scripts/verify_restore.sh")
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert backup.exists()
    assert verify.exists()

    assert "backup-data:" in makefile
    assert "verify-restore:" in makefile
