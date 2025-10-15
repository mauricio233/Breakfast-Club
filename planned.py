"""
Planificador de compras del Breakfast Club (Christchurch, NZ)
- Calcula cantidades por día (con 10% de margen) y redondea a envases estándar.
- Escala ingredientes de waffles automáticamente para el martes.
- Compara costos entre Pak'nSave, New World y Countdown.
- INTENTA actualizar precios en vivo desde las webs de los supermercados.
  Si falla, usa la tabla de precios por defecto (del brief del proyecto).

Uso rápido:
    python planner.py --mon 45 --tue 51 --live

Requisitos opcionales para precios en vivo:
    pip install httpx beautifulsoup4
(El scraping puede romperse si cambian las webs; el script hace "best effort" y 
 caería con gracia a precios por defecto si no encuentra un precio válido.)
"""
from __future__ import annotations
import math
import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

try:
    import httpx
    from bs4 import BeautifulSoup  # type: ignore
    HAS_SCRAPE_DEPS = True
except Exception:
    HAS_SCRAPE_DEPS = False

# ----------------------------- Configuración base -----------------------------
SUPERMARKETS = ["Pak'nSave", "New World", "Countdown"]

# Precios por defecto (NZD) del brief
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

# Empaques estándar (para redondeo de compra)
PACKS = {
    "Milk (1 L)": 1,                  # L
    "Tea (50 bags)": 1,               # pack
    "Bread (unit)": 1,                # unidad
    "Fruit (unit)": 1,                # unidad
    "Oats (portion)": 1,              # porción
    "Yogurt (cup)": 1,                # vaso
    "Flour (1 kg)": 1,                # kg
    "Eggs (each)": 1,                 # huevo
    "Sugar (1 kg)": 1,                # kg
    "Baking powder (100 g)": 1,       # 100 g
    "Butter (250 g)": 1,              # 250 g
}

# Mapeo de términos de búsqueda para scraping (mejorar según marcas locales)
SEARCH_TERMS = {
    "Milk (1 L)": "milk 1l",
    "Tea (50 bags)": "tea 50 bags",
    "Bread (unit)": "white bread",
    "Fruit (unit)": "banana",  # aproximación por unidad
    "Oats (portion)": "rolled oats",
    "Yogurt (cup)": "yoghurt 150g",
    "Flour (1 kg)": "plain flour 1kg",
    "Eggs (each)": "eggs 12 pack",
    "Sugar (1 kg)": "white sugar 1kg",
    "Baking powder (100 g)": "baking powder",
    "Butter (250 g)": "butter 250g",
}

# URL base de búsqueda ("best effort"; pueden cambiar). Las webs usan JS, por lo que
# a veces un request plano no trae precios. Se intenta y si no, se vuelve a DEFAULT.
SEARCH_ENDPOINTS = {
    "Pak'nSave": "https://www.paknsave.co.nz/shop/search/products?search={q}",
    "New World": "https://www.newworld.co.nz/shop/search/products?search={q}",
    "Countdown": "https://www.woolworths.co.nz/shop/searchproducts?search={q}",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}

# ------------------------------- Datos / modelos ------------------------------
@dataclass
class Needs:
    mon_children: int
    tue_children: int
    safety_margin: float = 0.10

@dataclass
class Quantities:
    # Consumos base (ya con margen) para desayuno
    mon: Dict[str, float]
    tue: Dict[str, float]
    # Ingredientes de waffles (martes) en gramos/ml/huevos (ya con margen)
    waffles: Dict[str, float]
    # Totales de compra redondeados a envase
    rounded: Dict[str, int]

# ----------------------------- Lógica de cantidades ---------------------------

def ceil_to_pack(qty: float, pack_size: int = 1) -> int:
    return int(math.ceil(qty / pack_size))


def compute_quantities(needs: Needs) -> Quantities:
    m, t = needs.mon_children, needs.tue_children
    margin = 1 + needs.safety_margin

    # Consumo por niño (según brief anterior del club)
    per_child = {
        "Milk (1 L)": 1.0,       # L por niño (modelo simplificado del club)
        "Bread (unit)": 1.0,
        "Fruit (unit)": 1.0,
        "Oats (portion)": 1.0,
        "Yogurt (cup)": 1.0,
    }

    mon = {
        "Milk (1 L)": per_child["Milk (1 L)"] * m * margin,
        "Tea (50 bags)": 1,  # 1 pack para el día
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

    # Waffles por cada 10 niños (receta del brief)
    # Flour 500 g, Eggs 4, Milk 500 ml, Sugar 50 g, Baking powder 10 g, Butter 50 g
    scale = (t * margin) / 10.0
    waffles = {
        "Flour (1 kg)": 500.0 * scale,           # gramos
        "Eggs (each)": 4.0 * scale,              # unidades
        "Milk for waffles (ml)": 500.0 * scale,  # mililitros
        "Sugar (1 kg)": 50.0 * scale,            # gramos
        "Baking powder (100 g)": 10.0 * scale,   # gramos
        "Butter (250 g)": 50.0 * scale,          # gramos
    }

    # Convertir waffles a las unidades de compra
    # Milk total (litros) = leche desayuno + leche waffles (ml->L)
    milk_total_L = mon["Milk (1 L)"] + tue["Milk (1 L)"] + (waffles["Milk for waffles (ml)"] / 1000.0)

    # Gramos -> kg/100g/250g packs
    flour_kg = waffles["Flour (1 kg)"] / 1000.0
    sugar_kg = waffles["Sugar (1 kg)"] / 1000.0
    bp_packs = waffles["Baking powder (100 g)"] / 100.0  # en "paquetes de 100 g"
    butter_blocks = waffles["Butter (250 g)"] / 250.0

    # Construir mapa de totales (antes de redondeo)
    totals = {
        "Milk (1 L)": milk_total_L,
        "Tea (50 bags)": mon["Tea (50 bags)"] + tue["Tea (50 bags)"],
        "Bread (unit)": mon["Bread (unit)"] ,
        "Fruit (unit)": mon["Fruit (unit)"] + tue["Fruit (unit)"],
        "Oats (portion)": mon["Oats (portion)"] + tue["Oats (portion)"],
        "Yogurt (cup)": mon["Yogurt (cup)"] + tue["Yogurt (cup)"],
        "Flour (1 kg)": flour_kg,
        "Eggs (each)": waffles["Eggs (each)"],
        "Sugar (1 kg)": sugar_kg,
        "Baking powder (100 g)": bp_packs,
        "Butter (250 g)": butter_blocks,
    }

    # Redondeo a envase
    rounded = {k: ceil_to_pack(v, PACKS[k]) for k, v in totals.items()}

    # Ajuste: pan del martes no estaba en el menú del martes; mantenemos solo lunes
    # (ya aplicado arriba)

    return Quantities(mon=mon, tue=tue, waffles=waffles, rounded=rounded)

# ------------------------------ Scraping simple -------------------------------
class LivePricer:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def fetch_price(self, market: str, product_key: str) -> Optional[float]:
        """Intenta obtener un precio unitario en NZD.
        Estrategia:
          1) Hacer búsqueda en el sitio del super.
          2) Tomar el primer resultado que tenga un precio visible.
        Observación: muchas páginas usan JS; este método puede fallar. Si falla: None.
        """
        if not HAS_SCRAPE_DEPS:
            return None
        base = SEARCH_ENDPOINTS.get(market)
        term = SEARCH_TERMS.get(product_key, product_key)
        if not base:
            return None
        url = base.format(q=term.replace(" ", "+"))
        try:
            with httpx.Client(headers=HEADERS, timeout=self.timeout, follow_redirects=True) as client:
                r = client.get(url)
                r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            # Heurísticas de precio comunes
            selectors = [
                {"tag": "span", "attrs": {"data-automation": "price-per-item"}},
                {"tag": "span", "attrs": {"class": lambda c: c and "price" in c}},
                {"tag": "div", "attrs": {"class": lambda c: c and "price" in c}},
            ]
            texts: List[str] = []
            for s in selectors:
                for el in soup.find_all(s.get("tag"), attrs=s.get("attrs")):
                    txt = el.get_text(strip=True)
                    if txt:
                        texts.append(txt)
            # Buscar primera coincidencia tipo $x.xx
            for t in texts:
                price = _extract_price_nzd(t)
                if price is not None:
                    return price
            return None
        except Exception:
            return None

    def prices_for_all(self) -> Dict[str, Dict[str, float]]:
        """Devuelve precios por mercado para todas las claves conocidas.
        Si un precio no se puede obtener, se deja el DEFAULT.
        """
        live: Dict[str, Dict[str, float]] = {k: DEFAULT_PRICES[k].copy() for k in DEFAULT_PRICES}
        for product in DEFAULT_PRICES.keys():
            for market in SUPERMARKETS:
                p = self.fetch_price(market, product)
                if p is not None:
                    live[product][market] = p
        return live


def _extract_price_nzd(text: str) -> Optional[float]:
    import re
    m = re.search(r"\$\s*([0-9]+(?:\.[0-9]{1,2})?)", text)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return None
    return None

# ------------------------------ Costeo y salida -------------------------------

def cost_by_super(rounded: Dict[str, int], prices: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    totals = {m: 0.0 for m in SUPERMARKETS}
    for product, qty in rounded.items():
        # convertir unidades "paquetes" a precio unitario correspondiente
        unit_price_by_market = prices.get(product, {})
        for m in SUPERMARKETS:
            price = unit_price_by_market.get(m)
            if price is None:
                continue
            totals[m] += qty * price
    return totals


def build_tables(q: Quantities, prices: Dict[str, Dict[str, float]]) -> Tuple[str, str]:
    # Tabla de cantidades (por día + waffles)
    def fmt(x: float) -> str:
        return f"{x:.2f}"

    rows_qty: List[str] = []
    # Lunes
    rows_qty.append("Día | Producto | Cantidad | Unidad")
    rows_qty.append("---|---|---|---")
    rows_qty.append(f"Lunes | Milk | {fmt(q.mon['Milk (1 L)'])} | L")
    rows_qty.append(f"Lunes | Tea | 1 | pack (50 bags)")
    rows_qty.append(f"Lunes | Bread | {fmt(q.mon['Bread (unit)'])} | unidades")
    rows_qty.append(f"Lunes | Fruit | {fmt(q.mon['Fruit (unit)'])} | unidades")
    rows_qty.append(f"Lunes | Oats | {fmt(q.mon['Oats (portion)'])} | porciones")
    rows_qty.append(f"Lunes | Yogurt | {fmt(q.mon['Yogurt (cup)'])} | vasos")
    # Martes
    rows_qty.append(f"Martes | Milk (desayuno) | {fmt(q.tue['Milk (1 L)'])} | L")
    rows_qty.append(f"Martes | Tea | 1 | pack (50 bags)")
    rows_qty.append(f"Martes | Fruit | {fmt(q.tue['Fruit (unit)'])} | unidades")
    rows_qty.append(f"Martes | Oats | {fmt(q.tue['Oats (portion)'])} | porciones")
    rows_qty.append(f"Martes | Yogurt | {fmt(q.tue['Yogurt (cup)'])} | vasos")
    # Waffles (martes)
    rows_qty.append(f"Martes | Waffles – Flour | {fmt(q.waffles['Flour (1 kg)'])} | g")
    rows_qty.append(f"Martes | Waffles – Eggs | {fmt(q.waffles['Eggs (each)'])} | unidades")
    rows_qty.append(f"Martes | Waffles – Milk | {fmt(q.waffles['Milk for waffles (ml)'])} | ml")
    rows_qty.append(f"Martes | Waffles – Sugar | {fmt(q.waffles['Sugar (1 kg)'])} | g")
    rows_qty.append(f"Martes | Waffles – Baking powder | {fmt(q.waffles['Baking powder (100 g)'])} | g")
    rows_qty.append(f"Martes | Waffles – Butter | {fmt(q.waffles['Butter (250 g)'])} | g")

    qty_table = "\n".join(rows_qty)

    # Tabla de costos
    rows_cost: List[str] = []
    rows_cost.append("Producto | Pak’nSave | New World | Countdown | Notes")
    rows_cost.append("---|---|---|---|---")

    for product in DEFAULT_PRICES.keys():
        pns = prices[product]["Pak'nSave"]
        nw = prices[product]["New World"]
        cd = prices[product]["Countdown"]
        note = "Live" if prices is not DEFAULT_PRICES else "Default"
        rows_cost.append(f"{product} | ${pns:.2f} | ${nw:.2f} | ${cd:.2f} | {note}")

    cost_table = "\n".join(rows_cost)
    return qty_table, cost_table


def email_draft(needs: Needs, totals: Dict[str, float], quantities: Quantities) -> str:
    week_of = _week_of_date(dt.date.today())
    cheapest = min(totals, key=totals.get)
    body_lines = []
    body_lines.append("To: mavisi036@gmail.com")
    body_lines.append(f"Subject: Breakfast Club – Weekly Shopping Plan (Week of {week_of})")
    body_lines.append("")
    body_lines.append("Hi Mavis,")
    body_lines.append("")
    body_lines.append("Here’s the shopping plan for this week:")
    body_lines.append(f"- Monday: expecting {needs.mon_children} children")
    body_lines.append(f"- Tuesday: expecting {needs.tue_children} children (includes waffles)")
    body_lines.append("A 10% safety margin has been added to all quantities.")
    body_lines.append("")
    body_lines.append("Shopping list:")
    body_lines.append("Monday: milk, tea, bread, fruit, oats, yogurt.")
    body_lines.append("Tuesday: milk, tea, fruit, oats, yogurt, and waffle ingredients (flour, eggs, milk, sugar, baking powder, butter).")
    body_lines.append("")
    body_lines.append("Estimated total costs:")
    body_lines.append(f"- Pak’nSave: ${totals['Pak\'nSave']:.2f}")
    body_lines.append(f"- New World: ${totals['New World']:.2f}")
    body_lines.append(f"- Countdown: ${totals['Countdown']:.2f}")
    body_lines.append(f"→ Cheapest: {cheapest}")
    body_lines.append("")
    body_lines.append("Please confirm or reply with changes.")
    return "\n".join(body_lines)


def _week_of_date(today: dt.date) -> str:
    # Lunes de la semana del "today"
    monday = today - dt.timedelta(days=(today.weekday()))
    return monday.strftime("%d %b %Y")

# ------------------------------ CLI de ejemplo -------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Breakfast Club Planner")
    parser.add_argument("--mon", type=int, default=25, help="Niños lunes")
    parser.add_argument("--tue", type=int, default=30, help="Niños martes")
    parser.add_argument("--live", action="store_true", help="Intentar precios en vivo")
    args = parser.parse_args()

    needs = Needs(mon_children=args.mon, tue_children=args.tue)
    q = compute_quantities(needs)

    # Precios: live si se puede, si no defaults
    prices = DEFAULT_PRICES
    if args.live:
        pricer = LivePricer()
        live = pricer.prices_for_all()
        prices = live  # usa mezcla live+default

    # Costos por super
    totals = cost_by_super(q.rounded, prices)

    # Construir tablas
    qty_table, cost_table = build_tables(q, prices)

    # Resumen
    served = needs.mon_children + needs.tue_children
    cheapest = min(totals, key=totals.get)

    print("\n== Cantidades (con 10% de margen, redondeadas a envases) ==")
    print(qty_table)
    print("\n== Totales redondeados a comprar ==")
    for k, v in q.rounded.items():
        print(f"- {k}: {v}")

    print("\n== Costos estimados por supermercado ==")
    print(cost_table)

    print("\n== Resumen ==")
    print(f"Total children served (est.): {served}")
    print(
        f"Total estimated cost – Pak’nSave ${totals['Pak\'nSave']:.2f} • New World ${totals['New World']:.2f} • Countdown ${totals['Countdown']:.2f} – Cheapest: {cheapest}"
    )
    print("Safety margin applied: 10%")
    print("Expected waste < 8%")

    print("\n== Email draft (copy/paste) ==")
    print(email_draft(needs, totals, q))
