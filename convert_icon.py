import os
from PIL import Image

def convert_to_ico():
    png_path = "bigfishlogo.png"
    ico_path = "bigfishlogo.ico"
    
    if not os.path.exists(png_path):
        print(f"Error: {png_path} not found.")
        return

    try:
        img = Image.open(png_path)
        # Windows icons usually contain multiple sizes
        icon_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, sizes=icon_sizes)
        print(f"Successfully converted {png_path} to {ico_path}")
    except Exception as e:
        print(f"Failed to convert icon: {e}")

if __name__ == "__main__":
    convert_to_ico()