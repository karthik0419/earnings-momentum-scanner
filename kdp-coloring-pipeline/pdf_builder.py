"""
PDF Builder - Create KDP-ready interior PDF from approved images
"""
import json
from pathlib import Path
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from config import (
    BOOK_PLANS_DIR, APPROVED_IMAGES_DIR, GENERATED_IMAGES_DIR,
    OUTPUT_DIR, KDP_SPECS, BOOK_CONFIG
)

class PDFBuilder:
    """Build KDP-ready PDF from coloring book images"""
    
    def __init__(self):
        """Initialize PDF builder"""
        self.trim_width = KDP_SPECS['trim_width_inches']
        self.trim_height = KDP_SPECS['trim_height_inches']
        self.dpi = KDP_SPECS['dpi']
        
        print(f"PDFBuilder initialized")
        print(f"  Trim size: {self.trim_width}\" x {self.trim_height}\"")
        print(f"  DPI: {self.dpi}")
    
    def build_interior(self, plan_file="book_001_plan.json", use_approved=True):
        """
        Build interior PDF from images
        
        Args:
            plan_file: Book plan JSON file
            use_approved: Use approved_images/ folder (True) or generated_images/ (False)
        """
        print("="*60)
        print("Building KDP Interior PDF")
        print("="*60)
        
        # Load book plan
        plan_path = BOOK_PLANS_DIR / plan_file
        with open(plan_path, "r") as f:
            book_plan = json.load(f)
        
        # Determine image source folder
        image_folder = APPROVED_IMAGES_DIR if use_approved else GENERATED_IMAGES_DIR
        print(f"\nImage source: {image_folder}")
        
        # Get all images
        pages = book_plan['pages']
        print(f"Total pages: {len(pages)}\n")
        
        # Create PDF
        output_file = OUTPUT_DIR / f"{book_plan['metadata']['title'].replace(' ', '_')}_Interior.pdf"
        
        # ReportLab uses points (1 inch = 72 points)
        page_width = self.trim_width * 72
        page_height = self.trim_height * 72
        
        c = canvas.Canvas(str(output_file), pagesize=(page_width, page_height))
        
        missing_images = []
        added_pages = 0
        
        for page in pages:
            page_num = page['page_number']
            subject = page['subject']
            
            # Find image file
            image_filename = f"page_{page_num:03d}_{subject.lower().replace(' ', '_')}.png"
            image_path = image_folder / image_filename
            
            if not image_path.exists():
                print(f"⚠ Page {page_num}: Image not found - {image_filename}")
                missing_images.append(page_num)
                continue
            
            print(f"✓ Page {page_num}: Adding {subject}")
            
            # Open and resize image to fit page
            img = Image.open(image_path)
            
            # Convert to grayscale (B&W for KDP)
            img = img.convert('L')
            
            # Calculate dimensions to fit page with margins
            margin = 0.5 * inch  # 0.5" margin on all sides
            available_width = page_width - (2 * margin)
            available_height = page_height - (2 * margin)
            
            # Resize image to fit
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            
            if aspect_ratio > (available_width / available_height):
                # Width is limiting factor
                new_width = available_width
                new_height = available_width / aspect_ratio
            else:
                # Height is limiting factor
                new_height = available_height
                new_width = available_height * aspect_ratio
            
            # Center image on page
            x = (page_width - new_width) / 2
            y = (page_height - new_height) / 2
            
            # Save temp resized image
            temp_path = image_folder / f"temp_{image_filename}"
            img_resized = img.resize((int(new_width * self.dpi / 72), int(new_height * self.dpi / 72)), Image.Resampling.LANCZOS)
            img_resized.save(temp_path)
            
            # Add to PDF
            c.drawImage(str(temp_path), x, y, width=new_width, height=new_height)
            c.showPage()
            
            # Clean up temp file
            temp_path.unlink()
            
            added_pages += 1
        
        # Save PDF
        c.save()
        
        print(f"\n{'='*60}")
        print(f"PDF Generation Complete!")
        print(f"  Pages added: {added_pages}")
        print(f"  Missing images: {len(missing_images)}")
        if missing_images:
            print(f"  Missing page numbers: {missing_images}")
        print(f"  Output: {output_file}")
        print(f"  File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"{'='*60}")
        
        return output_file
    
    def calculate_spine_width(self, page_count):
        """
        Calculate spine width for cover
        
        Args:
            page_count: Number of pages in book
        
        Returns:
            float: Spine width in inches
        """
        # KDP formula for B&W books on white paper
        # Spine width = (page count × 0.002252) inches
        spine_width = page_count * 0.002252
        return spine_width
    
    def get_cover_dimensions(self, page_count):
        """
        Get full cover dimensions including spine and bleed
        
        Args:
            page_count: Number of pages in book
        
        Returns:
            dict: Cover dimensions
        """
        spine_width = self.calculate_spine_width(page_count)
        bleed = KDP_SPECS['bleed_inches']
        
        # Full cover width = bleed + back cover + spine + front cover + bleed
        cover_width = (2 * bleed) + (2 * self.trim_width) + spine_width
        
        # Full cover height = bleed + trim height + bleed
        cover_height = (2 * bleed) + self.trim_height
        
        return {
            "width_inches": cover_width,
            "height_inches": cover_height,
            "spine_width_inches": spine_width,
            "bleed_inches": bleed,
            "trim_width_inches": self.trim_width,
            "trim_height_inches": self.trim_height
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build KDP interior PDF")
    parser.add_argument("--plan", default="book_001_plan.json", help="Book plan file")
    parser.add_argument("--use-generated", action="store_true", 
                       help="Use generated_images/ instead of approved_images/")
    
    args = parser.parse_args()
    
    builder = PDFBuilder()
    
    use_approved = not args.use_generated
    pdf_file = builder.build_interior(plan_file=args.plan, use_approved=use_approved)
    
    # Print cover dimensions
    print("\n" + "="*60)
    print("Cover Dimensions (for cover design):")
    print("="*60)
    
    page_count = BOOK_CONFIG['total_pages']
    cover_dims = builder.get_cover_dimensions(page_count)
    
    print(f"Page count: {page_count}")
    print(f"Spine width: {cover_dims['spine_width_inches']:.4f}\"")
    print(f"Full cover width: {cover_dims['width_inches']:.4f}\"")
    print(f"Full cover height: {cover_dims['height_inches']:.4f}\"")
    print(f"\nUse these dimensions in Canva or your cover design tool.")
    print("="*60)


if __name__ == "__main__":
    main()
