from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import Dict

app = FastAPI(title="Breakfast Club Planner", version="1.5.0")

# --- 🌐 Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend local (Vite)
        "https://breakfast-dashboard.onrender.com",  # Production frontend
        "*"  # Allow all during testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 💰 Base Prices (NZD) ---
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
    "milo": {"Pak'nSave": 7.80, "New World": 8.20, "Countdown": 8.40},  # 🆕 Added Milo
}

# --- 🧇 Waffle Recipe (per 10 children) ---
WAFFLE_RECIPE = {
    "flour": 500,  # grams
    "eggs": 4,
    "milk": 500,  # ml
    "sugar": 50,
    "baking_powder": 10,  # grams
    "butter": 50,  # grams
}

# --- 🔹 Nutrition and Calories ---
EXPECTED_KCAL_PER_CHILD = 450  # NZ Ministry of Health guideline

CALORIES = {
    "milk": 640,
    "yogurt": 60,
    "cheese": 90,
    "chicken": 165,
    "bread": 80,
    "bread_roll": 120,
    "hashbrown": 130,
    "pancake": 110,
    "fruit": 70,
    "oats": 150,
    "cereal": 120,
    "butter": 35,
    "milo": 120,
    "jam": 20,
    "maple_syrup": 18,
    "choc_chips": 50,
    "berries": 40,
}

# -------------------------
# ROUTES
# -------------------------

@app.get("/")
def home():
    return {"message": "✅ Breakfast Club Planner API is running", "version": "1.5.0"}


# --- 📅 Weekly Plan ---
@app.get("/jit/plan")
def plan(mon: int, tue: int, live: bool = False):
    """Calculate quantities and costs for Breakfast Club."""
    safety_margin = 1.10

    # --- Monday ---
    monday_items = {
        "milk": mon * 0.25,
        "tea": mon * 0.02,
        "bread": mon * 0.5,
        "fruit": mon * 1,
        "oats": mon * 1,
        "yogurt": mon * 1,
        "milo": mon * 0.02,  # 🆕 added Milo (kg)
    }

    # --- Tuesday (includes waffles) ---
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
        "baking_powder": waffle["baking_powder"] / 10,  # 🔧 adjusted scale
        "butter": waffle["butter"] / 50,  # 🔧 adjusted scale
        "milo": tue * 0.02,  # 🆕 added Milo (kg)
    }

    # Apply safety margin
    monday_items = {k: v * safety_margin for k, v in monday_items.items()}
    tuesday_items = {k: v * safety_margin for k, v in tuesday_items.items()}

    # --- Totals per supermarket ---
    totals = {store: 0 for store in ["Pak'nSave", "New World", "Countdown"]}
    for store in totals:
        for item, qty in {**monday_items, **tuesday_items}.items():
            if item in PRICES:
                totals[store] += PRICES[item][store] * qty

    cheapest = min(totals, key=totals.get)
    week = date.today().strftime("%Y-%m-%d")

    email_subject = f"Breakfast Club – Weekly Shopping Plan (Week of {week})"
    email_body = f"""To: mavisi036@gmail.com
Subject: {email_subject}

Hi team,

This week's attendance assumption:
- Monday: {mon} children
- Tuesday: {tue} children

Shopping list:
- Monday: milk, tea, bread, fruit, oats, yogurt, milo
- Tuesday: milk, tea, fruit, oats, yogurt, waffles (homemade), milo

Estimated costs (10% safety margin):
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
            "body": email_body,
        },
    }


# --- 🍽️ Record consumption and nutrition analysis ---
@app.post("/jit/consumption")
def record_consumption(data: Dict):
    """Record daily consumption and calculate caloric balance."""
    day = data.get("day", "unspecified").capitalize()
    children = data.get("children", 0)
    items = data.get("items", {})

    expected_total_kcal = children * EXPECTED_KCAL_PER_CHILD
    actual_total_kcal = 0
    detail = {}

    for food, qty in items.items():
        kcal_per_unit = CALORIES.get(food, 0)
        kcal_total = qty * kcal_per_unit
        detail[food] = {
            "quantity": qty,
            "kcal_each": kcal_per_unit,
            "kcal_total": kcal_total,
        }
        actual_total_kcal += kcal_total

    avg_per_child = actual_total_kcal / children if children > 0 else 0
    percent_of_target = (
        (avg_per_child / EXPECTED_KCAL_PER_CHILD * 100) if children > 0 else 0
    )

    return {
        "day": day,
        "children": children,
        "expected_total_kcal": round(expected_total_kcal, 1),
        "actual_total_kcal": round(actual_total_kcal, 1),
        "average_per_child": round(avg_per_child, 1),
        "percent_of_target": round(percent_of_target, 1),
        "details": detail,
    }


# --- 🧾 Executive Weekly Report ---
@app.post("/jit/report")
def generate_report(payload: Dict):
    """Combines planning data with real consumption to produce an executive weekly report."""
    mon = payload.get("mon", 0)
    tue = payload.get("tue", 0)
    actual = payload.get("actual", {})

    week = date.today().strftime("%Y-%m-%d")
    expected_children = mon + tue
    actual_children = (
        actual.get("monday", {}).get("children", 0)
        + actual.get("tuesday", {}).get("children", 0)
    )

    expected_kcal = expected_children * EXPECTED_KCAL_PER_CHILD
    total_real_kcal = 0
    details = {}

    for day, data in actual.items():
        items = data.get("items", {})
        children = data.get("children", 0)
        total_day_kcal = 0
        detail_day = {}

        for item, qty in items.items():
            kcal_each = CALORIES.get(item, 0)
            kcal_total = kcal_each * qty
            total_day_kcal += kcal_total
            detail_day[item] = {
                "quantity": qty,
                "kcal_each": kcal_each,
                "kcal_total": kcal_total,
            }

        details[day] = {
            "children": children,
            "total_kcal": total_day_kcal,
            "average_per_child": round(total_day_kcal / children, 1)
            if children
            else 0,
            "details": detail_day,
        }
        total_real_kcal += total_day_kcal

    avg_kcal_per_child = (
        round(total_real_kcal / actual_children, 1) if actual_children else 0
    )
    percent_of_target = (
        round((avg_kcal_per_child / EXPECTED_KCAL_PER_CHILD * 100), 1)
        if actual_children
        else 0
    )

    report_text = f"""
📅 WEEKLY EXECUTIVE REPORT – Breakfast Club
Week of {week}

👧 Attendance Summary:
- Estimated: {expected_children} (Mon {mon} / Tue {tue})
- Actual: {actual_children} (Mon {actual.get('monday', {}).get('children', 0)} / Tue {actual.get('tuesday', {}).get('children', 0)})

🍽 Energy Balance:
- Expected total: {expected_kcal:,} kcal
- Actual total: {total_real_kcal:,} kcal
- Average per child: {avg_kcal_per_child} kcal
- Target achievement: {percent_of_target}% of 450 kcal guideline
"""

    return {
        "week": week,
        "expected_children": expected_children,
        "actual_children": actual_children,
        "expected_kcal_total": expected_kcal,
        "actual_kcal_total": total_real_kcal,
        "average_per_child": avg_kcal_per_child,
        "percent_of_target": percent_of_target,
        "details": details,
        "executive_summary": report_text,
    }
