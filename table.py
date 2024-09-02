import requests
import sys
from PIL import Image, ImageDraw
import json
import os
import shutil
import time

token = "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"
model = "microsoft/table-transformer-structure-recognition"
API_URL = f"https://api-inference.huggingface.co/models/{model}"
headers = {"Authorization": f"Bearer {token}"}

if len(sys.argv) < 2:
    print("Please provide at least one image filename as an argument.")
    sys.exit(1)

# Start with a clean output directory
shutil.rmtree("output", ignore_errors=True)
os.makedirs("output", exist_ok=True)


def query(filename):
    with open(filename, "rb") as f:
        data = f.read()
    while True:
        response = requests.post(API_URL, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            print("Request failed. Retrying in 3 seconds...")
            print(
                f"Response status text: ",
                json.dumps(json.loads(response.text), indent=2),
            )
            time.sleep(3)


def process_image(image_filename):
    output = query(image_filename)
    base_name = os.path.splitext(os.path.basename(image_filename))[0]
    original_image = Image.open(image_filename).convert("RGBA")
    overlay = Image.new("RGBA", original_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # with open(f"output/{base_name}.json", "w") as f:
    #     json.dump(output, f, indent=2)

    # Draw vertical lines at the x-min coordinates
    x_coords = [
        item["box"]["xmin"]
        for item in output
        if item["label"] == "table column" and item["score"] > 0.9
    ]
    x_coords = sorted(set(x_coords))
    x_coords = x_coords[1:]
    for x in x_coords:
        draw.line([(x, 0), (x, original_image.size[1])], fill=(0, 0, 255, 255), width=2)

    # # Extract y-coordinates of all table row boxes
    # y_coords = [item["box"]["ymin"] for item in output if item["label"] == "table row"]
    # last_y_max = sorted(
    #     [item["box"]["ymax"] for item in output if item["label"] == "table row"]
    # )[-1]
    # y_coords = sorted(set(y_coords))
    # y_coords.append(last_y_max)

    # # Draw horizontal lines at the y-coordinates
    # for y in y_coords:
    #     draw.line([(0, y), (original_image.size[0], y)], fill=(255, 0, 0, 255), width=2)

    # Save the resulting image
    result = Image.alpha_composite(original_image, overlay)
    output_filename = f"output/{base_name}.png"
    result.save(output_filename)
    print(f"Image saved as {output_filename}")


# Process all image files provided as arguments
for image_filename in sys.argv[1:]:
    process_image(image_filename)
