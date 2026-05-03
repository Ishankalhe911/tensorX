"""
Fusion Model: Combines all signals into final credit report
"""
from typing import Dict, List
import math

class FusionModel:
    def __init__(self):
        # Signal weights (must sum to 1.0)
        self.weights = {
            "visual":       0.35,
            "geo":          0.30,
            "shoplive":     0.25,
            "opknowledge":  0.10,
        }
        
        # Base daily revenue for a kirana store
        self.BASE_DAILY = 4000  # ₹4000 baseline
        self.MAX_DAILY   = 18000 # ₹18000 cap for prototype
        
        # Typical net margin for kirana stores
        self.NET_MARGIN = 0.18   # 18%

    # ─── Main entry point ────────────────────────────────────────────────────

    def compute(
        self,
        visual_result:   Dict,
        geo_result:      Dict,
        shoplive_result: Dict,
        opknow_result:   Dict,
    ) -> Dict:
        """
        Combine four signals and return full credit report JSON.
        """

        # ── 1. Collect revenue contributions ─────────────────────────────────
        visual_contrib   = visual_result.get("visual_revenue_contribution",   2000)
        geo_contrib      = geo_result.get("geo_revenue_contribution",          1500)
        shoplive_contrib = shoplive_result.get("shoplive_revenue_contribution", 1000)
        opknow_contrib   = opknow_result.get("opknowledge_contribution",        500)

        raw_daily = (
            self.BASE_DAILY
            + visual_contrib   * self.weights["visual"]
            + geo_contrib      * self.weights["geo"]
            + shoplive_contrib * self.weights["shoplive"]
            + opknow_contrib   * self.weights["opknowledge"]
        )

        daily_estimate = max(1000, min(int(raw_daily), self.MAX_DAILY))

        # ── 2. Revenue ranges (±15 %) ─────────────────────────────────────────
        daily_min  = int(daily_estimate * 0.85)
        daily_max  = int(daily_estimate * 1.15)
        monthly_min = daily_min  * 30
        monthly_max = daily_max  * 30
        income_min  = int(monthly_min * self.NET_MARGIN)
        income_max  = int(monthly_max * self.NET_MARGIN)

        # ── 3. Confidence score ───────────────────────────────────────────────
        visual_conf   = visual_result.get("signal_confidence",   0.75)
        geo_conf      = geo_result.get("signal_confidence",      0.85)
        shoplive_conf = shoplive_result.get("signal_confidence", 0.90)
        opknow_conf   = opknow_result.get("confidence_score",    0.70)

        raw_confidence = (
            visual_conf   * self.weights["visual"]
            + geo_conf    * self.weights["geo"]
            + shoplive_conf * self.weights["shoplive"]
            + opknow_conf * self.weights["opknowledge"]
        )
        confidence_score = round(min(raw_confidence, 0.97), 2)

        # ── 4. Risk flags ─────────────────────────────────────────────────────
        risk_flags = self._compute_risk_flags(
            visual_result, geo_result, shoplive_result, opknow_result
        )

        # ── 5. Recommendation ─────────────────────────────────────────────────
        recommendation = self._compute_recommendation(
            confidence_score, risk_flags, shoplive_result
        )

        # ── 6. Peer benchmark ─────────────────────────────────────────────────
        peer_benchmark = self._compute_peer_benchmark(
            daily_estimate,
            geo_result.get("road_type", "unknown"),
            geo_result.get("competition_density", "unknown")
        )

        # ── 7. Signal summary for frontend ───────────────────────────────────
        signal_summary = {
            "visual": {
                "score": visual_result.get("sku_diversity_score", 0),
                "shelf_density": visual_result.get("shelf_density_score", 0),
                "refill_signal": visual_result.get("refill_signal", "unknown"),
                "objects_detected": len(visual_result.get("detected_objects", [])),
            },
            "geo": {
                "score": geo_result.get("footfall_score", 0),
                "poi_count": geo_result.get("poi_count", 0),
                "competitor_count": geo_result.get("competitor_count", 0),
                "road_type": geo_result.get("road_type", "unknown"),
            },
            "shoplive": {
                "zones_completed": shoplive_result.get("zones_completed", 0),
                "all_zones_passed": shoplive_result.get("all_zones_passed", False),
                "gps_consistent": shoplive_result.get("gps_consistent", False),
                "time_compliant": shoplive_result.get("time_compliant", False),
            },
            "operational_knowledge": {
                "test_passed": opknow_result.get("test_passed", False),
                "price_mentioned": opknow_result.get("price_mentioned", False),
                "response_time_ok": opknow_result.get("response_time_acceptable", False),
            }
        }

        return {
            "daily_sales_range":      [daily_min, daily_max],
            "monthly_revenue_range":  [monthly_min, monthly_max],
            "monthly_income_range":   [income_min, income_max],
            "confidence_score":        confidence_score,
            "risk_flags":              risk_flags,
            "recommendation":          recommendation,
            "peer_benchmark":          peer_benchmark,
            "signal_summary":          signal_summary,
        }

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _compute_risk_flags(self, visual, geo, shoplive, opknow) -> List[str]:
        flags = []

        # Visual vs Geo mismatch
        visual_score = visual.get("sku_diversity_score", 0.5)
        geo_score    = geo.get("footfall_score", 0.5)
        if abs(visual_score - geo_score) > 0.5:
            flags.append("inventory_footfall_mismatch")

        # Overstocked shelf (possible staged inventory)
        if visual.get("refill_signal") == "overstocked":
            flags.append("possible_staged_inventory")

        # ShopLive failures
        if not shoplive.get("gps_consistent", True):
            flags.append("gps_location_inconsistency")
        if not shoplive.get("time_compliant", True):
            flags.append("shoplive_time_exceeded")
        if not shoplive.get("all_zones_passed", True):
            flags.append("incomplete_shoplive_challenge")

        # Operational knowledge failure
        if opknow_flag := opknow.get("risk_flag"):
            flags.append(opknow_flag)

        # Employee count vs footfall mismatch
        emp = shoplive.get("employee_count", 1)
        geo_low = geo.get("footfall_score", 0.5) < 0.3
        if emp >= 3 and geo_low:
            flags.append("high_employee_count_low_footfall")

        return flags

    def _compute_recommendation(
        self, confidence: float, flags: List[str], shoplive: Dict
    ) -> str:
        critical_flags = {
            "gps_location_inconsistency",
            "incomplete_shoplive_challenge",
            "failed_operational_knowledge_test",
            "no_operational_knowledge_response",
        }

        has_critical = bool(set(flags) & critical_flags)
        shoplive_passed = shoplive.get("all_zones_passed", False)

        if has_critical or not shoplive_passed:
            return "reject"
        if confidence >= 0.75 and len(flags) == 0:
            return "pre_approved"
        if confidence >= 0.55:
            return "needs_verification"
        return "reject"

    def _compute_peer_benchmark(
        self, daily_estimate: int, road_type: str, competition: str
    ) -> Dict:
        # Peer ranges by road type
        peer_ranges = {
            "arterial_road":  {"low": 7000,  "median": 10000, "high": 15000},
            "main_road":      {"low": 4500,  "median": 7000,  "high": 10000},
            "internal_lane":  {"low": 2500,  "median": 4500,  "high": 7000},
            "unknown":        {"low": 3500,  "median": 6000,  "high": 9000},
        }

        peers = peer_ranges.get(road_type, peer_ranges["unknown"])
        median = peers["median"]

        pct_diff = ((daily_estimate - median) / median) * 100

        if pct_diff > 15:
            position = "above_peer_median"
        elif pct_diff < -15:
            position = "below_peer_median"
        else:
            position = "at_peer_median"

        return {
            "road_type_category": road_type,
            "peer_median_daily": median,
            "peer_range": [peers["low"], peers["high"]],
            "your_estimate": daily_estimate,
            "position": position,
            "percentile_approx": max(5, min(95, int(50 + pct_diff))),
        }