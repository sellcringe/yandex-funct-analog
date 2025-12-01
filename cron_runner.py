import os
import yaml
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parent

FUNCTION_ROOTS = [
    ROOT / "functions",
    # ROOT / "web_functions",
]

CRON_FILE = "/tmp/generated_cron"


def find_functions():
    """Ищет все каталоги с func.yaml"""
    configs = []
    for root in FUNCTION_ROOTS:
        if not root.exists():
            continue
        for item in root.iterdir():
            func_dir = item
            if func_dir.is_dir():
                cfg_path = func_dir / "func.yaml"
                if cfg_path.exists():
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}
                    configs.append((func_dir, cfg))
    return configs


def build_cron():
    lines = [
        "SHELL=/bin/bash",
        f"PYTHONPATH={ROOT}",
        f"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    ]

    for func_dir, cfg in find_functions():
        schedule = cfg.get("schedule")
        if not schedule:
            continue

        func_path = str(func_dir.relative_to(ROOT)).replace("/", ".")
        cmd = f"python3 {ROOT}/runner.py {func_path} --event '{{}}'"

        lines.append(f"{schedule} {cmd}")

    with open(CRON_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    print("Cron file generated:")
    print("\n".join(lines))


def install_cron():
    if not os.path.exists(CRON_FILE):
        print(f"ERROR: Cron file not found: {CRON_FILE}")
        exit(1)

    subprocess.run(["crontab", CRON_FILE], check=True)
    print("Cron installed.")


if __name__ == "__main__":
    build_cron()
    install_cron()
