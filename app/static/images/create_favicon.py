from PIL import Image, ImageDraw, ImageFont
import os

def create_favicon(size, output_path):
    # Create a new image with a white background
    image = Image.new('RGB', (size, size), color='#4F46E5')
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("Arial", size=int(size * 0.6))
    except:
        font = ImageFont.load_default()
    
    # Draw the letter M
    text = "M"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save the image
    image.save(output_path)
    print(f"Created {output_path}")

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Create favicons in different sizes
create_favicon(16, os.path.join(script_dir, 'favicon-16x16.png'))
create_favicon(32, os.path.join(script_dir, 'favicon-32x32.png'))
create_favicon(180, os.path.join(script_dir, 'apple-touch-icon.png'))
create_favicon(32, os.path.join(script_dir, 'favicon.ico')) 