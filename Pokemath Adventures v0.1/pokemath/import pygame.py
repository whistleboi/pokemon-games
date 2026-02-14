import pygame
import os

# --- Directory Fix ---
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def generate_full_mask():
    pygame.init()
    print("Loading FullKanto.png (Native Resolution)...")
    
    try:
        original = pygame.image.load("FullKanto.png").convert()
    except:
        print("Error: FullKanto.png not found.")
        return

    w, h = original.get_size()
    print(f"Processing {w}x{h} pixels. This may take a minute...")
    
    # Create a 1:1 surface for the mask
    mask_surface = pygame.Surface((w, h))
    
    # Use PixelArray for much faster pixel access than get_at/set_at
    input_pixels = pygame.PixelArray(original)
    output_pixels = pygame.PixelArray(mask_surface)

    for x in range(w):
        for y in range(h):
            # Get the mapped integer color
            raw_color = input_pixels[x, y]
            # Unmap to RGB
            r, g, b, _ = original.unmap_rgb(raw_color)
            
            # THE LOGIC: 
            # If it looks like water (blue) or dark trees/walls, make it BLACK.
            is_wall = False
            if b > r + 30 and b > g + 10: # Water
                is_wall = True
            elif r < 100 and g < 130 and b < 100: # Trees/Outlines
                is_wall = True
            
            if is_wall:
                output_pixels[x, y] = (0, 0, 0)
            else:
                output_pixels[x, y] = (255, 255, 255)

    # Clean up PixelArrays to unlock the surfaces
    del input_pixels
    del output_pixels
    
    print("Saving KantoMask_Full.png...")
    pygame.image.save(mask_surface, "KantoMask_Full.png")
    print("Done!")
    pygame.quit()

if __name__ == "__main__":
    generate_full_mask()