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
    return {"message": "✅ Breakfast Club Planner API is running", "version": "1.0.1"}

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
    email_body = (
        f"To: mavisi036@gmail.com\n"
        f"Subject: {email_subject}\n\n"
        f"Hi team,\n\n"
        f"This week's attendance assumption:\n"
        f"- Monday: {mon} children\n"
        f"- Tuesday: {tue} children\n\n"
        f"Shopping list:\n"
        f"- Monday: milk, tea, bread, fruit, oats, yogurt\n"
        f"- Tuesday: milk, tea, fruit, oats, yogurt, waffles (homemade)\n\n"
        f"Estimated costs (with 10% safety margin):\n"
        f"- Pak'nSave: ${totals[\"Pak'nSave\"]:.2f}\n"
        f"- New World: ${totals['New World']:.2f}\n"
        f"- Countdown: ${totals['Countdown']:.2f}\n\n"
        f"Cheapest option: {cheapest}\n\n"
        f"Please confirm or reply with changes.\n\nThanks!\n"
    )

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
