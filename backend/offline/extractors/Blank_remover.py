import os
from PIL import Image
import numpy as np

def trim_bottom_whitespace(image_path, padding=30, white_threshold=250):
    """
    Reads an image, finds the last row containing text/ink, 
    and crops off the empty white space below it.
    
    :param image_path: Path to the PNG file.
    :param padding: How many pixels of white space to leave at the bottom so it looks nice.
    :param white_threshold: Pixel brightness to consider "white" (0 is black, 255 is pure white).
    """
    try:
        # 1. Open the image and convert it to Grayscale ("L")
        img = Image.open(image_path).convert("L")
        
        # 2. Convert the image into a mathematical matrix (NumPy array)
        # Every pixel becomes a number from 0 (black) to 255 (white)
        img_data = np.array(img)
        
        # 3. Find all rows (Y-coordinates) that contain non-white pixels (ink)
        # We check for < 250 to account for slight grey anti-aliasing on text
        non_empty_rows = np.where(np.min(img_data, axis=1) < white_threshold)[0]
        
        if len(non_empty_rows) > 0:
            # The last element in this array is the Y-coordinate of the very last drop of ink!
            last_ink_y = non_empty_rows[-1]
            
            # 4. Calculate where to make the cut (adding our visual padding)
            cut_y = last_ink_y + padding
            
            # Ensure we don't accidentally try to cut outside the image boundaries
            cut_y = min(cut_y, img_data.shape[0])
            
            # 5. If the cut is actually reducing the image size significantly, do the crop
            if cut_y < img_data.shape[0] - 10:  # Only save if we are trimming at least 10 pixels
                original_img = Image.open(image_path)
                
                # Crop box format: (left, top, right, bottom)
                # We keep the full width, start at the top, and cut at 'cut_y'
                cropped_img = original_img.crop((0, 0, original_img.width, cut_y))
                
                cropped_img.save(image_path)
                print(f"✂️ Trimmed: {os.path.basename(image_path)}")
                
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def batch_trim_folder(folder_path):
    print(f"Starting whitespace trimmer in folder: {folder_path}\n")
    
    # Loop through all files in the directory
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".png"):
            file_path = os.path.join(folder_path, filename)
            trim_bottom_whitespace(file_path)
            
    print("\n✅ All images perfectly trimmed!")

# ==========================================
# Run the Trimmer
# ==========================================
if __name__ == "__main__":
    # Point this to the folder where your PyMuPDF script saves the questions
    target_folder = r"output_questions" 
    
    batch_trim_folder(target_folder)