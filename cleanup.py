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


def extractNumber(text):
    no_space = re.sub(r"\s+", "", text)  # remove spaces
    no_comma = re.sub(r"[^0-9+-]", ".", no_space)  # 10,000 => 10.000

    try:
        if str(int(no_comma)) == no_comma:
            return no_space
    except:
        if str(float(no_comma)) == no_comma:
            return no_space
    return text


def cleanupText(text):
    # Remove Roman numerals from the text
    text = re.sub(r"\b[IVXLCDM]+\b", "", text)

    try:
        return extractNumber(text)
    except:
        # Remove non-alphabetic/space characters
        return re.sub(r"[^a-zA-Z ]+", "", text)


def process_image(image_filename):
    original_image = Image.open(image_filename).convert("RGBA")
    SPACE_FACTOR = 2
    FONT_FACTOR = 1

    # Increase the size of the canvas
    new_size = (
        int(original_image.width + 100),
        int(original_image.height * SPACE_FACTOR),
    )
    canvas = Image.new("RGBA", new_size, (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    result = ocr.ocr(image_filename, cls=False)

    # Calculate average height of all bounding boxes
    total_height = sum(box[0][2][1] - box[0][0][1] for box in result[0])
    avg_height = total_height / len(result[0])

    # Draw text on the new canvas
    for line in result[0]:
        bounding_box = line[0]
        text = cleanupText(line[1][0])
        height = bounding_box[2][1] - bounding_box[0][1]

        # Use average height to determine font size, with a scaling factor
        font_size = int(avg_height * FONT_FACTOR)
        font = ImageFont.truetype("arial.ttf", font_size)

        # Adjust position to account for larger canvas and add more space between items
        position = (
            int(bounding_box[0][0]),
            int(bounding_box[0][1] * SPACE_FACTOR),
        )
        draw.text(position, text, font=font, fill=(0, 0, 0, 255))

    # Save the new image with extracted text
    base_name = os.path.splitext(os.path.basename(image_filename))[0]
    output_filename = f"output/{base_name}.png"
    canvas.save(output_filename)
    print(f"Image with extracted text saved as {output_filename}")


# Process all image files provided as arguments
for image_filename in sys.argv[1:]:
    process_image(image_filename)
