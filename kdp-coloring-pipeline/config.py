"""
KDP Coloring Book Pipeline - Configuration
"""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
BOOK_PLANS_DIR = PROJECT_ROOT / "book_plans"
GENERATED_IMAGES_DIR = PROJECT_ROOT / "generated_images"
APPROVED_IMAGES_DIR = PROJECT_ROOT / "approved_images"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Ensure directories exist
for dir_path in [BOOK_PLANS_DIR, GENERATED_IMAGES_DIR, APPROVED_IMAGES_DIR, OUTPUT_DIR, TEMPLATES_DIR]:
    dir_path.mkdir(exist_ok=True)

# Book #1 Configuration
BOOK_CONFIG = {
    "title": "My First Big Coloring Book",
    "subtitle": "100 Fun Pages for Kids Ages 3-8",
    "author": "Creative Kids Publishing",  # Change this to your pen name
    "total_pages": 100,
    "target_age": "3-8 years",
    "style": "Simple black line drawings for coloring",
    "categories": {
        "Animals": 20,
        "Vehicles": 15,
        "Fruits & Vegetables": 15,
        "Shapes & Objects": 15,
        "Birds": 10,
        "Sea Creatures": 10,
        "Insects": 10,
        "Flowers": 5
    }
}

# KDP Specifications (for 8.5" x 11" trim size)
KDP_SPECS = {
    "trim_width_inches": 8.5,
    "trim_height_inches": 11.0,
    "dpi": 300,  # Print resolution
    "bleed_inches": 0.125,  # 0.125" bleed on all sides
    "interior_color": "black_and_white",
    "paper_type": "white",
    "binding": "paperback"
}

# Calculate pixel dimensions
KDP_SPECS["page_width_px"] = int(KDP_SPECS["trim_width_inches"] * KDP_SPECS["dpi"])
KDP_SPECS["page_height_px"] = int(KDP_SPECS["trim_height_inches"] * KDP_SPECS["dpi"])
KDP_SPECS["bleed_px"] = int(KDP_SPECS["bleed_inches"] * KDP_SPECS["dpi"])

# Image generation settings
IMAGE_GEN_CONFIG = {
    "style_prompt": "simple black and white line drawing for kids coloring book, clean outlines, no shading, no color, white background, centered composition",
    "negative_prompt": "color, shading, gradients, complex details, text, watermark, realistic, photo",
    "width": 1024,  # Generate at higher res, then resize
    "height": 1024,
    "guidance_scale": 7.5,
    "num_inference_steps": 30
}

# AI API Configuration (you'll need to set these)
AI_CONFIG = {
    "provider": "openai",  # or "anthropic" for Claude
    "model": "gpt-4",  # for planning
    "api_key": "",  # Set via environment variable
}

# Image API Configuration
IMAGE_API_CONFIG = {
    "provider": "huggingface",  # Using Hugging Face free tier
    "api_key": "HF_API_KEY_REDACTED",
}

# Pricing (for US market via KDP)
PRICING = {
    "target_price_usd": 6.99,  # Typical kids coloring book price
    "printing_cost_estimate_usd": 2.50,  # KDP printing cost for 100-page B&W book
    "target_royalty_usd": 4.49,  # 6.99 - 2.50
    "marketplace": "Amazon.com (US)"
}
