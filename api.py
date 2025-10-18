"""
Breakfast Club Planner API – Christchurch, NZ
Calcula cantidades, costos y supermercado más barato
para los desayunos del lunes y martes, con 10% de margen.

Incluye:
- Escalado automático de ingredientes para waffles (martes)
- Costeo por supermercado (Pak’nSave, New World, Countdown)
- Detalle por producto y total
"""

from fastapi import FastAPI, Query
from typing import Dict, List, Optional
from dataclasses import dataclass
import math
import datetime as dt

# ---------------------------------------------------------------------
# Configuración base
# ---------------------------------------------------------------------

app = FastAPI(title="Breakfast Club Planner API")

SUPERMARKETS = ["Pak'nSave", "New World", "Countdown"]

DEFAULT_PRICES: Dict[str, Dict[str, float]] = {
    "Milk (1 L)": {"Pak'nSave": 2.20, "New World": 2.30, "Countdown": 2.40},
    "Tea (50 bags)": {"Pak'nSave": 6.29, "New World": 6.49, "Countdown": 6.59},
    "Bread (unit)": {"Pak'nSave": 0.50, "New World": 0.55, "Countdown": 0.60},
    "Fruit (unit)": {"Pak'nSave": 0.60, "New World": 0.65, "Countdown": 0.70},
    "Oats (portion)": {"Pak'nSave": 0.80, "New World": 0.85, "Countdown": 0.90},
    "Yogurt (cup)": {"Pak'nSave": 0.90, "New World": 0.95, "Countdown": 1.00},
    "Flour (1 kg)": {"Pak'nSave": 2.50, "New World": 2.70, "Countdown": 2.80},
    "Eggs (each)": {"Pak'nSave": 0.90, "New World": 1.00, "Countdown": 1.10},
    "Sugar (1 kg)": {"Pak'nSave": 2.80, "New World": 3.00, "Countdown": 3.10},
    "Baking powder (100 g)": {"Pak'nSave": 2.50, "New World": 2.70, "Countdown": 2.90},
    "Butter (250 g)": {"Pak'nSave": 5.00, "New World": 5.50, "Countdown": 5.80},
}

PACKS = {p: 1 for p in DEFAULT_PRICES.keys()}


# ---------------------------------------------------------------------
# Modelos internos
# ---------------------------------------------------------------------

@dataclass
class Needs:
    mon_children: int
    tue_children: int
    safety_margin: float = 0.10


@dataclass
class Quantities:
    mon: Dict[str, float]
    tue: Dict[str, float]
    waffles: Dict[str, float]
    rounded: Dict[str, int]


# ---------------------------------------------------------------------
# Cálculos principales
# ---------------------------------------------------------------------

def ceil_to_pack(qty: float, pack_size: int = 1) -> int:
    return int(math.ceil(qty / pack_size))


def compute_quantities(needs: Needs) -> Quantities:
    m, t = needs.mon_children, needs.tue_children
    margin = 1 + needs.safety_margin

    per_child = {
        "Milk (1 L)": 1.0,
        "Bread (unit)": 1.0,
        "Fruit (unit)": 1.0,
        "Oats (portion)": 1.0,
        "Yogurt (cup)": 1.0,
    }

    mon = {
        "Milk (1 L)": per_child["Milk (1 L)"] * m * margin,
        "Tea (50 bags)": 1,
        "Bread (unit)": per_child["Bread (unit)"] * m * margin,
        "Fruit (unit)": per_child["Fruit (unit)"] * m * margin,
        "Oats (portion)": per_child["Oats (portion)"] * m * margin,
        "Yogurt (cup)": per_child["Yogurt (cup)"] * m * margin,
    }

    tue = {
        "Milk (1 L)": per_child["Milk (1 L)"] * t * margin,
        "Tea (50 bags)": 1,
        "Fruit (unit)": per_child["Fruit (unit)"] * t * margin,
        "Oats (portion)": per_child["Oats (portion)"] * t * margin,
        "Yogurt (cup)": per_child["Yogurt (cup)"] * t * margin,
    }

    # Ingredientes para waffles (por cada 10 niños)
    scale = (t * margin) / 10.0
    waffles = {
        "Flour (1 kg)": 500.0 * scale,
        "Eggs (each)": 4.0 * scale,
        "Milk for waffles (ml)": 500.0 * scale,
        "Sugar (1 kg)": 50.0 * scale,
        "Baking powder (100 g)": 10.0 * scale,
        "Butter (250 g)": 50.0 * scale,
    }

    milk_total_L = mon["Milk (1 L)"] + tue["Milk (1 L)"] + (waffles["Milk for waffles (ml)"] / 1000.0)
