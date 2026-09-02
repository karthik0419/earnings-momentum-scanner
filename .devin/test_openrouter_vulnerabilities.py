#!/usr/bin/env python3
"""
OpenRouter Bug Bounty Testing Suite
Purpose: Responsible security research for credit/rate limit vulnerabilities
Contact: safety@openrouter.ai (get approval before running!)

⚠️  IMPORTANT: Get red-teaming approval from safety@openrouter.ai before running!
"""

import asyncio
import aiohttp
import requests
import time
import json
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

API_KEY = "OPENROUTER_API_KEY_REDACTED"
BASE_URL = "https://openrouter.ai/api/v1"
TEST_MODEL = "z-ai/glm-4.5v"  # Cheap model for testing

# ============================================================================
# Utility Functions
# ============================================================================

def log(message, level="INFO"):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def check_credits(api_key=API_KEY):
    """Check remaining credits on API key"""
    try:
        response = requests.get(
            f"{BASE_URL}/key",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        data = response.json()
        return {
            "limit": data.get("data", {}).get("limit"),
            "limit_remaining": data.get("data", {}).get("limit_remaining"),
            "limit_reset": data.get("data", {}).get("limit_reset"),
            "usage": data.get("data", {}).get("usage"),
            "raw": data
        }
    except Exception as e:
        log(f"Error checking credits: {e}", "ERROR")
        return None

def save_results(test_name, results):
    """Save test results to file"""
    filename = f"test_results_{test_name}_{int(time.time())}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    log(f"Results saved to {filename}")

# ============================================================================
# Test 1: TOCTOU Race Condition
# ============================================================================

async def test_race_condition(concurrent_requests=20):
    """
    Test if multiple concurrent requests can bypass credit checks
    
    Expected: Only 1 request succeeds (atomic deduction)
    Vulnerable: Multiple requests succeed (race condition)
    """
    log("="*60)
    log("TEST 1: TOCTOU Race Condition")
    log("="*60)
    
    # Check credits before
    credits_before = check_credits()
    log(f"Credits before: {credits_before.get('limit_remaining', 'unknown')}")
    
    async def make_request(session, i):
        start = time.time()
        try:
            async with session.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://devin.ai",
                    "X-Title": "Devin-BugBounty"
                },
                json={
                    "model": TEST_MODEL,
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 10  # Minimal tokens to reduce cost
                }
            ) as resp:
                status = resp.status
                body = await resp.text()
                elapsed = time.time() - start
                return {
                    "request_id": i,
                    "status": status,
                    "elapsed": elapsed,
                    "body": body[:200]
                }
        except Exception as e:
            return {
                "request_id": i,
                "status": "ERROR",
                "elapsed": time.time() - start,
                "error": str(e)
            }
    
    # Send concurrent requests
    log(f"Sending {concurrent_requests} concurrent requests...")
    async with aiohttp.ClientSession() as session:
        tasks = [make_request(session, i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
    
    # Analyze results
    successes = [r for r in results if r["status"] == 200]
    failures = [r for r in results if r["status"] != 200]
    
    log(f"\nResults:")
    log(f"  Total requests: {len(results)}")
    log(f"  Successful (200): {len(successes)}")
    log(f"  Failed: {len(failures)}")
    
    # Check credits after
    time.sleep(2)  # Wait for deduction
    credits_after = check_credits()
    log(f"Credits after: {credits_after.get('limit_remaining', 'unknown')}")
    
    # Verdict
    if len(successes) > 1:
        log("⚠️  POTENTIAL VULNERABILITY: Multiple requests succeeded!", "WARNING")
        log("   This suggests a race condition in credit deduction.", "WARNING")
    else:
        log("✅ No race condition detected (atomic credit deduction)", "SUCCESS")
    
    result_data = {
        "test": "race_condition",
        "timestamp": datetime.now().isoformat(),
        "concurrent_requests": concurrent_requests,
        "successes": len(successes),
        "failures": len(failures),
        "credits_before": credits_before,
        "credits_after": credits_after,
        "results": results
    }
    
    save_results("race_condition", result_data)
    return result_data

# ============================================================================
# Test 2: Streaming Credit Bypass
# ============================================================================

def test_streaming_bypass():
    """
    Test if disconnecting mid-stream avoids credit deduction
    
    Expected: Credits deducted even if disconnected
    Vulnerable: No credits deducted if disconnected early
    """
    log("="*60)
    log("TEST 2: Streaming Credit Bypass")
    log("="*60)
    
    credits_before = check_credits()
    log(f"Credits before: {credits_before.get('limit_remaining', 'unknown')}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://devin.ai",
                "X-Title": "Devin-BugBounty"
            },
            json={
                "model": TEST_MODEL,
                "messages": [{"role": "user", "content": "Write a 500 word essay"}],
                "stream": True,
                "max_tokens": 500
            },
            stream=True,
            timeout=5
        )
        
        # Read first chunk, then disconnect
        chunks_read = 0
        for chunk in response.iter_content(chunk_size=1):
            chunks_read += 1
            if chunks_read == 100:  # Disconnect after 100 bytes
                log(f"Disconnecting after {chunks_read} bytes...")
                response.close()
                break
        
        log(f"Read {chunks_read} bytes before disconnect")
        
    except Exception as e:
        log(f"Error during streaming: {e}", "ERROR")
    
    # Check credits after
    time.sleep(2)
    credits_after = check_credits()
    log(f"Credits after: {credits_after.get('limit_remaining', 'unknown')}")
    
    # Verdict
    credits_deducted = (credits_before.get('limit_remaining', 0) - 
                       credits_after.get('limit_remaining', 0))
    
    if credits_deducted == 0:
        log("⚠️  POTENTIAL VULNERABILITY: No credits deducted after disconnect!", "WARNING")
    else:
        log(f"✅ Credits deducted: {credits_deducted}", "SUCCESS")
    
    result_data = {
        "test": "streaming_bypass",
        "timestamp": datetime.now().isoformat(),
        "chunks_read": chunks_read,
        "credits_before": credits_before,
        "credits_after": credits_after,
        "credits_deducted": credits_deducted
    }
    
    save_results("streaming_bypass", result_data)
    return result_data

# ============================================================================
# Test 3: Failed Request Quota Test
# ============================================================================

def test_failed_request_quota(num_requests=10):
    """
    Test if failed requests count against quota
    
    Expected: Failed requests count against quota
    Vulnerable: Failed requests don't count (infinite retries)
    """
    log("="*60)
    log("TEST 3: Failed Request Quota")
    log("="*60)
    
    credits_before = check_credits()
    log(f"Credits before: {credits_before.get('limit_remaining', 'unknown')}")
    
    results = []
    for i in range(num_requests):
        try:
            response = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://devin.ai",
                    "X-Title": "Devin-BugBounty"
                },
                json={
                    "model": "invalid-model-name-12345",  # Force failure
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 10
                }
            )
            results.append({
                "request_id": i,
                "status": response.status_code,
                "body": response.text[:200]
            })
            log(f"Request {i+1}/{num_requests}: {response.status_code}")
        except Exception as e:
            results.append({
                "request_id": i,
                "status": "ERROR",
                "error": str(e)
            })
        
        time.sleep(0.5)  # Avoid rate limiting
    
    # Check credits after
    credits_after = check_credits()
    log(f"Credits after: {credits_after.get('limit_remaining', 'unknown')}")
    
    # Verdict
    credits_deducted = (credits_before.get('limit_remaining', 0) - 
                       credits_after.get('limit_remaining', 0))
    
    if credits_deducted == 0:
        log("⚠️  POTENTIAL VULNERABILITY: Failed requests don't count!", "WARNING")
    else:
        log(f"✅ Failed requests counted: {credits_deducted} credits deducted", "SUCCESS")
    
    result_data = {
        "test": "failed_request_quota",
        "timestamp": datetime.now().isoformat(),
        "num_requests": num_requests,
        "credits_before": credits_before,
        "credits_after": credits_after,
        "credits_deducted": credits_deducted,
        "results": results
    }
    
    save_results("failed_request_quota", result_data)
    return result_data

# ============================================================================
# Test 4: Negative Token Manipulation
# ============================================================================

def test_negative_tokens():
    """
    Test if negative max_tokens can manipulate credits
    
    Expected: Request rejected or ignored
    Vulnerable: Credits added instead of deducted
    """
    log("="*60)
    log("TEST 4: Negative Token Manipulation")
    log("="*60)
    
    credits_before = check_credits()
    log(f"Credits before: {credits_before.get('limit_remaining', 'unknown')}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://devin.ai",
                "X-Title": "Devin-BugBounty"
            },
            json={
                "model": TEST_MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": -1000  # Negative value
            }
        )
        log(f"Response status: {response.status_code}")
        log(f"Response body: {response.text[:200]}")
        
        result = {
            "status": response.status_code,
            "body": response.text
        }
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        result = {"error": str(e)}
    
    # Check credits after
    time.sleep(2)
    credits_after = check_credits()
    log(f"Credits after: {credits_after.get('limit_remaining', 'unknown')}")
    
    # Verdict
    credits_change = (credits_after.get('limit_remaining', 0) - 
                     credits_before.get('limit_remaining', 0))
    
    if credits_change > 0:
        log("⚠️  CRITICAL VULNERABILITY: Credits INCREASED!", "CRITICAL")
    elif credits_change == 0:
        log("✅ Request rejected or no credit change", "SUCCESS")
    else:
        log("✅ Credits deducted normally", "SUCCESS")
    
    result_data = {
        "test": "negative_tokens",
        "timestamp": datetime.now().isoformat(),
        "credits_before": credits_before,
        "credits_after": credits_after,
        "credits_change": credits_change,
        "result": result
    }
    
    save_results("negative_tokens", result_data)
    return result_data

# ============================================================================
# Main Test Suite
# ============================================================================

async def run_all_tests():
    """Run all vulnerability tests"""
    log("="*60)
    log("OpenRouter Bug Bounty Testing Suite")
    log("="*60)
    log("⚠️  WARNING: Get approval from safety@openrouter.ai before running!")
    log("⚠️  This is for responsible security research only!")
    log("="*60)
    
    input("Press Enter to continue (or Ctrl+C to abort)...")
    
    results = {}
    
    # Test 1: Race Condition
    try:
        results["race_condition"] = await test_race_condition(concurrent_requests=10)
    except Exception as e:
        log(f"Test 1 failed: {e}", "ERROR")
    
    time.sleep(5)  # Wait between tests
    
    # Test 2: Streaming Bypass
    try:
        results["streaming_bypass"] = test_streaming_bypass()
    except Exception as e:
        log(f"Test 2 failed: {e}", "ERROR")
    
    time.sleep(5)
    
    # Test 3: Failed Request Quota
    try:
        results["failed_request_quota"] = test_failed_request_quota(num_requests=5)
    except Exception as e:
        log(f"Test 3 failed: {e}", "ERROR")
    
    time.sleep(5)
    
    # Test 4: Negative Tokens
    try:
        results["negative_tokens"] = test_negative_tokens()
    except Exception as e:
        log(f"Test 4 failed: {e}", "ERROR")
    
    # Summary
    log("="*60)
    log("TEST SUITE COMPLETE")
    log("="*60)
    
    vulnerabilities_found = []
    for test_name, test_result in results.items():
        if test_result and "VULNERABILITY" in str(test_result):
            vulnerabilities_found.append(test_name)
    
    if vulnerabilities_found:
        log(f"⚠️  Potential vulnerabilities found in: {', '.join(vulnerabilities_found)}", "WARNING")
        log("📧 Report to: safety@openrouter.ai", "INFO")
    else:
        log("✅ No obvious vulnerabilities detected", "SUCCESS")
    
    # Save summary
    save_results("summary", {
        "timestamp": datetime.now().isoformat(),
        "tests_run": list(results.keys()),
        "vulnerabilities_found": vulnerabilities_found,
        "results": results
    })

if __name__ == "__main__":
    # Quick credit check
    log("Checking API key credits...")
    credits = check_credits()
    if credits:
        log(f"Current credits: {credits.get('limit_remaining', 'unknown')}")
        log(f"Credit limit: {credits.get('limit', 'unknown')}")
    else:
        log("Failed to check credits. Check API key.", "ERROR")
        exit(1)
    
    # Run tests
    asyncio.run(run_all_tests())
