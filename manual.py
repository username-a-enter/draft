import sys
import os
from PIL import Image, ImageDraw
import shutil
from paddleocr import PaddleOCR
from torchvision.transforms.functional import adjust_gamma, to_grayscale
import numpy as np

if len(sys.argv) < 2:
    print("Please provide at least one image filename as an argument.")
    sys.exit(1)

# Start with a clean output directory
shutil.rmtree("output", ignore_errors=True)
os.makedirs("output", exist_ok=True)

ocr = PaddleOCR(use_angle_cls=True, lang="fr")


def process_image(image_filename):
    image = Image.open(image_filename).convert("RGBA")
    canvas = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(canvas)
    image_darkened = adjust_gamma(image, 5)
    image_darkened = to_grayscale(image_darkened, num_output_channels=3)
    ocr_result = ocr.ocr(np.asarray(image_darkened), cls=False)

    for line in ocr_result[0]:
        bounding_box = line[0]

        # # Draw bounding box
        # draw.rectangle(
        #     [
        #         (int(bounding_box[0][0]), int(bounding_box[0][1])),
        #         (int(bounding_box[2][0]), int(bounding_box[2][1])),
        #     ],
        #     outline=(255, 0, 0, 255),  # Red color with full opacity
        #     width=2,
        # )

        # # Draw strip that spans the entire height of the image,
        # # and the width of the bounding box
        # # drawing multiple of these for boxes of the same column
        # # should result in a strong blue color along the column
        # draw.rectangle(
        #     [
        #         (int(bounding_box[0][0]), 0),
        #         (int(bounding_box[2][0]), image.height),
        #     ],
        #     fill=(0, 0, 255, 50),  # Blue color with 20% opacity
        # )

        # Draw strip that spans the entire width of the image,
        # and the height of the bounding box
        # drawing multiple of these for boxes of the same row
        # should result in a strong green color along the row
        draw.rectangle(
            [
                (0, int(bounding_box[0][1])),
                (image.width, int(bounding_box[2][1])),
            ],
            fill=(0, 255, 0, 50),  # Green color with 20% opacity
        )

        image.alpha_composite(canvas)
        draw.rectangle(
            [(0, 0), (image.width, image.height)],
            fill=(255, 255, 255, 0),
        )  # Clear the canvas

    # Save the original image after adding layers
    base_name = os.path.splitext(os.path.basename(image_filename))[0]
    output_filename = f"output/{base_name}.png"
    image.save(output_filename)
    print(f"Image with bounding boxes saved as {output_filename}")


# Process all image files provided as arguments
for image_filename in sys.argv[1:]:
    process_image(image_filename)
