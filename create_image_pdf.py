import fitz
from PIL import Image, ImageDraw, ImageFont

# Create an image with text
img = Image.new('RGB', (600, 800), color='white')
d = ImageDraw.Draw(img)
# Draw text (simulating a scan)
# Load default font is small, let's try to scale or just use default but acceptable?
# PIL default font is tiny. Let's try to get a font or just draw big.
try:
    font = ImageFont.truetype("Arial.ttf", 60)
except:
    font = ImageFont.load_default()

d.text((50, 50), "Tanpopo", fill='black', font=font)
d.text((50, 150), "This is a scanned document.", fill='black', font=font)

# Save as PDF
img.save("samples/scanned_sample.pdf", "PDF", resolution=100.0)
print("Created samples/scanned_sample.pdf")
