"""
Test script to verify Amazon Image Agent setup
Run this to check if all modules are working correctly
"""
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("Amazon Image Agent - Setup Test")
print("="*60)

# Test 1: Check Python version
print("\n[1/6] Checking Python version...")
if sys.version_info >= (3, 8):
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"✗ Python {sys.version_info.major}.{sys.version_info.minor} (need 3.8+)")
    sys.exit(1)

# Test 2: Check dependencies
print("\n[2/6] Checking dependencies...")
try:
    import requests
    print("✓ requests installed")
except ImportError:
    print("✗ requests not installed (run: pip install -r requirements.txt)")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    print("✓ python-dotenv installed")
except ImportError:
    print("✗ python-dotenv not installed (run: pip install -r requirements.txt)")
    sys.exit(1)

# Test 3: Check project structure
print("\n[3/6] Checking project structure...")
required_dirs = ["config", "modules", "logs", "state", "results"]
for dir_name in required_dirs:
    dir_path = Path(__file__).parent / dir_name
    if dir_path.exists():
        print(f"✓ {dir_name}/ exists")
    else:
        print(f"✗ {dir_name}/ missing")
        sys.exit(1)

# Test 4: Check modules
print("\n[4/6] Checking modules...")
sys.path.append(str(Path(__file__).parent))

try:
    from config.settings import KREA_API_KEY, RESULTS_DIR
    print("✓ config.settings imported")
except Exception as e:
    print(f"✗ config.settings import failed: {e}")
    sys.exit(1)

try:
    from modules.krea_client import KreaClient
    print("✓ modules.krea_client imported")
except Exception as e:
    print(f"✗ modules.krea_client import failed: {e}")
    sys.exit(1)

try:
    from modules.amazon_monitor import AmazonMonitor
    print("✓ modules.amazon_monitor imported")
except Exception as e:
    print(f"✗ modules.amazon_monitor import failed: {e}")
    sys.exit(1)

try:
    from modules.revenue_tracker import RevenueTracker
    print("✓ modules.revenue_tracker imported")
except Exception as e:
    print(f"✗ modules.revenue_tracker import failed: {e}")
    sys.exit(1)

# Test 5: Check .env file
print("\n[5/6] Checking .env configuration...")
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print("✓ .env file exists")
    load_dotenv(env_file)
    if KREA_API_KEY:
        print(f"✓ KREA_API_KEY configured ({len(KREA_API_KEY)} chars)")
    else:
        print("⚠ KREA_API_KEY not set in .env (add your key from https://krea.ai/app/api/tokens)")
else:
    print("⚠ .env file not found (copy .env.example to .env and add your Krea API key)")

# Test 6: Test module instantiation
print("\n[6/6] Testing module instantiation...")
try:
    krea_client = KreaClient()
    print("✓ KreaClient instantiated")
except Exception as e:
    print(f"✗ KreaClient failed: {e}")
    sys.exit(1)

try:
    monitor = AmazonMonitor()
    print("✓ AmazonMonitor instantiated")
except Exception as e:
    print(f"✗ AmazonMonitor failed: {e}")
    sys.exit(1)

try:
    tracker = RevenueTracker()
    print("✓ RevenueTracker instantiated")
except Exception as e:
    print(f"✗ RevenueTracker failed: {e}")
    sys.exit(1)

# Test 7: Test mock data
print("\n[7/7] Testing mock data...")
try:
    listings = monitor.get_new_listings(max_count=2)
    print(f"✓ AmazonMonitor returned {len(listings)} mock listings")
    if listings:
        print(f"  Sample: {listings[0]['title'][:50]}...")
except Exception as e:
    print(f"✗ AmazonMonitor.get_new_listings() failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*60)
print("Setup Test Complete!")
print("="*60)
print("\n✓ All checks passed!")
print("\nNext steps:")
print("1. Add your Krea API key to .env (if not done)")
print("2. Run: python agent.py")
print("3. Schedule daily runs: python scheduler.py create")
print("\nFor help, see README.md or QUICKSTART.md")
print("="*60)
