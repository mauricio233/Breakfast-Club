from fastapi import FastAPI
from typing import Dict

app = FastAPI(title="Breakfast Club Planner")

# --- Precios base (NZD) ---
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
    "butter": {"Pak'nSave": 5.00, "New World": 5.50, "Countdown": 5.80},
}

# --- Waffle receta (por cada 10 niños) ---
WAFFLE_RECIPE = {
    "flour": 500,          # g
    "eggs": 4,             # unidades
    "milk": 500,           # ml
    "sugar": 50,           # g
    "baking_powder": 10,   # g
    "butter": 50           # g
}


@app.get("/jit/plan")
def plan(mon: int, tue: int, live: bool = False) -> Dict:
    """
    Calcula las cantidades y costos para el Breakfast Club.
    Parámetros:
      - mon: número de niños lunes
      - tue: número de niños martes
    """
    safety_margin = 1.10  # 10%

    # --- Lunes ---
    monday_items = {
        "milk": mon * 0.25,
        "tea": mon * 0.02,
        "bread": mon * 0.5,
        "fruit": mon * 1,
        "oats": mon * 1,
        "yogurt": mon * 1,
    }

    # --- Martes ---
    t_factor = tue / 10
    waffle = {k: v * t_factor for k, v in WAFFLE_RECIPE.items()}
    tuesday_items = {
        "milk": tue * 0.25 + waffle["milk"] / 1000,  # convertir ml → L
        "tea": tue * 0.02,
        "fruit": tue * 1,
        "oats": tue * 1,
        "yogurt": tue * 1,
        "flour": waffle["flour"] / 1000,             # g → kg
        "eggs": waffle["eggs"],
        "sugar": waffle["sugar"] / 1000,             # g → kg
        "baking_powder": waffle["baking_powder"] / 100,  # g → 100 g
        "butter": waffle["butter"] / 250,            # g → 250 g
    }

    # --- Agregar margen de seguridad ---
    monday_items = {k: v * safety_margin for k, v in monday_items.items()}
    tuesday_items = {k: v * safety_margin for k, v in tuesday_items.items()}

    # --- Calcular costos ---
    totals = {store: 0 for store in ["Pak'nSave", "New World", "Countdown"]}
    for store in totals.keys():
        for k, q in {**monday_items, **tuesday_items}.items():
            if k in PRICES:
                totals[store] += PRICES[k][store] * q

    # --- Encontrar supermercado más barato ---
    cheapest = min(totals, key=totals.get)

    return {
        "attendance": {"monday": mon, "tuesday": tue},
        "monday_items": monday_items,
        "tuesday_items": tuesday_items,
        "totals": totals,
        "cheapest": cheapest,
        "email": "mavisi036@gmail.com"
    }
