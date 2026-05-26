"""
api.py
======
FastAPI backend for ECO-FAST optimization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import threading
import math
from model.solver import run_optimization

app = FastAPI(title="ECO-FAST API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs = {}


class OptimizationRequest(BaseModel):
    Qf: float = 1000.0
    Tann: float = 7920.0
    composition: dict
    objective: str = "Lowest Cost & Emissions Pathway"
    C_elec: float = 0.10
    C_tip: float = 0.08
    C_lbr: float = 30.0
    CRF: float = 0.11
    price_CH4: float = 0.185
    price_BIOCRUDE: float = 0.48
    price_COMPOST: float = 0.068
    price_ELECTRICITY: float = 0.10
    price_BIOSOLIDS: float = 0.05
    n_pareto_pts: int = 10
    time_limit: int = 300
    gap: float = 0.02
    BMP_scen: float = 802.91
    fdeg_CMP: float = 0.50
    C_frac: float = 0.4327
    H_frac: float = 0.0605
    O_frac: float = 0.4289
    N_frac: float = 0.0717
    S_frac: float = 0.0062


def clean_val(val):
    """Replace NaN/Inf with None for JSON serialization."""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def clean_records(records):
    """Clean all values in a list of dicts."""
    return [{k: clean_val(v) for k, v in row.items()} for row in records]


def run_job(job_id: str, user_inputs: dict):
    jobs[job_id]["status"] = "running"
    try:
        result = run_optimization(user_inputs)
        if result["status"] == "success":
            pareto_df = result["pareto_df"]
            records = pareto_df.to_dict(orient="records") if pareto_df is not None else []
            jobs[job_id].update({
                "status":    "complete",
                "message":   result["message"],
                "pareto_df": clean_records(records),
                "NAC_min":   clean_val(result["NAC_min"]),
                "GHG_min":   clean_val(result["GHG_min"]),
            })
        else:
            jobs[job_id].update({
                "status":  "error",
                "message": result["message"],
            })
    except Exception as e:
        jobs[job_id].update({
            "status":  "error",
            "message": str(e),
        })


@app.post("/optimize")
def start_optimization(req: OptimizationRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "message": "Job queued"}
    thread = threading.Thread(
        target=run_job,
        args=(job_id, req.model_dump()),
        daemon=True
    )
    thread.start()
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    if job_id not in jobs:
        return {"status": "not_found", "message": "Job not found"}
    return jobs[job_id]


@app.get("/health")
def health():
    return {"status": "ok"}
