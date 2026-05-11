from pathlib import Path


def test_monitoring_scripts_and_service_exist():
    monitor_once = Path("scripts/monitor_services.sh")
    monitor_loop = Path("scripts/monitor_loop.sh")
    monitor_service = Path("scripts/systemd/netty-monitor.service")
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert monitor_once.exists()
    assert monitor_loop.exists()
    assert monitor_service.exists()

    assert "monitor-check:" in makefile
    assert "monitor-loop:" in makefile


def test_monitor_script_has_resource_thresholds():
    script = Path("scripts/monitor_services.sh").read_text(encoding="utf-8")

    assert "CPU_WARN_PCT" in script
    assert "MEM_WARN_PCT" in script
    assert "DISK_WARN_PCT" in script
    assert "/proc/stat" in script
    assert "/proc/meminfo" in script
    assert "shutil.disk_usage" in script
