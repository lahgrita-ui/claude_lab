"""Entry point for the desert-recipe prompt evaluation framework.

Usage (from claude_lab/ root):
    uv run python api_testing_framework/main.py

What it does:
  1. Loads root .env (ANTHROPIC_API_KEY, OPIK_API_KEY)
  2. Configures Opik for project 'sunny-testing'
  3. Creates / reuses dataset 'desert-recipe-ingredients' (10 items)
  4. Runs two experiments: zero_shot vs. few_shot
  5. Prints a score comparison summary
"""

import sys
from pathlib import Path

# load root .env FIRST — before any opik/anthropic imports read env vars
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

# make sibling imports work when run as a script
sys.path.insert(0, str(Path(__file__).parent))

from config import configure
from dataset import build_dataset
from experiment import print_summary, run_experiments


def main():
    print("── Desert Recipe Prompt Evaluation ──")

    print("\n[1/3] Configuring Opik...")
    configure()
    print("  Opik configured → project: sunny-testing")

    print("\n[2/3] Building dataset...")
    dataset = build_dataset()

    print("\n[3/3] Running experiments...")
    results = run_experiments(dataset)

    print_summary(results)


if __name__ == "__main__":
    main()
