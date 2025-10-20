from fastapi import FastAPI
from datetime import date

app = FastAPI(title="Breakfast Club Planner")

# --- 💰 Precios base (NZD) ---
PRICES = {
    "milk": {"Pak'nSave": 2.20, "New World": 2.30, "Countdown": 2.40},
    "tea": {"Pak'nSave": 6.29, "New World": 6.49, "Countdown": 6.59},
    "bread": {"Pak'nSave": 0.50, "New World": 0.55, "Countdown": 0.60},
    "fruit": {"Pak'nSave": 0.60, "New World": 0.65, "Countdown": 0.70},
    "oats": {"Pak'nSave": 0.80, "New World": 0.85, "Countdown": 0.90},
    "yogurt": {"Pak'nSave": 0.90, "New World": 0.95, "Countdown": 1.00},
    "flour": {"Pak'nSave": 2.50, "New World": 2.70, "Countdown": 2.80},
    "eggs": {"Pak'nSave": 0.90, "New World": 1.00, "Countdown": 1.10},
    "sugar": {"Pak'nSave": 2.80, "New World": 3.00, "Countdown": 3.10},
    "baking_powder": {"Pak'nSave": 2.50, "New World": 2.70, "Countdown": 2.90},
    "butter": {"Pak'nSave": 5.00, "New World": 5.50, "Countdown": 5.80}
}

# --- 🧇 Receta de waffles (por cada 10 niños) ---
WAFFLE_RECIPE = {
    "flour": 500,
    "eggs": 4,
    "milk": 500,
    "sugar": 50,
    "baking_powder": 10,
    "butter": 50
}

@app.get("/")
def home():
    """Ruta principal: muestra estado del servicio."""
    return {"message": "✅ Breakfast Club Planner API is running", "version": "1.0.2"}

@app.get("/jit/plan")
def plan(mon: int, tue: int, live: bool = False):
    """Calcula las cantidades y costos del Breakfast Club."""
    safety_margin = 1.10

    # --- Lunes ---
    monday_items = {
        "milk": mon * 0.25,
        "tea": mon * 0.02,
        "bread": mon * 0.5,
        "fruit": mon * 1,
        "oats": mon * 1,
        "yogurt": mon * 1
    }

    # --- Martes ---
    t_factor = tue / 10
    waffle = {k: v * t_factor for k, v in WAFFLE_RECIPE.items()}
    tuesday_items = {
        "milk": tue * 0.25 + waffle["milk"] / 1000,
        "tea": tue * 0.02,
        "fruit": tue * 1,
        "oats": tue * 1,
        "yogurt": tue * 1,
        "flour": waffle["flour"] / 1000,
        "eggs": waffle["eggs"],
        "sugar": waffle["sugar"] / 1000,
        "baking_powder": waffle["baking_powder"] / 100,
        "butter": waffle["butter"] / 250
    }

    # --- Margen de seguridad ---
    monday_items = {k: v * safety_margin for k, v in monday_items.items()}
    tuesday_items = {k: v * safety_margin for k, v in tuesday_items.items()}

    # --- Calcular costos ---
    totals = {store: 0 for store in ["Pak'nSave", "New World", "Countdown"]}
    for store in totals:
        for item, qty in {**monday_items, **tuesday_items}.items():
            if item in PRICES:
                totals[store] += PRICES[item][store] * qty

    cheapest = min(totals, key=totals.get)

    # --- ✉️ Borrador de email ---
    week = date.today().strftime("%Y-%m-%d")
    email_subject = f"Breakfast Club – Weekly Shopping Plan (Week of {week})"

    email_body = f"""To: mavisi036@gmail.com
Subject: {email_subject}

Hi team,

This week's attendance assumption:
- Monday: {mon} children
- Tuesday: {tue} children

Shopping list:
- Monday: milk, tea, bread, fruit, oats, yogurt
- Tuesday: milk, tea, fruit, oats, yogurt, waffles (homemade)

Estimated costs (with 10% safety margin):
- Pak'nSave: ${totals["Pak'nSave"]:.2f}
- New World: ${totals["New World"]:.2f}
- Countdown: ${totals["Countdown"]:.2f}

Cheapest option: {cheapest}

Please confirm or reply with changes.

Thanks!
"""

    return {
        "attendance": {"monday": mon, "tuesday": tue},
        "monday_items": monday_items,
        "tuesday_items": tuesday_items,
        "totals": totals,
        "cheapest": cheapest,
        "email": {
            "to": "mavisi036@gmail.com",
            "subject": email_subject,
            "body": email_body
        }
    }
from fastapi import FastAPI
from typing import Dict

app = FastAPI(title="Breakfast Club Planner", version="1.1.0")

# -------------------------
# CONFIGURATION CONSTANTS
# -------------------------

EXPECTED_KCAL_PER_CHILD = 450  # NZ Ministry of Health guideline

# Energy content (kcal per unit)
CALORIES = {
    "milk": 640,             # per 1 L
    "yogurt": 60,            # per 100 g
    "cheese": 90,            # per 25 g
    "chicken": 165,          # per 100 g
    "bread": 80,             # per slice
    "bread_roll": 120,       # per roll
    "hashbrown": 130,        # per unit
    "pancake": 110,          # per small pancake
    "fruit": 70,             # per unit
    "oats": 150,             # per 40 g portion
    "cereal": 120,           # per 30 g portion
    "butter": 35,            # per 5 g
    "milo": 120,             # per 200 ml
    "jam": 20,               # per tsp
    "maple_syrup": 18,       # per tsp
    "choc_chips": 50,        # per tbsp
    "berries": 40            # per 50 g
}

# -------------------------
# ROUTES
# -------------------------

@app.get("/")
def home():
    """Check API status."""
    return {"message": "✅ Breakfast Club Planner API is running", "version": "1.1.0"}


@app.post("/jit/consumption")
def record_consumption(data: Dict):
    """
    Record consumption for the week and calculate energy balance.
    Example input:
    {
        "day": "monday",
        "children": 30,
        "items": {
            "milk": 8,
            "bread": 15,
            "yogurt": 2,
            "fruit": 20,
            "hashbrown": 10
        }
    }
    """

    day = data.get("day", "unspecified").capitalize()
    children = data.get("children", 0)
    items = data.get("items", {})

    # --- 1️⃣ Expected energy requirement ---
    expected_total_kcal = children * EXPECTED_KCAL_PER_CHILD

    # --- 2️⃣ Actual energy intake calculation ---
    actual_total_kcal = 0
    detail = {}
    for food, qty in items.items():
        kcal_per_unit = CALORIES.get(food, 0)
        kcal_total = qty * kcal_per_unit
        detail[food] = {
            "quantity": qty,
            "kcal_each": kcal_per_unit,
            "kcal_total": kcal_total
        }
        actual_total_kcal += kcal_total

    # --- 3️⃣ Summary ---
    avg_per_child = actual_total_kcal / children if children > 0 else 0
    percent_of_target = (avg_per_child / EXPECTED_KCAL_PER_CHILD * 100) if children > 0 else 0

    return {
        "day": day,
        "children": children,
        "expected_total_kcal": round(expected_total_kcal, 1),
        "actual_total_kcal": round(actual_total_kcal, 1),
        "average_per_child": round(avg_per_child, 1),
        "percent_of_target": round(percent_of_target, 1),
        "details": detail
    }
