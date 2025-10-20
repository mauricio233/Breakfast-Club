from fastapi import FastAPI
from datetime import date
from typing import Dict

app = FastAPI(title="Breakfast Club Planner", version="1.3.0")

# --- 💰 Base Prices (NZD) ---
PRICES = {
    "milk": {"Pak'nSave": 2.20, "New World": 2.30, "Countdown": 2.40},
    "tea": {"Pak'nSave": 6.29, "New World": 6.49, "Countdown": 6.59},
    "bread": {"Pak'nSave": 0.50, "New World": 0.55, "Countdown": 0.60},
    "fruit": {"Pak'nSave": 0.60, "New World": 0.65, "Countdown": 0.70},
    "oats": {"Pak'nSave": 0.80, "New World": 0.85, "Countdown": 0.90},
    "yogurt": {"Pak'nSave": 4.50, "New World": 4.80, "Countdown": 5.00},  # per litre
    "flour": {"Pak'nSave": 2.50, "New World": 2.70, "Countdown": 2.80},
    "eggs": {"Pak'nSave": 0.90, "New World": 1.00, "Countdown": 1.10},
    "sugar": {"Pak'nSave": 2.80, "New World": 3.00, "Countdown": 3.10},
    "baking_powder": {"Pak'nSave": 2.50, "New World": 2.70, "Countdown": 2.90},
    "butter": {"Pak'nSave": 5.00, "New World": 5.50, "Countdown": 5.80}
}

# --- 🧇 Waffle recipe (per 10 children) ---
WAFFLE_RECIPE = {
    "flour": 500,
    "eggs": 4,
    "milk": 500,
    "sugar": 50,
    "baking_powder": 10,
    "butter": 50
}

# --- 🔹 Nutrition data ---
EXPECTED_KCAL_PER_CHILD = 450  # NZ Ministry of Health recommendation

CALORIES = {
    "milk": 640,            # per litre
    "yogurt": 600,          # per litre
    "cheese": 90,           # per 25 g
    "chicken": 165,         # per 100 g
    "bread": 80,            # per slice
    "bread_roll": 120,      # per roll
    "hashbrown": 130,       # per unit
    "pancake": 110,         # per unit
    "fruit": 70,            # per piece
    "oats": 150,            # per 40 g
    "cereal": 120,          # per 30 g
    "butter": 35,           # per 5 g
    "milo": 120,            # per 200 ml
    "jam": 20,              # per tsp
    "maple_syrup": 18,      # per tsp
    "choc_chips": 50,       # per tbsp
    "berries": 40           # per 50 g
}

# --- 📏 Units for reporting clarity ---
UNITS = {
    "milk": "L",
    "yogurt": "L",
    "tea": "kg",
    "bread": "slices",
    "fruit": "pieces",
    "oats": "servings",
    "flour": "kg",
    "eggs": "units",
    "sugar": "kg",
    "baking_powder": "kg",
    "butter": "kg"
}

# -------------------------
# ROUTES
# -------------------------

@app.get("/")
def home():
    """Check API status."""
    return {"message": "✅ Breakfast Club Planner API is running", "version": "1.3.0"}


# --- 📅 Weekly Plan ---
@app.get("/jit/plan")
def plan(mon: int, tue: int, live: bool = False):
    """Calculate weekly quantities and costs."""
    safety_margin = 1.10

    monday_items = {
        "milk": mon * 0.25,
        "tea": mon * 0.02,
        "bread": mon * 0.5,
        "fruit": mon * 1,
        "oats": mon * 1,
        "yogurt": mon * 0.1  # litres (1L per 10 children)
    }

    t_factor = tue / 10
    waffle = {k: v * t_factor for k, v in WAFFLE_RECIPE.items()}
    tuesday_items = {
        "milk": tue * 0.25 + waffle["milk"] / 1000,
        "tea": tue * 0.02,
        "fruit": tue * 1,
        "oats": tue * 1,
        "yogurt": tue * 0.1,  # litres
        "flour": waffle["flour"] / 1000,
        "eggs": waffle["eggs"],
        "sugar": waffle["sugar"] / 1000,
        "baking_powder": waffle["baking_powder"] / 100,
        "butter": waffle["butter"] / 250
    }

    monday_items = {k: v * safety_margin for k, v in monday_items.items()}
    tuesday_items = {k: v * safety_margin for k, v in tuesday_items.items()}

    totals = {store: 0 for store in ["Pak'nSave", "New World", "Countdown"]}
    for store in totals:
        for item, qty in {**monday_items, **tuesday_items}.items():
            if item in PRICES:
                totals[store] += PRICES[item][store] * qty

    cheapest = min(totals, key=totals.get)
    week = date.today().strftime("%Y-%m-%d")

    # --- Executive report text ---
    report_text = f"""
📊 WEEKLY BREAKFAST CLUB PLAN
Week of {week}

👧 Attendance Forecast:
- Monday: {mon} children
- Tuesday: {tue} children

🧾 Estimated Ingredient Quantities:
Monday:
{chr(10).join([f"  • {item.capitalize()}: {round(qty,2)} {UNITS.get(item,'')}" for item, qty in monday_items.items()])}

Tuesday:
{chr(10).join([f"  • {item.capitalize()}: {round(qty,2)} {UNITS.get(item,'')}" for item, qty in tuesday_items.items()])}

💰 Cost Estimate (10% safety margin):
- Pak'nSave: ${totals['Pak'nSave']:.2f}
- New World: ${totals['New World']:.2f}
- Countdown: ${totals['Countdown']:.2f}

🏆 Recommended Supplier: {cheapest}

This plan aligns with NZ Ministry of Health nutritional guidelines (avg. 450 kcal/child/day).
"""

    return {
        "attendance": {"monday": mon, "tuesday": tue},
        "monday_items": monday_items,
        "tuesday_items": tuesday_items,
        "totals": totals,
        "cheapest": cheapest,
        "executive_summary": report_text
    }
