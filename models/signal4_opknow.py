"""
Signal 4: Operational Knowledge Verification
Analyzes video/audio response to product knowledge question
"""
from typing import Dict
import re

class OperationalKnowledge:
    def __init__(self):
        """Initialize operational knowledge analyzer"""
        pass
    
    def analyze(self, audio_transcript: str = None, video_duration: float = 0) -> Dict:
        """
        Analyze operational knowledge test response
        
        For prototype: accepts transcript text (from speech-to-text)
        For production: would integrate Google Cloud Speech-to-Text API
        
        Args:
            audio_transcript: Text transcription of shopkeeper's response
            video_duration: Length of video response in seconds
        
        Returns:
            {
                "test_passed": bool,
                "response_time_acceptable": bool,
                "price_mentioned": bool,
                "confidence_score": float,
                "opknowledge_contribution": int  # Revenue adjustment
            }
        """
        if not audio_transcript:
            # No response provided - fail
            return {
                "test_passed": False,
                "response_time_acceptable": False,
                "price_mentioned": False,
                "confidence_score": 0.0,
                "opknowledge_contribution": -1000,  # Penalty
                "risk_flag": "no_operational_knowledge_response"
            }
        
        # Check response time (should be under 30 seconds)
        response_time_acceptable = video_duration <= 35 if video_duration > 0 else True
        
        # Check if price was mentioned (look for numbers)
        # Common patterns: "40 rupees", "₹40", "40rs", "forty", etc.
        price_patterns = [
            r'\d+\s*(?:rupees|rs|₹)',  # "40 rupees", "40rs", "40₹"
            r'₹\s*\d+',                 # "₹40"
            r'\d+',                     # Any number
        ]
        
        price_mentioned = any(re.search(pattern, audio_transcript.lower()) 
                            for pattern in price_patterns)
        
        # Check for confidence indicators (hesitation words suggest uncertainty)
        hesitation_words = ['um', 'uh', 'maybe', 'i think', 'probably', 'not sure']
        hesitation_count = sum(1 for word in hesitation_words 
                              if word in audio_transcript.lower())
        
        # Test passed if:
        # 1. Price was mentioned
        # 2. Response time was reasonable
        # 3. Low hesitation (confident response)
        test_passed = (
            price_mentioned and 
            response_time_acceptable and 
            hesitation_count <= 2
        )
        
        # Confidence score
        if test_passed:
            confidence_score = 0.9 - (hesitation_count * 0.1)
        else:
            confidence_score = 0.3
        
        # Revenue contribution
        if test_passed:
            opknowledge_contribution = 800  # Bonus for passing
        else:
            opknowledge_contribution = -500  # Penalty for failing
        
        result = {
            "test_passed": test_passed,
            "response_time_acceptable": response_time_acceptable,
            "price_mentioned": price_mentioned,
            "hesitation_detected": hesitation_count > 2,
            "confidence_score": round(confidence_score, 2),
            "opknowledge_contribution": opknowledge_contribution,
            "transcript_preview": audio_transcript[:100]  # First 100 chars
        }
        
        if not test_passed:
            result["risk_flag"] = "failed_operational_knowledge_test"
        
        return result


# Quick test
if __name__ == "__main__":
    opk = OperationalKnowledge()
    
    # Test case 1: Good response
    test1 = opk.analyze(
        audio_transcript="The Ashirvaad atta is on the left shelf, it costs 280 rupees for 5kg",
        video_duration=8.5
    )
    print("Test 1 (Good response):")
    print(f"Passed: {test1['test_passed']}")
    print(f"Confidence: {test1['confidence_score']}")
    print()
    
    # Test case 2: Hesitant response
    test2 = opk.analyze(
        audio_transcript="Um, I think it's maybe on that shelf, uh, probably around 300 rupees",
        video_duration=15.2
    )
    print("Test 2 (Hesitant response):")
    print(f"Passed: {test2['test_passed']}")
    print(f"Confidence: {test2['confidence_score']}")
    print()
    
    # Test case 3: Failed response (no price)
    test3 = opk.analyze(
        audio_transcript="I don't know where it is",
        video_duration=12.0
    )
    print("Test 3 (Failed - no price):")
    print(f"Passed: {test3['test_passed']}")
    print(f"Risk Flag: {test3.get('risk_flag', 'None')}")