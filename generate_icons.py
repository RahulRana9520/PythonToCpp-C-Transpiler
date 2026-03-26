#!/usr/bin/env python3
"""
Generate PNG icons for PWA from SVG sources.
Install dependency: pip install pillow cairosvg
Then run: python3 generate_icons.py
"""

try:
    from PIL import Image, ImageDraw
    import os
except ImportError:
    print("ERROR: Pillow not found. Install with: pip install pillow")
    exit(1)

def create_icon_png(size, output_filename):
    """Generate a simple icon PNG with TransPyC branding."""
    # Create new image with dark background
    img = Image.new('RGBA', (size, size), color=(13, 17, 23, 255))  # Dark theme bg
    draw = ImageDraw.Draw(img)
    
    # Add rounded corners by drawing on a larger canvas
    corner_radius = size // 4
    
    # Create a new image with rounded corners
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=corner_radius, fill=255)
    
    # Create base icon
    base = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    base_draw = ImageDraw.Draw(base)
    
    # Draw blue background with rounded corners
    blue = (47, 129, 247, 255)  # #2f81f7
    base_draw.rounded_rectangle([(0, 0), (size-1, size-1)], radius=corner_radius, fill=blue)
    
    # Add lightning bolt (simple geometry)
    # Scale for the given size
    scale = size / 192
    bolt_points = [
        (96*scale, 36*scale),      # top
        (126*scale, 86*scale),     # right middle
        (96*scale, 86*scale),      # center
        (116*scale, 156*scale),    # bottom right
        (56*scale, 96*scale),      # center left
        (76*scale, 56*scale),      # top left
    ]
    base_draw.polygon(bolt_points, fill=(255, 255, 255, 255))
    
    # Paste with mask
    img.paste(base, (0, 0), mask)
    
    return img

def create_maskable_icon_png(size, output_filename):
    """Generate a maskable icon with safe zone padding."""
    # Maskable icons should have the main content in the center 2/3 of the image
    img = Image.new('RGBA', (size, size), color=(47, 129, 247, 255))  # Blue bg
    draw = ImageDraw.Draw(img)
    
    # Draw lightning bolt with safe zone
    safe_margin = size * 0.25  # 25% margin
    scale_factor = (size - 2*safe_margin) / 156
    
    base_x = safe_margin
    base_y = safe_margin
    
    bolt_points = [
        (base_x + 96*scale_factor, base_y + 36*scale_factor),
        (base_x + 126*scale_factor, base_y + 86*scale_factor),
        (base_x + 96*scale_factor, base_y + 86*scale_factor),
        (base_x + 116*scale_factor, base_y + 156*scale_factor),
        (base_x + 56*scale_factor, base_y + 96*scale_factor),
        (base_x + 76*scale_factor, base_y + 56*scale_factor),
    ]
    
    draw.polygon(bolt_points, fill=(255, 255, 255, 255))
    
    return img

def main():
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("[PWA] Generating app icons...")
    
    # Generate 192x192 icon
    try:
        icon_192 = create_icon_png(192, "icon-192x192.png")
        icon_192.save(os.path.join(output_dir, "icon-192x192.png"), "PNG")
        print("✓ Generated icon-192x192.png")
    except Exception as e:
        print(f"✗ Failed to generate icon-192x192.png: {e}")
    
    # Generate 512x512 icon
    try:
        icon_512 = create_icon_png(512, "icon-512x512.png")
        icon_512.save(os.path.join(output_dir, "icon-512x512.png"), "PNG")
        print("✓ Generated icon-512x512.png")
    except Exception as e:
        print(f"✗ Failed to generate icon-512x512.png: {e}")
    
    # Generate maskable 192x192
    try:
        maskable_192 = create_maskable_icon_png(192, "icon-192x192-maskable.png")
        maskable_192.save(os.path.join(output_dir, "icon-192x192-maskable.png"), "PNG")
        print("✓ Generated icon-192x192-maskable.png")
    except Exception as e:
        print(f"✗ Failed to generate icon-192x192-maskable.png: {e}")
    
    # Generate maskable 512x512
    try:
        maskable_512 = create_maskable_icon_png(512, "icon-512x512-maskable.png")
        maskable_512.save(os.path.join(output_dir, "icon-512x512-maskable.png"), "PNG")
        print("✓ Generated icon-512x512-maskable.png")
    except Exception as e:
        print(f"✗ Failed to generate icon-512x512-maskable.png: {e}")
    
    print("\n[PWA] Icon generation complete!")
    print("Place generated PNG files in the public/ directory and reference in manifest.json")

if __name__ == "__main__":
    main()
