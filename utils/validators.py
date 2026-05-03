"""
Utilities: GPS validation, timestamp checks, ShopLive protocol logic
"""
import math
import time
import random
from typing import Dict, List, Tuple

# All possible ShopLive zones
ALL_ZONES = [
    "left_shelf",
    "right_shelf",
    "counter",
    "entrance",
    "storage_area",
    "street_view",
    "ceiling_shot",
    "billing_area",
]

ZONE_LABELS = {
    "left_shelf":    "📦 Left Shelf",
    "right_shelf":   "📦 Right Shelf",
    "counter":       "🪙 Counter Area",
    "entrance":      "🚪 Shop Entrance",
    "storage_area":  "🗄️ Storage Area",
    "street_view":   "🛣️ Street View",
    "ceiling_shot":  "📐 Ceiling / Shop Size",
    "billing_area":  "🧾 Billing Area",
}

TIME_LIMIT_SECONDS = 480   # 8 minutes per zone
GPS_TOLERANCE_M    = 100   # 100 metre tolerance


# ─── Distance helper ────────────────────────────────────────────────────────

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in metres between two GPS coordinates."""
    R = 6371000  # Earth radius in metres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── ShopLive session generator ──────────────────────────────────────────────

def generate_shoplive_challenge() -> Dict:
    """
    Generate a randomised 4-zone ShopLive challenge.
    Returns the zone list + per-zone time limits.
    """
    selected = random.sample(ALL_ZONES, 4)
    zones = [
        {
            "zone_id":     zone,
            "label":       ZONE_LABELS[zone],
            "time_limit":  TIME_LIMIT_SECONDS,
            "instructions": _zone_instructions(zone),
        }
        for zone in selected
    ]
    return {
        "challenge_id":  f"SL-{int(time.time())}",
        "zones":          zones,
        "total_zones":    4,
        "generated_at":   int(time.time()),
        "expires_at":     int(time.time()) + (TIME_LIMIT_SECONDS * 5),
    }


def _zone_instructions(zone_id: str) -> str:
    instructions = {
        "left_shelf":   "Stand in the centre of your shop and photograph the LEFT side shelves completely.",
        "right_shelf":  "Stand in the centre of your shop and photograph the RIGHT side shelves completely.",
        "counter":      "Photograph your main billing counter including any UPI/QR stickers visible.",
        "entrance":     "Step back and photograph the full shop entrance from inside looking out.",
        "storage_area": "Photograph your storage or back-room area.",
        "street_view":  "Step outside and photograph the street facing your shop entrance.",
        "ceiling_shot": "Point camera upward to capture the ceiling and give a sense of shop size.",
        "billing_area": "Photograph your billing setup — cash drawer, phone, POS machine, receipt book.",
    }
    return instructions.get(zone_id, "Photograph this area of your shop clearly.")


# ─── ShopLive result validator ───────────────────────────────────────────────

def validate_shoplive(
    declared_lat:    float,
    declared_lng:    float,
    photo_metadata:  List[Dict],   # [{lat, lng, timestamp, zone_id}, ...]
    employee_count:  int = 0,
) -> Dict:
    """
    Validate a completed ShopLive challenge submission.

    photo_metadata items:
        lat, lng      – GPS at time of capture
        timestamp     – Unix epoch
        zone_id       – Which zone this photo belongs to
    """
    if not photo_metadata:
        return {
            "all_zones_passed":  False,
            "gps_consistent":    False,
            "time_compliant":    False,
            "zones_completed":   0,
            "employee_count":    employee_count,
            "shoplive_revenue_contribution": 0,
            "signal_confidence": 0.0,
            "risk_flags":        ["no_photos_submitted"],
        }

    # GPS consistency check
    gps_issues = []
    for meta in photo_metadata:
        dist = haversine_distance(
            declared_lat, declared_lng,
            meta.get("lat", declared_lat),
            meta.get("lng", declared_lng)
        )
        if dist > GPS_TOLERANCE_M:
            gps_issues.append({
                "zone":     meta.get("zone_id"),
                "distance": round(dist, 1),
            })
    gps_consistent = len(gps_issues) == 0

    # Timestamp check (all photos within 15 minutes of first photo)
    timestamps = [m.get("timestamp", 0) for m in photo_metadata if m.get("timestamp")]
    if len(timestamps) >= 2:
        total_span = max(timestamps) - min(timestamps)
        time_compliant = total_span <= (TIME_LIMIT_SECONDS * 4 + 120)  # 4 zones + 2 min buffer
    else:
        time_compliant = True  # Can't check with fewer than 2 timestamps

    # Zones completed
    zones_completed = len(photo_metadata)
    all_zones_passed = zones_completed >= 4

    # Revenue contribution (reward genuine compliance)
    if all_zones_passed and gps_consistent and time_compliant:
        shoplive_revenue_contribution = 3000
        signal_confidence = 0.92
    elif all_zones_passed and (gps_consistent or time_compliant):
        shoplive_revenue_contribution = 1800
        signal_confidence = 0.70
    else:
        shoplive_revenue_contribution = 500
        signal_confidence = 0.40

    # Employee signal
    employee_tier = _employee_tier(employee_count)

    return {
        "all_zones_passed":                all_zones_passed,
        "gps_consistent":                  gps_consistent,
        "time_compliant":                  time_compliant,
        "zones_completed":                 zones_completed,
        "gps_issues":                      gps_issues,
        "employee_count":                  employee_count,
        "employee_revenue_tier":           employee_tier,
        "shoplive_revenue_contribution":   shoplive_revenue_contribution,
        "signal_confidence":               signal_confidence,
    }


def _employee_tier(count: int) -> str:
    if count == 0:
        return "solo_operator"
    elif count == 1:
        return "small_team"
    elif count <= 3:
        return "medium_team"
    else:
        return "large_team"