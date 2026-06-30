"""Load environment and configure Opik for the sunny-testing project."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_ENV = Path(__file__).parent.parent / ".env"

PROJECT_NAME = "sunny-testing"
DATASET_NAME = "desert-recipe-ingredients"


def configure() -> None:
    """Load root .env and initialise Opik (no-op if already configured)."""
    load_dotenv(ROOT_ENV)

    api_key = os.environ.get("OPIK_API_KEY")
    if not api_key:
        raise EnvironmentError("OPIK_API_KEY not found in .env")

    import opik
    opik.configure(api_key=api_key, use_local=False)


def anthropic_client():
    """Return an Anthropic client wrapped with Opik tracing."""
    import anthropic
    from opik.integrations.anthropic import track_anthropic

    load_dotenv(ROOT_ENV)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not found in .env")

    return track_anthropic(anthropic.Anthropic(api_key=api_key))
