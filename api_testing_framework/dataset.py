"""Build and push the desert-recipe-ingredients dataset to Opik."""

from config import DATASET_NAME, PROJECT_NAME

ITEMS = [
    {"ingredients": "rice, milk, sugar, vanilla"},
    {"ingredients": "chocolate, butter, eggs, flour"},
    {"ingredients": "apples, cinnamon, butter, brown sugar"},
    {"ingredients": "strawberries, cream cheese, graham crackers, sugar"},
    {"ingredients": "bananas, peanut butter, oats, honey"},
    {"ingredients": "mango, coconut milk, lime, sugar"},
    {"ingredients": "lemon, sugar, eggs, butter"},
    {"ingredients": "oats, honey, almonds, dark chocolate"},
    {"ingredients": "pumpkin, cream cheese, cinnamon, nutmeg"},
    {"ingredients": "blueberries, yogurt, honey, granola"},
]


def build_dataset():
    """Create or reuse the Opik dataset and return it."""
    import opik

    client = opik.Opik(project_name=PROJECT_NAME)
    dataset = client.get_or_create_dataset(name=DATASET_NAME)

    existing = dataset.get_items()
    if not existing:
        dataset.insert(ITEMS)
        print(f"  Pushed {len(ITEMS)} items → dataset '{DATASET_NAME}'")
    else:
        print(f"  Dataset '{DATASET_NAME}' already has {len(existing)} items — skipping insert")

    return dataset
