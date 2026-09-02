# KDP Coloring Book Pipeline

**AI-powered pipeline for creating and publishing kids coloring books on Amazon KDP**

Validate manually first, then automate what works.

---

## 📚 Book #1: My First Big Coloring Book

- **Pages**: 100
- **Target**: Kids ages 3-8
- **Categories**: Animals, Vehicles, Fruits, Shapes, Birds, Sea Creatures, Insects, Flowers
- **Price**: $6.99 USD
- **Platform**: Amazon KDP (kdp.amazon.com)

---

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
cd F:\projects\claude\kdp-coloring-pipeline
pip install -r requirements.txt
```

### 2. Generate Book Plan (100 pages)

```powershell
python book_planner.py
```

Output: `book_plans/book_001_plan.json`

### 3. Generate Images

**Option A: Placeholders (for testing)**
```powershell
python image_generator.py --provider local --test
```

**Option B: Real AI images (requires API key)**
```powershell
# Set API key in config.py first
python image_generator.py --provider huggingface
```

Output: `generated_images/page_001_dog.png` ... `page_100_lotus.png`

### 4. Review & Approve Images

```powershell
# Copy good images to approved_images/
cp generated_images/page_*.png approved_images/
```

### 5. Build KDP PDF

```powershell
python pdf_builder.py
```

Output: `output/My_First_Big_Coloring_Book_Interior.pdf`

### 6. Create Cover

Use the dimensions printed by pdf_builder.py:
- Full cover width: ~17.25"
- Full cover height: ~11.25"
- Spine width: ~0.225"

Design in Canva or Photoshop.

### 7. Upload to KDP

Go to https://kdp.amazon.com/en_US/create and upload:
- Interior PDF
- Cover PDF
- Set price: $6.99

---

## 📁 Project Structure

```
kdp-coloring-pipeline/
├── book_planner.py          # Generate 100-page content plan
├── image_generator.py       # Generate line drawings (AI)
├── pdf_builder.py           # Assemble KDP-ready PDF
├── config.py                # Configuration
├── requirements.txt         # Python dependencies
├── book_plans/              # JSON plans
│   └── book_001_plan.json
├── generated_images/        # Raw AI images
├── approved_images/         # QC-passed images
└── output/                  # Final PDFs
```

---

## 🎨 Image Generation Options

### Free/Cheap Options

| Provider | Cost | Quality | Setup |
|----------|------|---------|-------|
| **Local (placeholder)** | Free | Low (testing only) | None |
| **Hugging Face** | Free tier | Medium | API key |
| **Replicate** | ~$0.01/image | High | API key + credit card |
| **Stability AI** | ~$0.02/image | High | API key + credit card |

### Recommended: Hugging Face (Free Tier)

1. Sign up at https://huggingface.co
2. Get API token: https://huggingface.co/settings/tokens
3. Add to `config.py`:
   ```python
   IMAGE_API_CONFIG = {
       "provider": "huggingface",
       "api_key": "hf_your_token_here"
   }
   ```
4. Run:
   ```powershell
   python image_generator.py --provider huggingface
   ```

---

## 🔧 Configuration

Edit `config.py`:

```python
# Book settings
BOOK_CONFIG = {
    "title": "My First Big Coloring Book",
    "author": "Creative Kids Publishing",  # Change to your pen name
    "total_pages": 100,
    "categories": {
        "Animals": 20,
        "Vehicles": 15,
        # ... adjust as needed
    }
}

# KDP specs (8.5" x 11")
KDP_SPECS = {
    "trim_width_inches": 8.5,
    "trim_height_inches": 11.0,
    "dpi": 300
}

# Pricing
PRICING = {
    "target_price_usd": 6.99,
    "printing_cost_estimate_usd": 2.50,
    "target_royalty_usd": 4.49
}
```

---

## 📊 Workflow

```
1. PLAN
   python book_planner.py
   → book_plans/book_001_plan.json

2. GENERATE
   python image_generator.py --provider huggingface
   → generated_images/page_*.png

3. REVIEW
   Manually check images, copy good ones to approved_images/

4. BUILD PDF
   python pdf_builder.py
   → output/My_First_Big_Coloring_Book_Interior.pdf

5. DESIGN COVER
   Use Canva with dimensions from pdf_builder output

6. PUBLISH
   Upload to kdp.amazon.com
```

---

## 🎯 Phase 1: Manual Validation

**Goal**: Create and publish Book #1 manually to validate the market.

**Steps**:
1. ✅ Generate book plan
2. ⏳ Generate 100 images (test with 5 first)
3. ⏳ Review quality
4. ⏳ Build PDF
5. ⏳ Design cover
6. ⏳ Publish on KDP
7. ⏳ Track sales for 30 days

**Decision point**: If Book #1 sells 5+ copies/day → automate and scale. If not → pivot niche.

---

## 🤖 Phase 2: Automation (After Book #1 Success)

Only automate after validating Book #1 works:

1. **Batch image generation** - Generate all 100 images overnight
2. **Auto QC** - Filter bad images automatically
3. **One-click PDF** - Auto-build PDF from approved images
4. **Cover templates** - Reusable cover designs
5. **Series generator** - Create Book #2, #3 in same niche

---

## 💰 Economics (Book #1)

| Item | Cost |
|------|------|
| Image generation (100 images @ $0.01) | $1.00 |
| Cover design (Canva Pro) | $0 (free tier) |
| **Total cost** | **$1.00** |

| Revenue (per book sold) | Amount |
|-------------------------|--------|
| List price | $6.99 |
| KDP printing cost | -$2.50 |
| **Your royalty** | **$4.49** |

**Break-even**: 1 book sold  
**Target**: 5 sales/day = $22.45/day = $674/month per book

---

## 📈 Next Steps

1. **Test image generation**:
   ```powershell
   python image_generator.py --provider local --test
   ```

2. **Review test images**:
   ```powershell
   ls generated_images/
   ```

3. **If placeholders look good, get real API**:
   - Sign up at Hugging Face
   - Get API token
   - Update `config.py`
   - Generate real images

4. **Build PDF and check quality**:
   ```powershell
   python pdf_builder.py --use-generated
   ```

5. **Open PDF and review**:
   ```powershell
   start output/My_First_Big_Coloring_Book_Interior.pdf
   ```

---

## 🐛 Troubleshooting

**"No module named 'PIL'"**
→ Run `pip install -r requirements.txt`

**"Image not found"**
→ Run `python image_generator.py` first to generate images

**"API key not set"**
→ Add your API key to `config.py` in `IMAGE_API_CONFIG`

**Images look bad**
→ Try different provider or adjust prompts in `book_planner.py`

---

## 📚 Resources

- **KDP Help**: https://kdp.amazon.com/en_US/help
- **KDP Cover Calculator**: https://kdp.amazon.com/en_US/cover-templates
- **Canva (cover design)**: https://www.canva.com
- **Hugging Face (free AI)**: https://huggingface.co

---

**Built for manual validation first, automation second. Let's make Book #1 work before scaling! 🚀**
