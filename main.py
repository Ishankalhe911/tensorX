"""
KhataSync Backend — FastAPI Application
Main entry point with all API routes
"""
import os
import time
import json
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from models.signal1_visual import VisualIntelligence
from models.signal2_geo import GeoIntelligence
from models.signal4_opknow import OperationalKnowledge
from models.fusion import FusionModel
from utils.validators import generate_shoplive_challenge, validate_shoplive

load_dotenv()

app = FastAPI(
    title="KhataSync API",
    description="Remote kirana store cash flow underwriting engine",
    version="1.0.0"
)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── CORS (allow frontend dev server) ────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Module initialisation ────────────────────────────────────────────────────

print("Loading KhataSync modules...")
visual_engine    = VisualIntelligence()
fusion_engine    = FusionModel()
opknow_engine    = OperationalKnowledge()

# Geo engine initialised lazily (needs API key)
geo_engine = None
def get_geo_engine():
    global geo_engine
    if geo_engine is None:
        try:
            geo_engine = GeoIntelligence()
        except ValueError as e:
            print(f"Geo engine init failed: {e}")
    return geo_engine

print("KhataSync ready.")


# ─── Pydantic models ──────────────────────────────────────────────────────────

class PhotoMeta(BaseModel):
    lat:       float
    lng:       float
    timestamp: int
    zone_id:   str

class AnalyzeRequest(BaseModel):
    lat:             float
    lng:             float
    employee_count:  int           = 0
    photo_metadata:  List[PhotoMeta] = []
    audio_transcript: Optional[str] = None
    video_duration:  float         = 0.0


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Quick liveness check for the frontend."""
    return {
        "status":     "ok",
        "service":    "KhataSync API",
        "version":    "1.0.0",
        "timestamp":  int(time.time()),
        "modules": {
            "visual":   visual_engine.model is not None,
            "geo":      get_geo_engine() is not None,
            "opknow":   True,
            "fusion":   True,
        }
    }

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serves the mobile web app UI"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Error: Frontend not found!</h1><p>Make sure index.html is inside the 'static' folder.</p>"
@app.get("/api/challenge")
def get_challenge():
    """
    Generate a fresh randomised ShopLive challenge.
    Frontend calls this when the shopkeeper starts the assessment.
    """
    challenge = generate_shoplive_challenge()
    return {"success": True, "challenge": challenge}


@app.post("/api/analyze")
async def analyze_images(
    images: List[UploadFile] = File(...),
    lat:    float = Form(...),
    lng:    float = Form(...),
    employee_count: int = Form(0),
    photo_metadata_json: str = Form("[]"),
    audio_transcript: Optional[str] = Form(None),
    video_duration:   float = Form(0.0),
):
    """
    Full analysis endpoint.
    Accepts images + form data, runs all 4 signals, returns credit report.
    """
    start_time = time.time()

    # ── Parse photo metadata ──────────────────────────────────────────────────
    try:
        raw_meta = json.loads(photo_metadata_json)
        photo_metadata = [PhotoMeta(**m) for m in raw_meta]
    except Exception:
        photo_metadata = []

    # ── Signal 1: Visual (process first uploaded image) ───────────────────────
    visual_result = {}
    if images:
        try:
            image_bytes = await images[0].read()
            visual_result = visual_engine.analyze(image_bytes)
        except Exception as e:
            visual_result = {
                "sku_diversity_score":      0.5,
                "shelf_density_score":      0.5,
                "inventory_value_estimate": 12000,
                "refill_signal":            "normal",
                "upi_sticker_detected":     False,
                "visual_revenue_contribution": 2000,
                "signal_confidence":        0.4,
                "error":                    str(e),
            }
    else:
        visual_result = {
            "sku_diversity_score":      0.5,
            "shelf_density_score":      0.5,
            "inventory_value_estimate": 12000,
            "refill_signal":            "normal",
            "upi_sticker_detected":     False,
            "visual_revenue_contribution": 2000,
            "signal_confidence":        0.4,
        }

    # ── Signal 2: Geo ─────────────────────────────────────────────────────────
    geo = get_geo_engine()
    if geo:
        geo_result = geo.analyze(lat, lng)
    else:
        # Fallback when API key not set
        geo_result = {
            "poi_count":                 5,
            "competitor_count":          2,
            "footfall_score":            0.5,
            "competition_density":       "medium",
            "road_type":                 "main_road",
            "geo_revenue_contribution":  1500,
            "signal_confidence":         0.5,
            "error":                     "Geo engine unavailable",
        }

    # ── Signal 3: ShopLive validation ─────────────────────────────────────────
    meta_dicts = [m.dict() for m in photo_metadata]
    shoplive_result = validate_shoplive(
        declared_lat=lat,
        declared_lng=lng,
        photo_metadata=meta_dicts,
        employee_count=employee_count,
    )

    # ── Signal 4: Operational Knowledge ──────────────────────────────────────
    opknow_result = opknow_engine.analyze(
        audio_transcript=audio_transcript,
        video_duration=video_duration,
    )

    # ── Fusion ────────────────────────────────────────────────────────────────
    credit_report = fusion_engine.compute(
        visual_result=visual_result,
        geo_result=geo_result,
        shoplive_result=shoplive_result,
        opknow_result=opknow_result,
    )

    elapsed = round(time.time() - start_time, 2)

    return {
        "success":             True,
        "processing_time_sec": elapsed,
        "credit_report":       credit_report,
        "raw_signals": {
            "visual":   visual_result,
            "geo":      geo_result,
            "shoplive": shoplive_result,
            "opknow":   opknow_result,
        }
    }


@app.post("/api/analyze/demo")
def analyze_demo(scenario: str = "pass"):
    """
    Demo endpoint — returns realistic pre-computed results.
    Use when live APIs are unavailable or for judge demo.
    scenario: 'pass' | 'verify' | 'fail'
    """
    scenarios = {
        "pass": {
            "credit_report": {
                "daily_sales_range":     [8000, 11000],
                "monthly_revenue_range": [240000, 330000],
                "monthly_income_range":  [43200, 59400],
                "confidence_score":      0.87,
                "risk_flags":            [],
                "recommendation":        "pre_approved",
                "peer_benchmark": {
                    "road_type_category": "arterial_road",
                    "peer_median_daily":   10000,
                    "peer_range":          [7000, 15000],
                    "your_estimate":       9500,
                    "position":            "at_peer_median",
                    "percentile_approx":   52,
                },
                "signal_summary": {
                    "visual":   {"score": 0.82, "shelf_density": 0.78, "refill_signal": "recent_sales", "objects_detected": 9},
                    "geo":      {"score": 0.80, "poi_count": 12, "competitor_count": 2, "road_type": "arterial_road"},
                    "shoplive": {"zones_completed": 4, "all_zones_passed": True, "gps_consistent": True, "time_compliant": True},
                    "operational_knowledge": {"test_passed": True, "price_mentioned": True, "response_time_ok": True},
                }
            }
        },
        "verify": {
            "credit_report": {
                "daily_sales_range":     [5000, 8000],
                "monthly_revenue_range": [150000, 240000],
                "monthly_income_range":  [27000, 43200],
                "confidence_score":      0.63,
                "risk_flags":            ["inventory_footfall_mismatch"],
                "recommendation":        "needs_verification",
                "peer_benchmark": {
                    "road_type_category": "main_road",
                    "peer_median_daily":   7000,
                    "peer_range":          [4500, 10000],
                    "your_estimate":       6500,
                    "position":            "below_peer_median",
                    "percentile_approx":   38,
                },
                "signal_summary": {
                    "visual":   {"score": 0.75, "shelf_density": 0.82, "refill_signal": "overstocked", "objects_detected": 7},
                    "geo":      {"score": 0.42, "poi_count": 6, "competitor_count": 5, "road_type": "main_road"},
                    "shoplive": {"zones_completed": 4, "all_zones_passed": True, "gps_consistent": True, "time_compliant": True},
                    "operational_knowledge": {"test_passed": True, "price_mentioned": True, "response_time_ok": True},
                }
            }
        },
        "fail": {
            "credit_report": {
                "daily_sales_range":     [1500, 3000],
                "monthly_revenue_range": [45000, 90000],
                "monthly_income_range":  [8100, 16200],
                "confidence_score":      0.31,
                "risk_flags":            [
                    "gps_location_inconsistency",
                    "possible_staged_inventory",
                    "failed_operational_knowledge_test",
                ],
                "recommendation":        "reject",
                "peer_benchmark": {
                    "road_type_category": "internal_lane",
                    "peer_median_daily":   4500,
                    "peer_range":          [2500, 7000],
                    "your_estimate":       2200,
                    "position":            "below_peer_median",
                    "percentile_approx":   18,
                },
                "signal_summary": {
                    "visual":   {"score": 0.90, "shelf_density": 0.95, "refill_signal": "overstocked", "objects_detected": 12},
                    "geo":      {"score": 0.15, "poi_count": 2, "competitor_count": 7, "road_type": "internal_lane"},
                    "shoplive": {"zones_completed": 4, "all_zones_passed": False, "gps_consistent": False, "time_compliant": True},
                    "operational_knowledge": {"test_passed": False, "price_mentioned": False, "response_time_ok": False},
                }
            }
        }
    }

    data = scenarios.get(scenario, scenarios["verify"])
    return {"success": True, "demo_mode": True, "scenario": scenario, **data}