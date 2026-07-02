#!/usr/bin/env python3
"""Generate OpenMythos social preview infographic (1200x630)."""

from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630

# Colors
BG = (15, 23, 42)  # dark slate
WHITE = (255, 255, 255)
GRAY = (148, 163, 184)
ACCENT = (56, 189, 248)  # sky blue
CAT_COLORS = [
    (239, 68, 68),
    (249, 115, 22),
    (245, 158, 11),
    (234, 179, 8),
    (132, 204, 22),
    (34, 197, 94),
    (20, 184, 166),
    (6, 182, 212),
    (59, 130, 246),
    (139, 92, 246),
    (236, 72, 153),
]

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# Try to load a decent font, fall back to default
try:
    font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
    font_sub = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    font_cat = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    font_stat = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
except:
    font_title = ImageFont.load_default()
    font_sub = ImageFont.load_default()
    font_cat = ImageFont.load_default()
    font_stat = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Title
draw.text((60, 40), "OpenMythos Governance Benchmark", fill=WHITE, font=font_title)
draw.text((60, 105), "v1.0", fill=ACCENT, font=font_sub)

# Stats row
stats = [
    ("275", "cases"),
    ("11", "categorieën"),
    ("750", "referenties"),
    ("CC-BY-4.0", "licentie"),
]
x = 60
for val, label in stats:
    draw.text((x, 160), val, fill=ACCENT, font=font_sub)
    draw.text((x, 195), label, fill=GRAY, font=font_small)
    x += 180

# Category grid
categories = [
    "hierarchy",
    "injection",
    "tool-scope",
    "contradiction",
    "canary",
    "overthinking",
    "hallucination",
    "calibration",
    "value-alignment",
    "temporal",
    "cross-lingual",
]

# Draw category boxes in a grid
cols = 6
box_w = 170
box_h = 55
gap_x = 15
gap_y = 12
start_x = 60
start_y = 260

for i, cat in enumerate(categories):
    col = i % cols
    row = i // cols
    x = start_x + col * (box_w + gap_x)
    y = start_y + row * (box_h + gap_y)
    color = CAT_COLORS[i % len(CAT_COLORS)]
    # Rounded rectangle (approximated)
    draw.rounded_rectangle(
        [x, y, x + box_w, y + box_h],
        radius=8,
        fill=color + (40,),
        outline=color,
        width=2,
    )
    # Truncate long names
    display = cat[:14]
    draw.text((x + 8, y + 8), display, fill=WHITE, font=font_cat)
    draw.text((x + 8, y + 28), "25 cases", fill=color, font=font_small)

# DOI badge area
draw.rounded_rectangle([60, 430, 500, 490], radius=8, outline=ACCENT, width=2)
draw.text((75, 440), "DOI: 10.5281/zenodo.21140158", fill=ACCENT, font=font_stat)

# Footer
draw.text(
    (60, 510), "github.com/djimit/openmythos-benchmark", fill=GRAY, font=font_stat
)

# Difficulty bar chart (right side)
chart_x = 600
chart_y = 260
chart_w = 540
chart_h = 200

draw.text((chart_x, chart_y - 35), "Moeilijkheidsgraad", fill=WHITE, font=font_stat)

diffs = [33, 62, 113, 62, 5]
max_val = max(diffs)
bar_w = 80
bar_gap = 20
for i, val in enumerate(diffs):
    bh = int((val / max_val) * 140)
    bx = chart_x + i * (bar_w + bar_gap)
    by = chart_y + 160 - bh
    color = CAT_COLORS[i + 5]
    draw.rounded_rectangle([bx, by, bx + bar_w, chart_y + 160], radius=4, fill=color)
    draw.text((bx + 20, by - 22), str(val), fill=WHITE, font=font_small)
    draw.text((bx + 15, chart_y + 165), f"L{i + 1}", fill=GRAY, font=font_small)

# Output
out_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "social-preview.png"
)
out_path = "/Users/dlandman/OpenMythos/openmythos-benchmark/social-preview.png"
img.save(out_path, "PNG")
print(f"Saved: {out_path}")
print(f"Size: {os.path.getsize(out_path)} bytes")
