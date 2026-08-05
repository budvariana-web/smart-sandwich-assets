"""Build English menu data from official i-food translation fields and live image/price data."""
import json
import re
from pathlib import Path

ROOT = Path(r"C:/Users/Asus/AppData/Local/hermes/projects/smart-sandwich-bar")
live = json.loads((ROOT / "menu-data.json").read_text(encoding="utf-8"))
ifood = json.loads((ROOT / "ifood-full-menu.json").read_text(encoding="utf-8"))
texts = ifood["menu_lang_texts"]
products = ifood["food_maker_menu"]

# Same sequence as the live Russian source: active i-food positions, excluding its incomplete test product.
ru_items = [x for x in live["items"] if re.search(r"[А-Яа-яЁё]", x.get("category", ""))]
keys = [
    key for key, product in sorted(products.items(), key=lambda kv: kv[1].get("display_order", 0))
    if product.get("is_active") and not product.get("is_deleted") and key != "Smart_Sandwich_Bar__sandwich_test"
]
if len(ru_items) != len(keys):
    raise RuntimeError(f"Expected matching 23 item lists; live={len(ru_items)} i-food={len(keys)}")

CATEGORY_EN = {
    "Smart_Sandwich_Bar__Burgers": "Burgers",
    "Smart_Sandwich_Bar__Sandwiches": "Sandwiches",
    "Smart_Sandwich_Bar__Bruschetta": "Bruschetta",
    "Smart_Sandwich_Bar__Focaccia": "Focaccia",
    "Smart_Sandwich_Bar__Appetizers": "Appetizers",
    "Smart_Sandwich_Bar__Bread": "Bread",
    "Smart_Sandwich_Bar__Desserts": "Desserts",
    "Smart_Sandwich_Bar__Sauces": "Sauces",
}
# Marketing-friendly display titles (i-food literal names can contain outdated promo copy or unmatched quotes).
NAME_EN = {
    "Smart_Sandwich_Bar__Black_Beef_Burger": "MACHO BURGER",
    "Smart_Sandwich_Bar__Pink_Chicken_Burger": "BELLA BURGER",
    "Smart_Sandwich_Bar__kombo_bella_burger": "Bella Burger Set: burger, fries & sauce",
    "Smart_Sandwich_Bar__Burger_Combo_Burger_Fries_Sauce": "MACHO BURGER Set: burger, fries & sauce",
    "Smart_Sandwich_Bar__Neapolitano_Sandwich": "Neapolitano Sandwich",
    "Smart_Sandwich_Bar__Roasted_Pork_Sandwich_Ukrainian_Vibe": "Ukrainian Vibe Sandwich",
    "Smart_Sandwich_Bar__Mortadella_Sandwich": "Neapolitano Plus Sandwich",
    "Smart_Sandwich_Bar__Prosciutto_Sandwich": "Montenegro Love Sandwich",
    "Smart_Sandwich_Bar__Catalan_Chicken_Sandwich": "Catalan Chicken Sandwich",
    "Smart_Sandwich_Bar__Salami_Sandwich": "Salami Sandwich",
    "Smart_Sandwich_Bar__Bruschetta_with_Caramelized_Onion_and_Prosciutto": "Bruschetta with Caramelized Onion & Prosciutto",
    "Smart_Sandwich_Bar__Bruschetta_with_Cherry_Tomatoes_Olives_and_Salami": "Bruschetta with Cherry Tomatoes, Olives & Salami",
    "Smart_Sandwich_Bar__Focaccia_with_Olives_and_Cheese": "Focaccia with Olives & Cheese",
    "Smart_Sandwich_Bar__Garlic_Rye_Croutons": "Garlic Rye Croutons",
    "Smart_Sandwich_Bar__Garlic_Croutons_Set_3_Sauces": "Croutons Set with 3 Sauces",
    "Smart_Sandwich_Bar__French_Fries": "French Fries",
    "Smart_Sandwich_Bar__Orange_Cake": "Taormina Orange Cake",
    "Smart_Sandwich_Bar__Caramelized_Onion": "Caramelized Onion Sauce",
    "Smart_Sandwich_Bar__Marinade_Sauce": "Marinade Sauce",
    "Smart_Sandwich_Bar__Spicy_Ketchup": "Spicy Ketchup",
}

# Complete English descriptions where i-food has no English entry.
MANUAL_DESC_EN = {
    "Smart_Sandwich_Bar__kombo_bella_burger": "Pink brioche chicken burger (400 g), 150 g French fries and a sauce of your choice: aioli, ketchup or chilli ketchup.",
    "Smart_Sandwich_Bar__Burger_Combo_Burger_Fries_Sauce": "Black MACHO burger with beef, French fries with smoked paprika, and a sauce of your choice: ketchup, chilli ketchup or aioli with French mustard.",
    "Smart_Sandwich_Bar__Prosciutto_Sandwich": "A classic Montenegrin flavour: Njeguši cured prosciutto, Edam cheese, fresh cucumber and a sauce of ketchup, mayonnaise, mustard and pickles.",
    "Smart_Sandwich_Bar__Salami_Sandwich": "Italian salami, fresh tomato and mozzarella on ciabatta, toasted in a press grill until crisp.",
    "Smart_Sandwich_Bar__Bruschetta_with_Caramelized_Onion_and_Prosciutto": "Toasted bread with caramelized onion and tender prosciutto.",
    "Smart_Sandwich_Bar__Bruschetta_with_Cherry_Tomatoes_Olives_and_Salami": "Toasted bread with cherry tomatoes, olives and salami.",
    "Smart_Sandwich_Bar__Focaccia_with_Olives_and_Cheese": "Homemade focaccia with olives and cheese — delicious as a snack or as a sandwich base.",
    "Smart_Sandwich_Bar__Arancini": "A Sicilian street-food classic: a crispy fried rice ball filled with meat ragù, green peas and mozzarella. 220 g each.",
    "Smart_Sandwich_Bar__Garlic_Rye_Croutons": "House-baked dark rye bread with malt, fried until crisp and finished with garlic confit.",
    "Smart_Sandwich_Bar__Garlic_Croutons_Set_3_Sauces": "Garlic rye croutons served with three sauces: aioli, caramelized onion and Marinade sauce with olive oil, garlic and herbs.",
    "Smart_Sandwich_Bar__French_Fries": "Golden French fries (150 g), served with a choice of ketchup, chilli ketchup or aioli.",
    "Smart_Sandwich_Bar__Ciabatta": "Italian ciabatta, baked in-house and used for our sandwiches.",
    "Smart_Sandwich_Bar__Orange_Cake": "Made only with natural ingredients: oranges, vegetable oil, eggs and flour. A taste of Sicily in every slice.",
    "Smart_Sandwich_Bar__Caramelized_Onion": "Sweet and savoury caramelized onion sauce.",
    "Smart_Sandwich_Bar__Aioli": "Creamy handmade aioli sauce.",
    "Smart_Sandwich_Bar__Spicy_Ketchup": "Ketchup with a spicy kick.",
    "Smart_Sandwich_Bar__ketchup": "Classic ketchup.",
}

out = []
for item, key in zip(ru_items, keys):
    prod = products[key]
    title = NAME_EN.get(key) or texts.get(key, {}).get("en") or item["name"]
    title = title.replace('"', '').strip()
    desc = MANUAL_DESC_EN.get(key) or texts.get(key + "__description", {}).get("en") or item.get("description", "")
    desc = re.sub(r"\s+", " ", desc.replace("<br>", " ")).strip()
    out.append({
        **item,
        "category": CATEGORY_EN.get(prod.get("category_code"), item["category"]),
        "name": title,
        "description": desc,
    })

payload = {**live, "items": out, "language": "en"}
(ROOT / "menu-data-en.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
for item in out:
    print(f"{item['category']} | {item['name']} | {item['price']}")
print(f"Wrote {len(out)} English items")
