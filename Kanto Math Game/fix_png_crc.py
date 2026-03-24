import os
import sys

# This script fixes "libpng warning: iCCP: CRC error" by stripping corrupted color profiles.
# It requires the Pillow library. Install it via: pip install Pillow

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow library not found.")
    print("Please install it by running: pip install Pillow")
    input("Press Enter to exit...")
    sys.exit(1)

def fix_image(file_path):
    try:
        # Open the image
        img = Image.open(file_path)
        
        # Check if it has an ICC profile
        if "icc_profile" in img.info:
            # Force load the image data
            img.load()
            # Remove the corrupted profile
            img.info.pop("icc_profile")
            # Save it back to the same path, preserving transparency
            img.save(file_path, "PNG")
            print(f"Fixed: {os.path.basename(file_path)}")
            return True
            
    except Exception as e:
        print(f"Could not process {os.path.basename(file_path)}: {e}")
    
    return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "assets")
    
    if not os.path.exists(assets_dir):
        print(f"Assets folder not found at: {assets_dir}")
        return

    print(f"Scanning {assets_dir} for PNGs with bad iCCP chunks...")
    fixed_count = 0

    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            if file.lower().endswith(".png"):
                full_path = os.path.join(root, file)
                if fix_image(full_path):
                    fixed_count += 1

    print(f"Done! Fixed {fixed_count} images.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
