#!/usr/bin/env python3
"""
Multi-Provider Vision API Router
Purpose: Maximize free/cheap vision API usage by rotating between providers
Strategy: Use free tiers from multiple providers before paying anything

Provider Priority (Best to Cheapest):
1. Google Gemini (FREE FOREVER - 1500 requests/day)
2. OpenRouter GLM-4.5V (Current setup - $0.0001/image)
3. GPT4Free (Reverse engineered - FREE but unstable)
4. Groq (Free tier - limited)
"""

import requests
import json
import base64
from pathlib import Path
from typing import Optional, Dict, List
import time

# ============================================================================
# Configuration
# ============================================================================

PROVIDERS = {
    "gemini": {
        "name": "Google Gemini Flash",
        "api_key": "GEMINI_API_KEY_REDACTED",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-flash-latest",
        "free_tier": "1500 requests/day PERMANENT",
        "cost": "$0 forever",
        "enabled": True  # ✅ ENABLED (2026-08-23)
    },
    "openrouter": {
        "name": "OpenRouter GLM-4.5V",
        "api_key": "OPENROUTER_API_KEY_REDACTED",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "z-ai/glm-4.5v",
        "free_tier": "$1-5 free credits",
        "cost": "$0.0001 per image",
        "enabled": True
    },
    "gpt4free": {
        "name": "GPT4Free (Community)",
        "api_key": "not-needed",
        "base_url": "https://g4f.dev/v1",
        "model": "gpt-4o",
        "free_tier": "Unlimited (community-maintained)",
        "cost": "$0 (reverse engineered)",
        "enabled": False  # Unstable, use as last resort
    }
}

# Provider rotation strategy
PROVIDER_ORDER = ["gemini", "openrouter", "gpt4free"]

# ============================================================================
# Vision API Wrapper
# ============================================================================

class MultiProviderVision:
    """Smart vision API router that maximizes free tier usage"""
    
    def __init__(self):
        self.providers = PROVIDERS
        self.usage_stats = {p: {"calls": 0, "errors": 0} for p in PROVIDER_ORDER}
        self.last_provider = None
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def analyze_with_gemini(self, image_path: str, prompt: str) -> Optional[Dict]:
        """Call Google Gemini API (FREE FOREVER)"""
        config = self.providers["gemini"]
        
        if not config["enabled"]:
            return None
        
        try:
            # Gemini uses different API format
            url = f"{config['base_url']}/models/{config['model']}:generateContent"
            
            # Read image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Detect image mime type
            ext = Path(image_path).suffix.lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp",
                ".gif": "image/gif"
            }.get(ext, "image/png")
            
            # Gemini request format (uses X-goog-api-key header)
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": config["api_key"]
                },
                json={
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_data
                                }
                            }
                        ]
                    }]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                self.usage_stats["gemini"]["calls"] += 1
                return {
                    "provider": "gemini",
                    "status": "success",
                    "text": text,
                    "cost": 0.0
                }
            else:
                print(f"[ERROR] Gemini API returned {response.status_code}: {response.text[:200]}")
                self.usage_stats["gemini"]["errors"] += 1
                return None
                
        except Exception as e:
            print(f"[ERROR] Gemini exception: {e}")
            self.usage_stats["gemini"]["errors"] += 1
            return None
    
    def analyze_with_openrouter(self, image_path: str, prompt: str) -> Optional[Dict]:
        """Call OpenRouter API (Current setup)"""
        config = self.providers["openrouter"]
        
        if not config["enabled"]:
            return None
        
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # OpenRouter uses OpenAI format
            response = requests.post(
                f"{config['base_url']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {config['api_key']}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://devin.ai",
                    "X-Title": "Devin-TradingView"
                },
                json={
                    "model": config["model"],
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                cost = data.get("usage", {}).get("cost", 0.0001)
                self.usage_stats["openrouter"]["calls"] += 1
                return {
                    "provider": "openrouter",
                    "status": "success",
                    "text": text,
                    "cost": cost
                }
            else:
                self.usage_stats["openrouter"]["errors"] += 1
                return None
                
        except Exception as e:
            print(f"OpenRouter error: {e}")
            self.usage_stats["openrouter"]["errors"] += 1
            return None
    
    def analyze_with_gpt4free(self, image_path: str, prompt: str) -> Optional[Dict]:
        """Call GPT4Free API (Reverse engineered - use as last resort)"""
        config = self.providers["gpt4free"]
        
        if not config["enabled"]:
            return None
        
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            response = requests.post(
                f"{config['base_url']}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": config["model"],
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                self.usage_stats["gpt4free"]["calls"] += 1
                return {
                    "provider": "gpt4free",
                    "status": "success",
                    "text": text,
                    "cost": 0.0
                }
            else:
                self.usage_stats["gpt4free"]["errors"] += 1
                return None
                
        except Exception as e:
            print(f"GPT4Free error: {e}")
            self.usage_stats["gpt4free"]["errors"] += 1
            return None
    
    def analyze_image(self, image_path: str, prompt: str = "Analyze this TradingView chart. Identify the pattern, key levels, and trend.") -> Dict:
        """
        Analyze image using best available provider
        
        Strategy:
        1. Try Gemini first (FREE FOREVER)
        2. Fallback to OpenRouter (cheap)
        3. Last resort: GPT4Free (unstable)
        """
        print(f"\n{'='*60}")
        print(f"Analyzing: {Path(image_path).name}")
        print(f"{'='*60}")
        
        for provider_name in PROVIDER_ORDER:
            if not self.providers[provider_name]["enabled"]:
                print(f"[SKIP] {provider_name} (disabled)")
                continue
            
            print(f"[TRY] {self.providers[provider_name]['name']}...")
            
            # Call appropriate provider
            if provider_name == "gemini":
                result = self.analyze_with_gemini(image_path, prompt)
            elif provider_name == "openrouter":
                result = self.analyze_with_openrouter(image_path, prompt)
            elif provider_name == "gpt4free":
                result = self.analyze_with_gpt4free(image_path, prompt)
            else:
                continue
            
            # If successful, return result
            if result and result["status"] == "success":
                self.last_provider = provider_name
                print(f"[SUCCESS] {result['provider']} (cost: ${result['cost']:.6f})")
                return result
            else:
                print(f"[FAIL] {provider_name}")
        
        # All providers failed
        print("[ERROR] All providers failed!")
        return {
            "provider": "none",
            "status": "error",
            "text": "All providers failed. Check API keys and quotas.",
            "cost": 0.0
        }
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        total_calls = sum(s["calls"] for s in self.usage_stats.values())
        total_errors = sum(s["errors"] for s in self.usage_stats.values())
        
        return {
            "total_calls": total_calls,
            "total_errors": total_errors,
            "by_provider": self.usage_stats,
            "last_provider": self.last_provider
        }

# ============================================================================
# Convenience Functions for Scanner Integration
# ============================================================================

# Global instance
_vision_api = None

def get_vision_api():
    """Get or create vision API instance"""
    global _vision_api
    if _vision_api is None:
        _vision_api = MultiProviderVision()
    return _vision_api

def analyze_chart(image_path: str, prompt: str = None) -> str:
    """
    Analyze a TradingView chart screenshot
    
    Usage:
        from multi_provider_vision import analyze_chart
        
        result = analyze_chart("chart.png", "Is this a Cup & Handle pattern?")
        print(result)
    """
    api = get_vision_api()
    
    if prompt is None:
        prompt = """Analyze this TradingView chart:
1. What pattern is forming? (Cup & Handle, Double Bottom, etc.)
2. What are the key support and resistance levels?
3. What is the overall trend?
4. Is this a valid breakout setup?
5. What are the entry, stop loss, and target levels?"""
    
    result = api.analyze_image(image_path, prompt)
    return result["text"]

def extract_chart_text(image_path: str) -> str:
    """
    Extract all text from a chart (OCR)
    
    Usage:
        text = extract_chart_text("chart.png")
        print(text)
    """
    api = get_vision_api()
    prompt = "Extract ALL text from this image. List every number, label, indicator value, and price level you can see."
    result = api.analyze_image(image_path, prompt)
    return result["text"]

def compare_charts(image_paths: List[str], question: str = "Which chart shows a stronger setup?") -> str:
    """
    Compare multiple charts
    
    Usage:
        result = compare_charts(["daily.png", "weekly.png"], "Which timeframe is stronger?")
        print(result)
    """
    # For now, analyze each separately and combine
    # TODO: Implement multi-image analysis
    api = get_vision_api()
    
    results = []
    for i, path in enumerate(image_paths):
        prompt = f"Chart {i+1}: {question}"
        result = api.analyze_image(path, prompt)
        results.append(f"Chart {i+1}: {result['text']}")
    
    return "\n\n".join(results)

# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI for testing"""
    import sys
    import os
    
    # Fix Windows encoding issues
    if os.name == 'nt':  # Windows
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    
    if len(sys.argv) < 2:
        print("Usage: python multi_provider_vision.py <image_path> [prompt]")
        print("\nExamples:")
        print("  python multi_provider_vision.py chart.png")
        print("  python multi_provider_vision.py chart.png 'Is this a Cup & Handle?'")
        sys.exit(1)
    
    image_path = sys.argv[1]
    prompt = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)
    
    # Analyze
    result = analyze_chart(image_path, prompt)
    print(f"\n{'='*60}")
    print("ANALYSIS RESULT")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")
    
    # Show stats
    api = get_vision_api()
    stats = api.get_stats()
    print(f"Total calls: {stats['total_calls']}")
    print(f"Total errors: {stats['total_errors']}")
    print(f"Last provider: {stats['last_provider']}")

if __name__ == "__main__":
    main()
