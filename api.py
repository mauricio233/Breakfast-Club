"""
# api.py
from fastapi import FastAPI
from planner import Needs, compute_quantities, cost_by_super, DEFAULT_PRICES

app = FastAPI(title="Breakfast Club Planner API")

@app.get("/")
def home():
    """Ruta de prueba para Render"""
    return {"status": "ok", "message": "Breakfast Club Planner API is live."}

@app.get("/jit_plugin/plan")
def plan(mon: int = 25, tue: int = 30, live: bool = False):
    """Calcula costos y supermercado más barato"""
    needs = Needs(mon_children=mon, tue_children=tue)
    q = compute_quantities(needs)
    prices = DEFAULT_PRICES
    totals = cost_by_super(q.rounded, prices)
    cheapest = min(totals, key=totals.get)
    return {
        "totals": totals,
        "cheapest": cheapest,
        "email": "mavisi036@gmail.com"
    }

    
