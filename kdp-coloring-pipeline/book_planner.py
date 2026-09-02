"""
Book Planner - Generate structured content plan for coloring book
Creates a 100-page plan with specific subjects for each page
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from config import BOOK_CONFIG, BOOK_PLANS_DIR

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Detailed page subjects for each category
SUBJECTS = {
    "Animals": [
        "Dog", "Cat", "Elephant", "Lion", "Tiger", "Giraffe", "Zebra", "Monkey",
        "Bear", "Rabbit", "Horse", "Cow", "Pig", "Sheep", "Goat", "Deer",
        "Fox", "Wolf", "Panda", "Koala"
    ],
    "Vehicles": [
        "Car", "Bus", "Train", "Airplane", "Helicopter", "Boat", "Ship", "Bicycle",
        "Motorcycle", "Truck", "Fire Truck", "Police Car", "Ambulance", "Tractor", "Rocket"
    ],
    "Fruits & Vegetables": [
        "Apple", "Banana", "Orange", "Grapes", "Strawberry", "Watermelon", "Pineapple",
        "Carrot", "Tomato", "Broccoli", "Corn", "Pumpkin", "Potato", "Onion", "Pepper"
    ],
    "Shapes & Objects": [
        "Circle", "Square", "Triangle", "Star", "Heart", "House", "Tree", "Sun",
        "Moon", "Cloud", "Ball", "Balloon", "Kite", "Umbrella", "Book"
    ],
    "Birds": [
        "Parrot", "Peacock", "Owl", "Eagle", "Sparrow", "Duck", "Swan", "Penguin",
        "Flamingo", "Crow"
    ],
    "Sea Creatures": [
        "Fish", "Dolphin", "Whale", "Octopus", "Starfish", "Crab", "Seahorse",
        "Jellyfish", "Turtle", "Shark"
    ],
    "Insects": [
        "Butterfly", "Bee", "Ladybug", "Dragonfly", "Ant", "Grasshopper",
        "Caterpillar", "Spider", "Snail", "Firefly"
    ],
    "Flowers": [
        "Rose", "Sunflower", "Tulip", "Daisy", "Lotus"
    ]
}


def generate_book_plan():
    """
    Generate a structured 100-page book plan
    
    Returns:
        dict: Book plan with page-by-page subjects
    """
    print("="*60)
    print("KDP Coloring Book Planner")
    print("="*60)
    print(f"\nGenerating plan for: {BOOK_CONFIG['title']}")
    print(f"Total pages: {BOOK_CONFIG['total_pages']}")
    print(f"Target age: {BOOK_CONFIG['target_age']}\n")
    
    pages = []
    page_num = 1
    
    # Generate pages for each category
    for category, count in BOOK_CONFIG['categories'].items():
        print(f"Planning {category}: {count} pages")
        
        subjects = SUBJECTS[category][:count]  # Get required number of subjects
        
        for subject in subjects:
            page = {
                "page_number": page_num,
                "category": category,
                "subject": subject,
                "prompt": generate_prompt(subject, category),
                "status": "pending"
            }
            pages.append(page)
            page_num += 1
    
    # Create book plan
    book_plan = {
        "metadata": {
            "title": BOOK_CONFIG['title'],
            "subtitle": BOOK_CONFIG['subtitle'],
            "author": BOOK_CONFIG['author'],
            "total_pages": BOOK_CONFIG['total_pages'],
            "target_age": BOOK_CONFIG['target_age'],
            "created_at": datetime.now().isoformat(),
            "status": "planned"
        },
        "pages": pages,
        "summary": {
            "total_pages": len(pages),
            "categories": BOOK_CONFIG['categories']
        }
    }
    
    # Save to file
    output_file = BOOK_PLANS_DIR / "book_001_plan.json"
    with open(output_file, "w") as f:
        json.dump(book_plan, f, indent=2)
    
    print(f"\n✓ Book plan saved to: {output_file}")
    print(f"✓ Total pages planned: {len(pages)}")
    print("\nCategory breakdown:")
    for category, count in BOOK_CONFIG['categories'].items():
        print(f"  {category}: {count} pages")
    
    return book_plan


def generate_prompt(subject, category):
    """
    Generate AI image prompt for a specific subject
    
    Args:
        subject: The subject to draw (e.g., "Dog", "Car")
        category: The category (e.g., "Animals", "Vehicles")
    
    Returns:
        str: Complete prompt for image generation
    """
    # Base prompt for kids coloring book style
    base_style = "Simple black and white line drawing for kids coloring book"
    
    # Subject-specific details
    subject_prompt = f"{subject}"
    
    # Add context based on category
    if category == "Animals":
        subject_prompt += ", cute and friendly looking, full body view"
    elif category == "Vehicles":
        subject_prompt += ", side view, simple design"
    elif category == "Fruits & Vegetables":
        subject_prompt += ", whole fruit/vegetable, simple shape"
    elif category == "Shapes & Objects":
        subject_prompt += ", clear and simple shape"
    elif category == "Birds":
        subject_prompt += ", side or front view, wings visible"
    elif category == "Sea Creatures":
        subject_prompt += ", swimming pose, friendly looking"
    elif category == "Insects":
        subject_prompt += ", top view, clear body parts"
    elif category == "Flowers":
        subject_prompt += ", front view, petals clearly visible"
    
    # Complete prompt
    full_prompt = f"{base_style}. {subject_prompt}. Clean bold outlines, no shading, no color, no gradients, white background, centered composition, suitable for ages 3-8, no text"
    
    return full_prompt


def print_sample_pages(book_plan, num_samples=10):
    """Print sample pages from the plan"""
    print(f"\n{'='*60}")
    print(f"Sample Pages (first {num_samples}):")
    print(f"{'='*60}\n")
    
    for page in book_plan['pages'][:num_samples]:
        print(f"Page {page['page_number']}: {page['subject']} ({page['category']})")
        print(f"  Prompt: {page['prompt'][:80]}...")
        print()


if __name__ == "__main__":
    # Generate the book plan
    plan = generate_book_plan()
    
    # Print samples
    print_sample_pages(plan, num_samples=10)
    
    print("\n" + "="*60)
    print("Next steps:")
    print("="*60)
    print("1. Review the book plan: book_plans/book_001_plan.json")
    print("2. Run image_generator.py to generate images")
    print("3. Review and approve images")
    print("4. Run pdf_builder.py to create KDP files")
    print("="*60)
