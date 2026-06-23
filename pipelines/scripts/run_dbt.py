import argparse
import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DBT_PROJECT_DIR = PROJECT_ROOT / "pipelines" / "dbt" / "riskops_dbt"


def run_dbt(command: str, project_dir: Path) -> None:
    profiles_dir = Path(os.getenv("DBT_PROFILES_DIR", str(project_dir)))
    target = os.getenv("DBT_TARGET", "dev")
    dbt_command = [
        "dbt",
        command,
        "--project-dir",
        str(project_dir),
        "--profiles-dir",
        str(profiles_dir),
        "--target",
        target,
    ]
    subprocess.run(dbt_command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run dbt commands for RiskOps.")
    parser.add_argument("command", choices=["debug", "run", "test", "all"])
    parser.add_argument("--project-dir", default=str(DEFAULT_DBT_PROJECT_DIR))
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if args.command == "all":
        for command in ["debug", "run", "test"]:
            run_dbt(command, project_dir)
    else:
        run_dbt(args.command, project_dir)


if __name__ == "__main__":
    main()
