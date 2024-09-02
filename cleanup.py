import sys
import os
from PIL import Image, ImageDraw, ImageFont
import shutil
from paddleocr import PaddleOCR
import re

if len(sys.argv) < 2:
    print("Please provide at least one image filename as an argument.")
    sys.exit(1)

# Start with a clean output directory
shutil.rmtree("output", ignore_errors=True)
os.makedirs("output", exist_ok=True)

ocr = PaddleOCR(use_angle_cls=True, lang="fr")


def process_image(image_filename):
    original_image = Image.open(image_filename).convert("RGBA")
    canvas = Image.new("RGBA", original_image.size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    result = ocr.ocr(image_filename, cls=False)

    # Calculate average height of all bounding boxes
    total_height = sum(box[0][2][1] - box[0][0][1] for box in result[0])
    avg_height = total_height / len(result[0])

    # Draw text on the new canvas
    for line in result[0]:
        bounding_box = line[0]
        text = line[1][0]
        height = bounding_box[2][1] - bounding_box[0][1]
        
        # Use average height to determine font size, with a scaling factor
        font_size = int(avg_height * 0.8)
        font = ImageFont.truetype("arial.ttf", font_size)

        # Remove Roman numerals from the text
        filtered_text = re.sub(r"\b[IVXLCDM]+\b", "", text)

        position = tuple(bounding_box[0])  # Top-left corner of the bounding box
        draw.text(position, filtered_text, font=font, fill=(0, 0, 0, 255))

    # Save the new image with extracted text
    base_name = os.path.splitext(os.path.basename(image_filename))[0]
    output_filename = f"output/{base_name}.png"
    canvas.save(output_filename)
    print(f"Image with extracted text saved as {output_filename}")


# Process all image files provided as arguments
for image_filename in sys.argv[1:]:
    process_image(image_filename)
