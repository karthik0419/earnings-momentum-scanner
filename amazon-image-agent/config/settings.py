"""
Configuration settings for Amazon Image Agent
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = PROJECT_ROOT / "logs"
STATE_DIR = PROJECT_ROOT / "state"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure directories exist
for dir_path in [LOGS_DIR, STATE_DIR, RESULTS_DIR]:
    dir_path.mkdir(exist_ok=True)

# Krea AI settings
KREA_API_KEY = os.getenv("KREA_API_KEY", "")  # Get from https://krea.ai/app/api/tokens
KREA_MCP_URL = "https://api.krea.ai/mcp"

# Amazon settings
AMAZON_MARKETPLACE = os.getenv("AMAZON_MARKETPLACE", "amazon.in")  # amazon.com, amazon.in, etc.
AMAZON_SELLER_ID = os.getenv("AMAZON_SELLER_ID", "")

# Image generation settings
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
IMAGES_PER_LISTING = 5  # Generate 5 images per product
IMAGE_QUALITY = "high"

# Loop settings
LOOP_INTERVAL_HOURS = 24  # Run once per day
MAX_LISTINGS_PER_RUN = 10  # Process max 10 listings per run
STATE_FILE = STATE_DIR / "agent_state.json"

# Revenue tracking
REVENUE_LOG = STATE_DIR / "revenue_log.json"
CONVERSION_RATE_TARGET = 0.03  # 3% target conversion rate
AVG_ORDER_VALUE_TARGET = 500  # Rs 500 average order value (adjust for your market)

# Logging
LOG_FILE = LOGS_DIR / "agent.log"
LOG_LEVEL = "INFO"
