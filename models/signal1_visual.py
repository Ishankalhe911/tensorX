"""
Signal 1: Visual Intelligence
Uses YOLOv8 to detect objects and derive inventory signals
"""
from ultralytics import YOLO
from PIL import Image
import io
from typing import Dict, List
import numpy as np

class VisualIntelligence:
    def __init__(self):
        """Initialize YOLOv8 Nano model (fastest, smallest)"""
        try:
            # Download model on first run (cached afterward)
            self.model = YOLO('yolov8n.pt')
            print("YOLOv8 Nano loaded successfully")
        except Exception as e:
            print(f"YOLO load error: {e}")
            self.model = None
    
    def analyze(self, image_bytes: bytes) -> Dict:
        """
        Analyze shop image and extract visual signals
        
        Returns:
            {
                "detected_objects": List[str],
                "sku_diversity_score": float,      # 0-1
                "shelf_density_score": float,      # 0-1
                "inventory_value_estimate": int,   # ₹
                "refill_signal": str,              # "recent_sales" | "overstocked" | "normal"
                "upi_sticker_detected": bool,
                "visual_revenue_contribution": int # ₹
            }
        """
        if not self.model:
            return self._fallback_analysis(image_bytes)
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Run YOLO detection
            results = self.model(image, verbose=False)
            
            # Extract detected classes
            detected_classes = []
            if len(results) > 0 and results[0].boxes is not None:
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    detected_classes.append(class_name)
            
            # Remove duplicates
            unique_objects = list(set(detected_classes))
            
            # SKU Diversity Score
            # More unique object types = higher diversity
            # COCO has 80 classes, but shops typically have 5-15 visible categories
            sku_diversity_score = min(len(unique_objects) / 12, 1.0)
            
            # Shelf Density Score (proxy from detection count)
            # More objects detected = fuller shelves
            total_detections = len(detected_classes)
            shelf_density_score = min(total_detections / 30, 1.0)  # Cap at 30 objects
            
            # Inventory Value Estimate
            # Map detected objects to rough price categories
            inventory_estimate = self._estimate_inventory_value(unique_objects)
            
            # Refill Signal
            # If density is low but diversity is high = recent sales (partially empty)
            # If density is very high = potentially overstocked
            if shelf_density_score < 0.5 and sku_diversity_score > 0.6:
                refill_signal = "recent_sales"  # Good sign
            elif shelf_density_score > 0.85:
                refill_signal = "overstocked"   # Flag: might be staged
            else:
                refill_signal = "normal"
            
            # UPI Sticker Detection (basic text/QR code proxy)
            # Check if 'cell phone' or similar objects detected (proxy for UPI sticker)
            upi_indicators = ['cell phone', 'laptop', 'keyboard']
            upi_sticker_detected = any(obj in unique_objects for obj in upi_indicators)
            
            # Revenue Contribution
            visual_revenue_contribution = int(
                (sku_diversity_score * 2000) +  # Diversity adds ₹2000 max
                (shelf_density_score * 2500) +  # Density adds ₹2500 max
                (500 if refill_signal == "recent_sales" else 0)  # Bonus for healthy turnover
            )
            
            return {
                "detected_objects": unique_objects[:10],  # Limit to top 10 for readability
                "sku_diversity_score": round(sku_diversity_score, 2),
                "shelf_density_score": round(shelf_density_score, 2),
                "inventory_value_estimate": inventory_estimate,
                "refill_signal": refill_signal,
                "upi_sticker_detected": upi_sticker_detected,
                "visual_revenue_contribution": visual_revenue_contribution,
                "signal_confidence": 0.75
            }
            
        except Exception as e:
            print(f"Visual Intelligence Error: {e}")
            return self._fallback_analysis(image_bytes)
    
    def _estimate_inventory_value(self, detected_objects: List[str]) -> int:
        """
        Rough inventory value mapping based on detected object types
        """
        # Simple heuristic: more categories = more working capital deployed
        category_count = len(detected_objects)
        
        if category_count >= 10:
            return 35000  # High diversity = ₹25k-₹40k inventory
        elif category_count >= 7:
            return 22000  # Medium diversity = ₹15k-₹25k
        elif category_count >= 4:
            return 12000  # Low diversity = ₹8k-₹15k
        else:
            return 6000   # Very low = ₹5k-₹8k
    
    def _fallback_analysis(self, image_bytes: bytes) -> Dict:
        """
        Fallback if YOLO fails - use image properties as proxy
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Use image brightness as shelf density proxy
            grayscale = image.convert('L')
            pixels = np.array(grayscale)
            avg_brightness = pixels.mean() / 255.0
            
            # Brighter images often mean well-lit, full shops
            shelf_density_score = min(avg_brightness * 1.2, 1.0)
            
            return {
                "detected_objects": [],
                "sku_diversity_score": 0.6,  # Assume medium
                "shelf_density_score": round(shelf_density_score, 2),
                "inventory_value_estimate": 15000,
                "refill_signal": "normal",
                "upi_sticker_detected": False,
                "visual_revenue_contribution": 2500,
                "signal_confidence": 0.4,  # Low confidence fallback
                "fallback_mode": True
            }
        except:
            # Ultimate fallback
            return {
                "detected_objects": [],
                "sku_diversity_score": 0.5,
                "shelf_density_score": 0.5,
                "inventory_value_estimate": 12000,
                "refill_signal": "normal",
                "upi_sticker_detected": False,
                "visual_revenue_contribution": 2000,
                "signal_confidence": 0.3,
                "error": "Fallback mode active"
            }


# Quick test
if __name__ == "__main__":
    # Test with a sample image (you'd need to provide one)
    print("Visual Intelligence module loaded. Provide image bytes to test.")