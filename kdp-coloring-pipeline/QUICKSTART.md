# Quick Start - KDP Coloring Book Pipeline

Get your first book ready in 30 minutes (with placeholders) or 2 hours (with real AI images).

---

## ✅ What's Already Done

- ✅ Book plan generated (100 pages)
- ✅ 5 test images created
- ✅ All scripts ready

---

## 🚀 Next Steps

### Step 1: Generate All 100 Images (Choose One)

**Option A: Placeholders (5 minutes - for testing)**
```powershell
cd F:\projects\claude\kdp-coloring-pipeline
python image_generator.py --provider local
```

**Option B: Real AI Images (2 hours - production ready)**
1. Sign up at https://huggingface.co
2. Get API token: https://huggingface.co/settings/tokens
3. Edit `config.py`:
   ```python
   IMAGE_API_CONFIG = {
       "provider": "huggingface",
       "api_key": "hf_your_token_here"
   }
   ```
4. Generate:
   ```powershell
   python image_generator.py --provider huggingface
   ```

---

### Step 2: Review Images

```powershell
# View generated images
start generated_images\

# Copy good ones to approved folder
cp generated_images\*.png approved_images\
```

---

### Step 3: Build PDF

```powershell
python pdf_builder.py
```

Output: `output/My_First_Big_Coloring_Book_Interior.pdf`

---

### Step 4: Check PDF Quality

```powershell
start output\My_First_Big_Coloring_Book_Interior.pdf
```

Verify:
- ✅ All 100 pages present
- ✅ Images centered
- ✅ Black and white only
- ✅ No text or watermarks

---

### Step 5: Design Cover

The PDF builder printed cover dimensions. Use them in Canva:

1. Go to https://www.canva.com
2. Create custom size (from pdf_builder output)
3. Design front cover, back cover, spine
4. Download as PDF

---

### Step 6: Publish on KDP

1. Go to https://kdp.amazon.com/en_US/create
2. Click "Paperback"
3. Fill in:
   - Title: "My First Big Coloring Book"
   - Author: Your pen name
   - Description: "100 fun coloring pages for kids ages 3-8..."
4. Upload interior PDF
5. Upload cover PDF
6. Set price: $6.99
7. Publish!

---

## 📊 Expected Timeline

| Task | Time |
|------|------|
| Generate 100 images (placeholder) | 5 min |
| Generate 100 images (real AI) | 2 hours |
| Review images | 30 min |
| Build PDF | 2 min |
| Design cover | 30 min |
| Upload to KDP | 15 min |
| **Total (placeholder)** | **1 hour** |
| **Total (real AI)** | **3 hours** |

---

## 💰 Cost Breakdown

| Item | Cost |
|------|------|
| Hugging Face API (100 images) | **Free** (free tier) |
| Canva cover design | **Free** (free tier) |
| **Total** | **$0** |

Alternative (paid):
- Replicate API: $1 (100 images @ $0.01 each)
- Stability AI: $2 (100 images @ $0.02 each)

---

## 🎯 Success Metrics (Track After Publishing)

**Week 1:**
- Sales: ? copies
- Reviews: ?
- BSR: ?

**Decision point:**
- If 5+ sales/day → Create Book #2
- If <5 sales/day → Try different niche

---

## 🐛 Troubleshooting

**"No images in generated_images/"**
→ Run `python image_generator.py --provider local` first

**"Missing images when building PDF"**
→ Copy images from `generated_images/` to `approved_images/`

**"PDF looks bad"**
→ Check image quality in `generated_images/` first
→ Try different AI provider

**"Cover dimensions confusing"**
→ Use KDP Cover Calculator: https://kdp.amazon.com/en_US/cover-templates

---

## 📚 What's Next?

After Book #1 is published:

1. **Track sales** for 30 days
2. **If successful**: Create Book #2 (different theme)
3. **If not**: Research new niche, try again
4. **After 3 successful books**: Automate the pipeline

---

**You're ready to publish! Follow the steps above and you'll have a KDP book live in 3 hours. 🚀**
