"""
Image Generator - Generate simple line drawings for coloring book
Supports multiple AI image generation APIs
"""
import json
import sys
import requests
import time
from pathlib import Path
from PIL import Image
import io
from config import (
    BOOK_PLANS_DIR, GENERATED_IMAGES_DIR, 
    IMAGE_GEN_CONFIG, IMAGE_API_CONFIG
)

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

class ImageGenerator:
    """Generate coloring book images using AI"""
    
    def __init__(self, provider="stability"):
        """
        Initialize image generator
        
        Args:
            provider: API provider ("stability", "replicate", "huggingface", "local")
        """
        self.provider = provider
        self.api_key = IMAGE_API_CONFIG.get("api_key", "")
        
        print(f"ImageGenerator initialized with provider: {provider}")
        
        if not self.api_key and provider != "local":
            print("⚠ Warning: No API key set. Set IMAGE_API_CONFIG['api_key'] in config.py")
    
    def generate_from_plan(self, plan_file="book_001_plan.json", start_page=1, end_page=None):
        """
        Generate images for all pages in a book plan
        
        Args:
            plan_file: Book plan JSON file
            start_page: Start from this page number
            end_page: End at this page number (None = all pages)
        """
        print("="*60)
        print("Image Generation")
        print("="*60)
        
        # Load book plan
        plan_path = BOOK_PLANS_DIR / plan_file
        with open(plan_path, "r") as f:
            book_plan = json.load(f)
        
        pages = book_plan['pages']
        if end_page:
            pages = [p for p in pages if start_page <= p['page_number'] <= end_page]
        else:
            pages = [p for p in pages if p['page_number'] >= start_page]
        
        print(f"\nGenerating {len(pages)} images...")
        print(f"Provider: {self.provider}")
        print(f"Output: {GENERATED_IMAGES_DIR}\n")
        
        success_count = 0
        fail_count = 0
        
        for page in pages:
            page_num = page['page_number']
            subject = page['subject']
            prompt = page['prompt']
            
            print(f"[{page_num}/100] Generating: {subject}...", end=" ")
            
            try:
                image_path = self.generate_image(
                    prompt=prompt,
                    page_number=page_num,
                    subject=subject
                )
                
                if image_path:
                    print(f"✓ Saved to {image_path.name}")
                    success_count += 1
                    
                    # Update plan status
                    page['status'] = 'generated'
                    page['image_path'] = str(image_path)
                else:
                    print("✗ Failed")
                    fail_count += 1
                    page['status'] = 'failed'
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                fail_count += 1
                page['status'] = 'failed'
        
        # Save updated plan
        with open(plan_path, "w") as f:
            json.dump(book_plan, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"Generation complete!")
        print(f"  Success: {success_count}")
        print(f"  Failed: {fail_count}")
        print(f"{'='*60}")
    
    def generate_image(self, prompt, page_number, subject):
        """
        Generate a single image
        
        Args:
            prompt: Text prompt
            page_number: Page number
            subject: Subject name (for filename)
        
        Returns:
            Path: Path to saved image, or None if failed
        """
        if self.provider == "stability":
            return self._generate_stability(prompt, page_number, subject)
        elif self.provider == "replicate":
            return self._generate_replicate(prompt, page_number, subject)
        elif self.provider == "huggingface":
            return self._generate_huggingface(prompt, page_number, subject)
        elif self.provider == "local":
            return self._generate_local(prompt, page_number, subject)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _generate_stability(self, prompt, page_number, subject):
        """Generate using Stability AI API"""
        if not self.api_key:
            raise ValueError("Stability AI API key not set")
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                },
                {
                    "text": IMAGE_GEN_CONFIG['negative_prompt'],
                    "weight": -1
                }
            ],
            "cfg_scale": IMAGE_GEN_CONFIG['guidance_scale'],
            "height": IMAGE_GEN_CONFIG['height'],
            "width": IMAGE_GEN_CONFIG['width'],
            "samples": 1,
            "steps": IMAGE_GEN_CONFIG['num_inference_steps']
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            image_data = data['artifacts'][0]['base64']
            
            # Decode and save
            import base64
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Save
            filename = f"page_{page_number:03d}_{subject.lower().replace(' ', '_')}.png"
            output_path = GENERATED_IMAGES_DIR / filename
            image.save(output_path)
            
            return output_path
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    
    def _generate_replicate(self, prompt, page_number, subject):
        """Generate using Replicate API (cheaper alternative)"""
        # TODO: Implement Replicate API
        # https://replicate.com/stability-ai/sdxl
        raise NotImplementedError("Replicate provider not yet implemented")
    
    def _generate_huggingface(self, prompt, page_number, subject):
        """Generate using Hugging Face Inference API (free tier available)"""
        if not self.api_key:
            raise ValueError("Hugging Face API key not set")
        
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": IMAGE_GEN_CONFIG['negative_prompt'],
                "num_inference_steps": IMAGE_GEN_CONFIG['num_inference_steps'],
                "guidance_scale": IMAGE_GEN_CONFIG['guidance_scale']
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content))
            
            # Save
            filename = f"page_{page_number:03d}_{subject.lower().replace(' ', '_')}.png"
            output_path = GENERATED_IMAGES_DIR / filename
            image.save(output_path)
            
            return output_path
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    
    def _generate_local(self, prompt, page_number, subject):
        """
        Generate using local Stable Diffusion
        Requires: stable-diffusion-webui or ComfyUI running locally
        """
        # TODO: Implement local SD API
        # For now, create a placeholder
        print("(Creating placeholder - set up local SD for real generation)")
        
        # Create a simple placeholder image
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (1024, 1024), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw simple text placeholder
        text = f"{subject}\n(Page {page_number})"
        draw.text((512, 512), text, fill='black', anchor='mm')
        
        # Save
        filename = f"page_{page_number:03d}_{subject.lower().replace(' ', '_')}.png"
        output_path = GENERATED_IMAGES_DIR / filename
        img.save(output_path)
        
        return output_path


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate coloring book images")
    parser.add_argument("--provider", default="local", choices=["stability", "replicate", "huggingface", "local"],
                       help="Image generation provider")
    parser.add_argument("--plan", default="book_001_plan.json", help="Book plan file")
    parser.add_argument("--start", type=int, default=1, help="Start page number")
    parser.add_argument("--end", type=int, default=None, help="End page number")
    parser.add_argument("--test", action="store_true", help="Test mode (generate only first 5 pages)")
    
    args = parser.parse_args()
    
    if args.test:
        args.end = 5
        print("⚠ TEST MODE: Generating only pages 1-5\n")
    
    generator = ImageGenerator(provider=args.provider)
    generator.generate_from_plan(
        plan_file=args.plan,
        start_page=args.start,
        end_page=args.end
    )


if __name__ == "__main__":
    main()
