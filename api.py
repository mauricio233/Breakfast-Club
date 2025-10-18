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
    "butter": {"Pak'nSave": 5.00, "New World": 5.50, "Countdown": 5.80},
}

# --- 🧇 Receta de waffles (por cada 10 niños) ---
WAFFLE_RECIPE = {
    "flour": 500,          # gramos
    "eggs": 4,             # unidades
    "milk": 500,           # mililitros
