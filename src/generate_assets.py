"""
Icon generator for ArchivesOrganizer in assets/
Creates icon.png and icon.ico with sleek monochrome design.
"""

import os
from PIL import Image, ImageDraw

def generate_icons(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    size = 256
    # Create base RGBA image with transparent background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Base with rounded corners (minimalist dark card/box)
    # Monochrome palette: Charcoal background #1E1E1E, Details #E0E0E0 and #8E8E93
    card_bg = (30, 30, 30, 255)
    border_color = (70, 70, 70, 255)
    
    # Smooth container rectangle
    draw.rounded_rectangle([16, 16, 240, 240], radius=44, fill=card_bg, outline=border_color, width=4)

    # Minimalist geometric folder silhouette
    folder_color = (245, 245, 245, 255)
    folder_dim = (140, 140, 140, 255)

    # Folder tab
    draw.rounded_rectangle([48, 68, 114, 96], radius=8, fill=folder_dim)
    # Folder body
    draw.rounded_rectangle([48, 86, 208, 188], radius=16, fill=folder_color)

    # Organization stripes / file shelves (monochrome in medium and dark gray)
    line_dark = (40, 40, 40, 255)
    line_subtle = (90, 90, 90, 255)
    
    # Three horizontal stripes representing neat sorting
    draw.rounded_rectangle([68, 112, 188, 122], radius=4, fill=line_dark)
    draw.rounded_rectangle([68, 134, 156, 144], radius=4, fill=line_subtle)
    draw.rounded_rectangle([68, 156, 172, 166], radius=4, fill=line_dark)

    # Tag indicator boxes
    draw.rectangle([166, 134, 188, 144], fill=line_dark)

    png_path = os.path.join(output_dir, "icon.png")
    ico_path = os.path.join(output_dir, "icon.ico")

    img.save(png_path, format="PNG")
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    print(f"Icons successfully generated in:\n - {png_path}\n - {ico_path}")

if __name__ == "__main__":
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    generate_icons(assets_dir)
