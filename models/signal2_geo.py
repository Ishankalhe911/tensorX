"""
Signal 2: Geo Intelligence
Uses Google Places API to derive footfall and competition signals
"""
import googlemaps
from typing import Dict, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

class GeoIntelligence:
    def __init__(self):
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in environment")
        self.gmaps = googlemaps.Client(key=api_key)
    
    def analyze(self, lat: float, lng: float) -> Dict:
        """
        Analyze location and return geo intelligence signals
        
        Returns:
            {
                "poi_count": int,           # Points of interest nearby
                "competitor_count": int,     # Similar stores nearby
                "footfall_score": float,     # 0-1 normalized score
                "competition_density": str,  # "low" | "medium" | "high"
                "road_type": str,           # Inferred from POI density
                "geo_revenue_contribution": int  # ₹ contribution to daily sales
            }
        """
        try:
            # POI Search - schools, offices, transit (500m radius)
            pois = self.gmaps.places_nearby(
                location=(lat, lng),
                radius=500,
                type='school|university|office|transit_station|bus_station|subway_station'
            )
            poi_count = len(pois.get('results', []))
            
            # Competition Search (300m radius)
            competitors = self.gmaps.places_nearby(
                location=(lat, lng),
                radius=300,
                keyword='kirana|grocery|general store|convenience store'
            )
            competitor_count = len(competitors.get('results', []))
            
            # Footfall Score (normalized 0-1)
            # More POIs = higher footfall
            footfall_score = min(poi_count / 15, 1.0)  # Cap at 15 POIs = max score
            
            # Competition Density Classification
            if competitor_count <= 2:
                competition_density = "low"
                competition_penalty = 0
            elif competitor_count <= 5:
                competition_density = "medium"
                competition_penalty = 500
            else:
                competition_density = "high"
                competition_penalty = 1000
            
            # Road Type Inference
            # High POI count = likely arterial road
            if poi_count >= 10:
                road_type = "arterial_road"
            elif poi_count >= 5:
                road_type = "main_road"
            else:
                road_type = "internal_lane"
            
            # Revenue Contribution Calculation
            # Base geo contribution: footfall adds revenue, competition reduces it
            base_contribution = footfall_score * 3500  # Max ₹3500 from footfall
            geo_revenue_contribution = int(base_contribution - competition_penalty)
            
            return {
                "poi_count": poi_count,
                "competitor_count": competitor_count,
                "footfall_score": round(footfall_score, 2),
                "competition_density": competition_density,
                "road_type": road_type,
                "geo_revenue_contribution": geo_revenue_contribution,
                "signal_confidence": 0.85  # Geo data is highly reliable
            }
            
        except Exception as e:
            print(f"Geo Intelligence Error: {e}")
            # Return degraded signal on error
            return {
                "poi_count": 0,
                "competitor_count": 0,
                "footfall_score": 0.5,  # Assume medium
                "competition_density": "unknown",
                "road_type": "unknown",
                "geo_revenue_contribution": 1500,  # Conservative estimate
                "signal_confidence": 0.3,  # Low confidence
                "error": str(e)
            }


# Quick test
if __name__ == "__main__":
    geo = GeoIntelligence()
    
    # Test location: MG Road, Pune (high footfall commercial area)
    result = geo.analyze(18.5204, 73.8567)
    
    print("Geo Intelligence Test:")
    print(f"POI Count: {result['poi_count']}")
    print(f"Competitors: {result['competitor_count']}")
    print(f"Footfall Score: {result['footfall_score']}")
    print(f"Road Type: {result['road_type']}")
    print(f"Revenue Contribution: ₹{result['geo_revenue_contribution']}")