"""Two prompt variants for the desert-recipe hypothesis experiment."""

ZERO_SHOT = """\
You are a creative pastry chef.
Given these ingredients, create a dessert recipe.

Ingredients: {ingredients}

Provide the following:
- Recipe name
- Servings
- Ingredients with amounts
- Numbered step-by-step instructions"""

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
