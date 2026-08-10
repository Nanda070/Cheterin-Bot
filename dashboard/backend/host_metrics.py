"""Host / VPS metrics for the super-admin Health page.

Uses psutil when available; falls back to stdlib / platform probes so the
endpoint still works in slim environments.
"""

from __future__ import annotations

import os
import platform
import shutil
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:  # pragma: no cover - exercised via fallbacks in tests when mocked
    psutil = None


def _pct(used: float | int | None, total: float | int | None) -> float | None:
    if used is None or total is None or not total:
        return None
    return round(100.0 * float(used) / float(total), 1)


def _bytes_ram() -> tuple[int | None, int | None]:
    if psutil is not None:
        mem = psutil.virtual_memory()
        return int(mem.used), int(mem.total)
    if sys.platform.startswith("linux"):
        info: dict[str, int] = {}
        try:
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0].endswith(":"):
                    info[parts[0][:-1]] = int(parts[1]) * 1024
        except OSError:
            return None, None
        total = info.get("MemTotal")
        available = info.get("MemAvailable")
        if total is None:
            return None, None
        used = total - available if available is not None else None
        return used, total
    return None, None


def _bytes_disk(path: str | None = None) -> tuple[int | None, int | None]:
    target = path or os.path.abspath(os.sep)
    try:
        usage = shutil.disk_usage(target)
        return int(usage.used), int(usage.total)
    except OSError:
        return None, None


def _cpu_percent() -> float | None:
    if psutil is not None:
        # Non-blocking: first call after import may be 0.0; callers refresh periodically.
        return float(psutil.cpu_percent(interval=None))
    return None


def _load_average() -> list[float] | None:
    try:
        one, five, fifteen = os.getloadavg()
        return [round(one, 2), round(five, 2), round(fifteen, 2)]
    except (AttributeError, OSError):
        return None


def _boot_time() -> float | None:
    if psutil is not None:
        return float(psutil.boot_time())
    if sys.platform.startswith("linux"):
        try:
            uptime_sec = float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
            return time.time() - uptime_sec
        except (OSError, ValueError, IndexError):
            return None
    return None


def _process_info() -> dict | None:
    if psutil is None:
        return {
            "pid": os.getpid(),
            "name": Path(sys.executable).name,
            "rss_bytes": None,
            "create_time": None,
        }
    try:
        proc = psutil.Process(os.getpid())
        with proc.oneshot():
            mem = proc.memory_info()
            return {
                "pid": proc.pid,
                "name": proc.name(),
                "rss_bytes": int(mem.rss),
                "create_time": float(proc.create_time()),
            }
    except Exception:
        return {"pid": os.getpid(), "name": None, "rss_bytes": None, "create_time": None}


def collect_host_metrics() -> dict:
    """Snapshot of host resource usage for the dashboard Health page."""
    ram_used, ram_total = _bytes_ram()
    disk_used, disk_total = _bytes_disk()
    boot = _boot_time()
    now = time.time()
    return {
        "platform": platform.system(),
        "hostname": platform.node() or None,
        "python_version": platform.python_version(),
        "cpu_percent": _cpu_percent(),
        "cpu_count": os.cpu_count(),
        "load_avg": _load_average(),
        "ram": {
            "used_bytes": ram_used,
            "total_bytes": ram_total,
            "percent": _pct(ram_used, ram_total),
        },
        "disk": {
            "used_bytes": disk_used,
            "total_bytes": disk_total,
            "percent": _pct(disk_used, disk_total),
            "path": os.path.abspath(os.sep),
        },
        "uptime_seconds": round(now - boot) if boot is not None else None,
        "boot_time": boot,
        "process": _process_info(),
        "collected_at": now,
    }
