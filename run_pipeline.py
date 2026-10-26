"""
Sanjeevani Dataset Pipeline Orchestrator
Runs Objective 1 steps in order, pausing at interactive gates.

Steps:
  1  collect   — download Kaggle + iNaturalist images
  2  verify    — IMPPAT check + spot-check grids
  3  clean     — remove corrupt / duplicate / bad images
  4  build     — build master_labels.csv
  5  balance   — plot class distribution
  6  split     — stratified train/val/test split
  7  check     — final validation checklist

Usage:
    python scripts/run_pipeline.py              # full run, interactive gates
    python scripts/run_pipeline.py --from clean # resume from step 3
    python scripts/run_pipeline.py --step build # run only step 4
    python scripts/run_pipeline.py --auto       # skip all confirmation prompts
"""

import argparse
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
SCRIPTS = Path(__file__).parent

STEPS = [
    ("collect",  "Data collection (Kaggle + iNaturalist)",
     [
         [PYTHON, str(SCRIPTS / "collect_kaggle.py")],
         [PYTHON, str(SCRIPTS / "collect_inat.py"), "--priority", "HIGH"],
     ],
     "After collection: check raw/ to see how many images arrived per species."
    ),
    ("verify",   "Label verification (IMPPAT + spot-checks)",
     [[PYTHON, str(SCRIPTS / "verify_labels.py"), "--mode", "all"]],
     "Open reports/spotcheck_*.png and visually confirm every grid looks correct.\n"
     "  Move any obviously wrong images to raw/review/ before continuing."
    ),
    ("clean",    "Image cleaning pipeline",
     [[PYTHON, str(SCRIPTS / "clean_images.py")]],
     "Review metadata/cleaning_summary.csv.\n"
     "  If too many images were removed for a species, collect more."
    ),
    ("build",    "Build master_labels.csv",
     [[PYTHON, str(SCRIPTS / "build_master_csv.py")]],
     "Check for CRITICAL species (< 80 images).\n"
     "  Run collect_inat.py --species <name> for any critical ones."
    ),
    ("balance",  "Class balance chart",
     [[PYTHON, str(SCRIPTS / "check_balance.py")]],
     "Open reports/class_distribution.png.\n"
     "  Red bars = critical (must fix), yellow = acceptable."
    ),
    ("split",    "Train/val/test split",
     [[PYTHON, str(SCRIPTS / "split_dataset.py")]],
     "processed/ is now populated.\n"
     "  SEAL processed/test/ — never touch it until final evaluation."
    ),
    ("check",    "Final validation checklist",
     [[PYTHON, str(SCRIPTS / "final_check.py")]],
     "All checks must be green before moving to Objective 2."
    ),
]

STEP_NAMES = [s[0] for s in STEPS]


def run_command(cmd: list[str]) -> int:
    print(f"\n  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def confirm(prompt: str, auto: bool) -> bool:
    if auto:
        return True
    ans = input(f"\n{prompt} [Y/n] ").strip().lower()
    return ans in ("", "y", "yes")


def main():
    parser = argparse.ArgumentParser(description="Run Sanjeevani Objective 1 pipeline")
    parser.add_argument("--from",  dest="from_step", metavar="STEP",
                        choices=STEP_NAMES, help="Resume from this step")
    parser.add_argument("--step",  metavar="STEP",
                        choices=STEP_NAMES, help="Run only this one step")
    parser.add_argument("--auto",  action="store_true",
                        help="Skip confirmation prompts (non-interactive)")
    args = parser.parse_args()

    if args.step:
        run_steps = [s for s in STEPS if s[0] == args.step]
    elif args.from_step:
        idx = STEP_NAMES.index(args.from_step)
        run_steps = STEPS[idx:]
    else:
        run_steps = STEPS

    print("=" * 60)
    print("  SANJEEVANI SCAN AI — Objective 1: Dataset Engineering")
    print("=" * 60)
    print(f"  Steps to run: {[s[0] for s in run_steps]}\n")

    for step_name, description, commands, gate_msg in run_steps:
        print(f"\n{'─'*60}")
        print(f"  STEP: {step_name.upper()}  —  {description}")
        print(f"{'─'*60}")

        if not confirm(f"  Run '{step_name}'?", args.auto):
            print(f"  Skipped '{step_name}'.")
            continue

        for cmd in commands:
            rc = run_command(cmd)
            if rc != 0:
                print(f"\n  ERROR: command exited with code {rc}.")
                if not confirm("  Continue anyway?", args.auto):
                    print("  Pipeline stopped.")
                    sys.exit(rc)

        print(f"\n  ── Gate: {gate_msg}")
        if step_name != "check":
            if not confirm("  Ready to proceed to the next step?", args.auto):
                print("  Pipeline paused. Re-run with --from to resume.")
                sys.exit(0)

    print("\n" + "=" * 60)
    print("  Objective 1 pipeline complete!")
    print("  Run 'python scripts/final_check.py' if you haven't already.")
    print("=" * 60)


if __name__ == "__main__":
    main()
