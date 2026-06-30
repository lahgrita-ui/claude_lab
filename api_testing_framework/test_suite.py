"""Two-case test suite comparing zero-shot vs few-shot with expected outputs.

Test cases have a ground-truth reference recipe so graders can measure
output quality against a known-good baseline — not just structural checks.

Two new graders added on top of the existing ones:
  ReferenceQualityGrader  — LLM judge comparing output vs expected_output
  IngredientHallucinationGrader — code-based, penalises invented ingredients

Both prompt configs (zero_shot, few_shot) run on the same 2 items and
upload to Opik project 'sunny-testing' as:
  test_suite_zero_shot
  test_suite_few_shot
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env", override=True)

sys.path.insert(0, str(Path(__file__).parent))

import json
import os
import re

import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import BaseMetric
from opik.evaluation.metrics.score_result import ScoreResult

from config import PROJECT_NAME, configure
from experiment import make_task
from metrics import RecipeStructureGrader, make_ingredient_relevance_grader
from prompts import FEW_SHOT, ZERO_SHOT

# ── Test dataset ──────────────────────────────────────────────────────────────

SUITE_DATASET_NAME = "recipe-test-suite"

TEST_CASES = [
    {
        "ingredients": "rice, milk, sugar, vanilla",
        "expected_output": (
            "Classic Vanilla Rice Pudding (serves 4)\n"
            "Ingredients:\n"
            "- 1 cup arborio rice\n"
            "- 2 cups whole milk\n"
            "- 3 tbsp sugar\n"
            "- 1 tsp vanilla extract\n\n"
            "Steps:\n"
            "1. Combine rice and milk in a saucepan over medium heat.\n"
            "2. Stir constantly until rice absorbs the milk, about 20 minutes.\n"
            "3. Stir in sugar and vanilla extract.\n"
            "4. Cook 2 more minutes, then remove from heat.\n"
            "5. Serve warm or refrigerate 2 hours and serve chilled."
        ),
    },
    {
        "ingredients": "chocolate, butter, eggs, flour",
        "expected_output": (
            "Rich Chocolate Brownies (serves 12)\n"
            "Ingredients:\n"
            "- 200g dark chocolate, chopped\n"
            "- 100g unsalted butter\n"
            "- 3 large eggs\n"
            "- 1 cup all-purpose flour\n"
            "- 1/2 cup sugar\n\n"
            "Steps:\n"
            "1. Preheat oven to 350°F. Grease a 9x9 baking pan.\n"
            "2. Melt chocolate and butter together; stir until smooth.\n"
            "3. Whisk in sugar, then eggs one at a time.\n"
            "4. Fold in flour until just combined — do not overmix.\n"
            "5. Pour into pan and bake 25 minutes until a toothpick has moist crumbs.\n"
            "6. Cool completely before cutting into squares."
        ),
    },
]

# ── Graders ───────────────────────────────────────────────────────────────────

class ReferenceQualityGrader(BaseMetric):
    """LLM-as-judge: compares generated recipe against the expected_output reference.

    Scores 4 axes equally (cooking method, ingredient proportions, step flow, dish type).
    Uses claude-haiku-4-5-20251001 via direct Anthropic call so it can compare two
    full text blocks — GEval only inspects a single output field.
    """

    def __init__(self):
        super().__init__(name="reference_quality")

    def score(self, output: str, expected_output: str = "", **kwargs) -> ScoreResult:
        if not expected_output or not output:
            return ScoreResult(name=self.name, value=0.0, reason="missing output or reference")

        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

        prompt = (
            "Compare these two dessert recipes and score their similarity on a 0.0–1.0 scale.\n\n"
            f"REFERENCE RECIPE:\n{expected_output}\n\n"
            f"GENERATED RECIPE:\n{output}\n\n"
            "Score based on 4 equally-weighted axes:\n"
            "1. Cooking method and technique match\n"
            "2. Ingredient quantities in the same ballpark\n"
            "3. Step count and logical flow are similar\n"
            "4. Final dish type matches (e.g., both are pudding, both are brownies)\n\n"
            "1.0 = all 4 match  |  0.75 = 3 of 4  |  0.5 = 2 of 4  |  0.25 = 1 of 4  |  0.0 = none\n\n"
            'Reply ONLY with valid JSON: {"score": <float 0.0-1.0>, "reason": "<one sentence>"}'
        )

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            raw = response.content[0].text.strip()
            # strip optional ```json ... ``` code fence the model sometimes adds
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S).strip()
            result = json.loads(raw)
            value = max(0.0, min(1.0, float(result["score"])))
            return ScoreResult(name=self.name, value=round(value, 3), reason=result.get("reason", ""))
        except Exception as exc:
            return ScoreResult(name=self.name, value=0.0, reason=f"parse error: {exc}")


class IngredientHallucinationGrader(BaseMetric):
    """Code-based: penalises recipes that invent savoury ingredients not in the list.

    Checks for surprising protein/vegetable/condiment terms absent from the
    ingredient list.  Returns 1.0 (no hallucination) down to 0.0 (severe).
    """

    _FLAGS = [
        (r"\b(chicken|beef|pork|lamb|salmon|tuna|shrimp|bacon)\b", "unexpected protein"),
        (r"\b(tomato|onion|garlic|pepper|broccoli|spinach|carrot|celery)\b", "unexpected vegetable"),
        (r"\b(soy sauce|worcestershire|mustard|mayo|ketchup|vinegar)\b", "unexpected condiment"),
    ]

    def __init__(self):
        super().__init__(name="no_hallucination")

    def score(self, output: str, ingredients: str = "", **kwargs) -> ScoreResult:
        violations = []
        for pattern, label in self._FLAGS:
            for match in re.finditer(pattern, output, re.I):
                word = match.group(0).lower()
                if word not in ingredients.lower():
                    violations.append(f"{label}: '{word}'")

        value = max(0.0, round(1.0 - 0.4 * len(violations), 3))
        reason = f"violations={violations}" if violations else "no hallucinated ingredients"
        return ScoreResult(name=self.name, value=value, reason=reason)


# ── Dataset builder ───────────────────────────────────────────────────────────

def build_test_dataset():
    """Create or reuse the 2-item test-suite dataset in Opik."""
    client = opik.Opik(project_name=PROJECT_NAME)
    dataset = client.get_or_create_dataset(name=SUITE_DATASET_NAME)

    existing = dataset.get_items()
    if not existing:
        dataset.insert(TEST_CASES)
        print(f"  Pushed {len(TEST_CASES)} test cases → '{SUITE_DATASET_NAME}'")
    else:
        print(f"  Dataset '{SUITE_DATASET_NAME}' already has {len(existing)} items — skipping insert")

    return dataset


# ── Experiment runner ─────────────────────────────────────────────────────────

def run_test_suite(dataset) -> dict:
    """Run both prompt configs on the 2 test cases; return EvaluationResult objects."""
    metrics = [
        RecipeStructureGrader(),
        make_ingredient_relevance_grader(),
        ReferenceQualityGrader(),
        IngredientHallucinationGrader(),
    ]

    results = {}
    for label, template in [("zero_shot", ZERO_SHOT), ("few_shot", FEW_SHOT)]:
        exp_name = f"test_suite_{label}"
        print(f"\n  Running: {exp_name}")
        result = evaluate(
            experiment_name=exp_name,
            dataset=dataset,
            task=make_task(template, label),
            scoring_metrics=metrics,
            project_name=PROJECT_NAME,
        )
        results[label] = result
        print(f"  → '{exp_name}' complete")

    return results


# ── Summary printer ───────────────────────────────────────────────────────────

_METRICS = ["recipe_structure", "ingredient_relevance", "reference_quality", "no_hallucination"]

def print_test_results(results: dict) -> None:
    col = 20
    header = f"{'Experiment':<16}" + "".join(f"{m:>{col}}" for m in _METRICS)
    print("\n" + "=" * (16 + col * len(_METRICS)))
    print("TEST SUITE: zero-shot vs few-shot — 2 cases with expected outputs")
    print("=" * (16 + col * len(_METRICS)))
    print(header)
    print("-" * (16 + col * len(_METRICS)))

    for label, result in results.items():
        scores: dict[str, list] = {}
        for trial in result.test_results:
            for sr in trial.score_results:
                scores.setdefault(sr.name, []).append(sr.value)

        avg = {k: round(sum(v) / len(v), 3) for k, v in scores.items()}
        row = f"  {label:<14}" + "".join(f"{str(avg.get(m, 'n/a')):>{col}}" for m in _METRICS)
        print(row)

    print("=" * (16 + col * len(_METRICS)))
    print("View results at https://www.comet.com/opik → sunny-testing")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("── Recipe Test Suite: 2 cases with expected outputs ──")

    print("\n[1/3] Configuring Opik...")
    configure()
    print("  Opik configured → project: sunny-testing")

    print("\n[2/3] Building test dataset...")
    dataset = build_test_dataset()

    print("\n[3/3] Running test suite (zero-shot + few-shot)...")
    results = run_test_suite(dataset)

    print_test_results(results)


if __name__ == "__main__":
    main()
