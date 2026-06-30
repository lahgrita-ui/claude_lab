"""Run the zero-shot vs. few-shot desert-recipe experiment via Opik evaluate().

Hypothesis: Few-shot prompts produce higher-quality dessert recipes than
zero-shot prompts, as measured by recipe structure completeness and
ingredient relevance.

Two named experiments are pushed to Opik project 'sunny-testing':
  desert_recipes_zero_shot
  desert_recipes_few_shot

Prompts are fetched from the Opik Prompt Library inside @opik.track so each
trace links to the exact prompt version that generated it.
"""

import opik
from opik.api_objects.prompt.types import PromptType
from opik.evaluation import evaluate

from config import PROJECT_NAME, anthropic_client
from metrics import RecipeStructureGrader, make_ingredient_relevance_grader
from prompts import FEW_SHOT, ZERO_SHOT

# Maps experiment label → Opik prompt library name
PROMPT_NAMES = {
    "zero_shot": "desert-recipe-zero-shot",
    "few_shot": "desert-recipe-few-shot",
}

# Fallback templates if the prompt doesn't exist in the library yet
_FALLBACK_TEMPLATES = {
    "zero_shot": ZERO_SHOT,
    "few_shot": FEW_SHOT,
}

_opik_client = opik.Opik()


def make_task(label: str):
    """Return an Opik-tracked task that fetches its prompt from the Opik library.

    The get_prompt() call is inside @opik.track so the prompt version is
    linked to the trace and visible in the Opik Traces view.
    """
    anthropic = anthropic_client()
    prompt_name = PROMPT_NAMES[label]
    fallback_template = _FALLBACK_TEMPLATES[label]

    @opik.track(project_name=PROJECT_NAME, name=f"generate_recipe_{label}")
    def task(dataset_item: dict) -> dict:
        # Fetch versioned prompt from Opik library — must be inside @opik.track
        prompt_obj = _opik_client.get_prompt(name=prompt_name)
        if prompt_obj is None:
            # First-run bootstrap: push to library and use immediately
            prompt_obj = _opik_client.create_prompt(
                name=prompt_name,
                prompt=fallback_template.replace("{ingredients}", "{{ ingredients }}"),
                type=PromptType.JINJA2,
                metadata={
                    "version": "v1",
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 600,
                },
            )

        meta = prompt_obj.metadata or {}
        model = meta.get("model", "claude-haiku-4-5-20251001")
        max_tokens = int(meta.get("max_tokens", 600))

        ingredients = dataset_item["ingredients"]
        rendered = prompt_obj.format(ingredients=ingredients)

        response = anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": rendered}],
        )
        return {
            "input": ingredients,
            "output": response.content[0].text,
        }

    return task


def run_experiments(dataset) -> dict[str, object]:
    """Run both prompt variants and return Opik EvaluationResult objects."""
    metrics = [RecipeStructureGrader(), make_ingredient_relevance_grader()]
    results = {}

    for label in ["zero_shot", "few_shot"]:
        print(f"\n  Running experiment: desert_recipes_{label}")
        result = evaluate(
            experiment_name=f"desert_recipes_{label}",
            dataset=dataset,
            task=make_task(label),
            scoring_metrics=metrics,
            project_name=PROJECT_NAME,
        )
        results[label] = result
        print(f"  → experiment 'desert_recipes_{label}' complete")

    return results


def print_summary(results: dict) -> None:
    """Print a simple score comparison table."""
    print("\n" + "=" * 60)
    print("HYPOTHESIS: few-shot > zero-shot on recipe quality")
    print("=" * 60)
    print(f"{'Experiment':<30} {'recipe_structure':>17} {'ingredient_relevance':>20}")
    print("-" * 70)

    for label, result in results.items():
        scores = {}
        for trial in result.test_results:
            for score in trial.score_results:
                scores.setdefault(score.name, []).append(score.value)

        avg = {k: round(sum(v) / len(v), 3) for k, v in scores.items()}
        rs = avg.get("recipe_structure", "n/a")
        ir = avg.get("ingredient_relevance", "n/a")
        print(f"  {label:<28} {str(rs):>17} {str(ir):>20}")

    print("=" * 60)
    print("View full results at https://www.comet.com/opik → sunny-testing")
