"""Evaluation metrics for the desert-recipe experiment.

Two graders:
1. RecipeStructureGrader — fast code-based, parallel-safe, checks structural
   completeness (name, amounts, numbered steps, minimum length).
2. ingredient_relevance_grader — LLM-as-judge via Opik GEval that checks
   whether the recipe actually uses the supplied ingredients.
"""

import re

from opik.evaluation.metrics import BaseMetric, GEval
from opik.evaluation.metrics.score_result import ScoreResult


class RecipeStructureGrader(BaseMetric):
    """Code-based grader — stateless, runs in parallel across dataset items.

    Scores 4 equally-weighted checks (0.0 – 1.0):
      has_recipe_name    — output contains a title-like line or 'recipe'
      has_amounts        — output mentions cup/tbsp/tsp/gram/oz/ml
      has_numbered_steps — output contains '1.' or 'Step 1' pattern
      min_length         — at least 80 words (filters trivially short outputs)
    """

    def __init__(self):
        super().__init__(name="recipe_structure")

    def score(self, output: str, **kwargs) -> ScoreResult:
        checks = {
            "has_recipe_name": bool(
                re.search(r"recipe|:\s*\n|\b[A-Z][a-z]+ (Cake|Pudding|Tart|Pie|Mousse|Crumble|Cookies|Bars|Parfait|Sorbet)\b", output)
            ),
            "has_amounts": bool(
                re.search(r"\d+\s*(cup|tbsp|tsp|gram|oz|ml|lb|kg|litre|liter|pound)", output, re.I)
            ),
            "has_numbered_steps": bool(
                re.search(r"(step\s*\d|^\s*\d+[\.\)]\s)", output, re.I | re.MULTILINE)
            ),
            "min_length": len(output.split()) >= 80,
        }
        value = sum(checks.values()) / len(checks)
        return ScoreResult(
            name=self.name,
            value=round(value, 3),
            reason=f"checks={checks}",
        )


def make_ingredient_relevance_grader() -> GEval:
    """Build the GEval grader lazily — called after dotenv has loaded the API key.

    GEval scores on a 0-10 integer scale (Opik normalises to 0-1 by ÷10).
    """
    return GEval(
        name="ingredient_relevance",
        task_introduction=(
            "You are evaluating whether a generated dessert recipe uses the "
            "ingredients mentioned in the recipe text. Score on a 0-10 integer scale."
        ),
        evaluation_criteria="""\
Read the recipe text and judge how thoroughly it incorporates a variety of
key dessert ingredients (things like sugars, dairy, eggs, flour, fruits,
spices, or other flavouring agents).

10 — Recipe uses 4 or more distinct key dessert ingredients with specific amounts.
7-9 — Recipe uses 3 key ingredients with amounts; one ingredient is generic/vague.
4-6 — Recipe uses only 2 key ingredients or amounts are missing for most.
1-3 — Recipe mentions ingredients but gives no quantities or method.
0 — No recognisable dessert ingredients or recipe is completely absent.

Score as a single integer 0-10.
""",
        model="claude-haiku-4-5-20251001",
    )
