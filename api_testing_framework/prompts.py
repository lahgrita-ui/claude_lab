"""Two prompt variants for the desert-recipe hypothesis experiment.

Python format strings (used at runtime via .format(ingredients=...)).
Jinja2 equivalents are registered in the Opik prompt library by register_prompts().
"""

ZERO_SHOT = """\
You are a creative pastry chef.
Given these ingredients, create a dessert recipe.

Ingredients: {ingredients}

Provide the following:
- Recipe name
- Servings
- Ingredients with amounts
- Numbered step-by-step instructions"""  # end ZERO_SHOT


FEW_SHOT = """\
You are a creative pastry chef.
Given a list of ingredients, create a dessert recipe.

Here are two examples:

Ingredients: rice, milk, sugar
Recipe: Classic Rice Pudding (serves 4)
Ingredients: 1 cup arborio rice, 2 cups whole milk, 3 tbsp sugar, 1 tsp vanilla
Steps:
1. Combine rice and milk in a saucepan over medium heat.
2. Stir constantly until rice absorbs milk, about 20 minutes.
3. Add sugar and vanilla, stir 2 more minutes. Serve warm or chilled.

Ingredients: banana, flour, eggs
Recipe: Banana Loaf Cake (serves 8)
Ingredients: 3 ripe bananas, 2 cups all-purpose flour, 2 eggs, 1/2 cup sugar, 1/4 cup butter
Steps:
1. Preheat oven to 350°F. Grease a loaf pan.
2. Mash bananas; beat in eggs, sugar, and melted butter.
3. Fold in flour until just combined. Pour into pan.
4. Bake 55 minutes until a toothpick comes out clean.

Now create a recipe for:
Ingredients: {ingredients}

Provide the following:
- Recipe name
- Servings
- Ingredients with amounts
- Numbered step-by-step instructions"""


def register_prompts() -> None:
    """Push both prompt variants to the Opik prompt library (versioned).

    Converts Python {ingredients} placeholders to Jinja2 {{ ingredients }}
    so Opik can render them natively in its UI.
    """
    import opik
    from opik.api_objects.prompt.types import PromptType
    from config import PROJECT_NAME

    client = opik.Opik(project_name=PROJECT_NAME)

    for name, template, description in [
        (
            "desert-recipe-zero-shot",
            ZERO_SHOT,
            "Zero-shot: instructs the model to produce a dessert recipe from an ingredient list. No examples provided.",
        ),
        (
            "desert-recipe-few-shot",
            FEW_SHOT,
            "Few-shot: same task with two in-context recipe examples (rice pudding, banana loaf) before the target ingredients.",
        ),
    ]:
        jinja2_template = template.replace("{ingredients}", "{{ ingredients }}")
        prompt = client.create_prompt(
            name=name,
            prompt=jinja2_template,
            description=description,
            type=PromptType.JINJA2,
            tags=["desert-recipes", "hypothesis-test"],
            metadata={
                "version": "v1",
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 600,
            },
            project_name=PROJECT_NAME,
        )
        print(f"  Registered '{name}' v1 (commit: {prompt.commit})")
