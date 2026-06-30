"""Run the zero-shot vs. few-shot desert-recipe experiment via Opik evaluate().

Hypothesis: Few-shot prompts produce higher-quality dessert recipes than
zero-shot prompts, as measured by recipe structure completeness and
ingredient relevance.

Two named experiments are pushed to Opik project 'sunny-testing':
  desert_recipes_zero_shot
  desert_recipes_few_shot
"""

import opik
from opik.evaluation import evaluate

from config import PROJECT_NAME, anthropic_client
from metrics import RecipeStructureGrader, make_ingredient_relevance_grader
from prompts import FEW_SHOT, ZERO_SHOT


def make_task(prompt_template: str, label: str):
    """Return an Opik-tracked task function for the given prompt template."""
    client = anthropic_client()

    @opik.track(project_name=PROJECT_NAME, name=f"generate_recipe_{label}")
    def task(dataset_item: dict) -> dict:
        ingredients = dataset_item["ingredients"]
        prompt = prompt_template.format(ingredients=ingredients)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
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

    for label, template in [("zero_shot", ZERO_SHOT), ("few_shot", FEW_SHOT)]:
        print(f"\n  Running experiment: desert_recipes_{label}")
        result = evaluate(
            experiment_name=f"desert_recipes_{label}",
            dataset=dataset,
            task=make_task(template, label),
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
