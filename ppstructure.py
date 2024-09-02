import os
import sys
import cv2
from paddleocr import PPStructure,save_structure_res
import shutil

table_engine = PPStructure(layout=False, show_log=True)
save_folder = 'output'

# Start with a clean output directory
shutil.rmtree(save_folder, ignore_errors=True)
os.makedirs(save_folder, exist_ok=True)

if len(sys.argv) < 2:
    print("Please provide at least one image filename as an argument.")
    sys.exit(1)

for img_path in sys.argv[1:]:
    img = cv2.imread(img_path)
    result = table_engine(img)
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    save_structure_res(result, save_folder, base_name)
    print(f"Image processed and saved: {base_name}")
