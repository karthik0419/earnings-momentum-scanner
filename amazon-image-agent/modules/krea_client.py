"""
Krea AI image generation client
Integrates with Krea AI MCP server for product image generation
"""
import logging
import json
import requests
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config.settings import KREA_API_KEY, KREA_MCP_URL, IMAGE_WIDTH, IMAGE_HEIGHT, RESULTS_DIR

logger = logging.getLogger(__name__)


class KreaClient:
    """Client for Krea AI image generation via MCP"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Krea client
        
        Args:
            api_key: Krea API key (if not using OAuth)
        """
        self.api_key = api_key or KREA_API_KEY
        self.mcp_url = KREA_MCP_URL
        self.headers = {}
        
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
        
        logger.info("KreaClient initialized")
    
    def generate_product_image(
        self,
        prompt: str,
        product_name: str,
        asin: str,
        width: int = IMAGE_WIDTH,
        height: int = IMAGE_HEIGHT,
        style: str = "realistic"
    ) -> Dict:
        """
        Generate a product image using Krea AI
        
        Args:
            prompt: Text prompt describing the product image
            product_name: Name of the product
            asin: Amazon ASIN
            width: Image width in pixels
            height: Image height in pixels
            style: Image style (realistic, artistic, minimal, etc.)
        
        Returns:
            Dict with image URL and metadata
        """
        logger.info(f"Generating image for {product_name} (ASIN: {asin})")
        
        # Build the full prompt with style guidance
        full_prompt = self._build_prompt(prompt, product_name, style)
        
        # TODO: Call Krea MCP server via MCP protocol
        # For now, this is a placeholder structure
        # You'll need to use the MCP client library or direct API calls
        
        result = {
            "asin": asin,
            "product_name": product_name,
            "prompt": full_prompt,
            "image_url": None,  # Will be populated by Krea API
            "local_path": None,
            "status": "pending",
            "metadata": {
                "width": width,
                "height": height,
                "style": style
            }
        }
        
        # Save metadata
        self._save_result(result)
        
        return result
    
    def _build_prompt(self, base_prompt: str, product_name: str, style: str) -> str:
        """
        Build enhanced prompt for product image generation
        
        Args:
            base_prompt: Base product description
            product_name: Product name
            style: Desired image style
        
        Returns:
            Enhanced prompt string
        """
        style_prompts = {
            "realistic": "photorealistic, high quality, professional product photography, studio lighting, white background",
            "lifestyle": "lifestyle photography, natural setting, in-use context, warm lighting, lifestyle scene",
            "minimal": "minimalist, clean, simple background, modern aesthetic, high contrast",
            "artistic": "artistic, creative composition, dramatic lighting, unique perspective"
        }
        
        style_suffix = style_prompts.get(style, style_prompts["realistic"])
        
        full_prompt = f"{product_name}: {base_prompt}. {style_suffix}"
        
        return full_prompt
    
    def _save_result(self, result: Dict) -> None:
        """Save generation result to disk"""
        asin = result["asin"]
        output_file = RESULTS_DIR / f"{asin}_metadata.json"
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Saved result metadata to {output_file}")
    
    def download_image(self, image_url: str, asin: str, index: int = 0) -> Path:
        """
        Download generated image from URL
        
        Args:
            image_url: URL of the generated image
            asin: Amazon ASIN
            index: Image index (for multiple images per product)
        
        Returns:
            Path to downloaded image
        """
        logger.info(f"Downloading image for ASIN {asin} (index {index})")
        
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        # Save image
        image_path = RESULTS_DIR / f"{asin}_image_{index}.png"
        
        with open(image_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Image saved to {image_path}")
        return image_path
    
    def generate_multiple_images(
        self,
        prompts: List[str],
        product_name: str,
        asin: str,
        styles: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Generate multiple images for a single product
        
        Args:
            prompts: List of prompts (different angles/contexts)
            product_name: Product name
            asin: Amazon ASIN
            styles: List of styles (one per prompt, or None for default)
        
        Returns:
            List of result dictionaries
        """
        if styles is None:
            styles = ["realistic"] * len(prompts)
        
        results = []
        for i, (prompt, style) in enumerate(zip(prompts, styles)):
            result = self.generate_product_image(
                prompt=prompt,
                product_name=product_name,
                asin=asin,
                style=style
            )
            result["index"] = i
            results.append(result)
        
        return results


if __name__ == "__main__":
    # Test the client
    client = KreaClient()
    
    test_result = client.generate_product_image(
        prompt="wireless bluetooth headphones with noise cancellation, black color, modern design",
        product_name="Premium Wireless Headphones",
        asin="B08TEST123",
        style="realistic"
    )
    
    print(json.dumps(test_result, indent=2))
