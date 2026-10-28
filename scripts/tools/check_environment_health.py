"""CLI Tool for running SDET Pre-flight Environment & Health checks."""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from qaops.health import run_all_health_checks


def main():
    report = run_all_health_checks()
    print(report.format_console())

    if not report.is_healthy:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
