import requests
import sys
from PIL import Image, ImageDraw
import json
import os
import shutil
import time

token = "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"
model = "poloclub/UniTable"
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
    # while True:
    response = requests.post(API_URL, headers=headers, data=data)
    # if response.status_code == 200:
    return response.json()
    # else:
        # print("Request failed. Retrying in 3 seconds...")
        # time.sleep(3)


def process_image(image_filename):
    output = query(image_filename)
    base_name = os.path.splitext(os.path.basename(image_filename))[0]

    with open(f"output/{base_name}.json", "w") as f:
        json.dump(output, f, indent=2)


# Process all image files provided as arguments
for image_filename in sys.argv[1:]:
    process_image(image_filename)
