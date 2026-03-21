import fitz  # PyMuPDF
import re

def auto_slice_entire_exam(pdf_path):
    print(f"Opening {pdf_path} for automated slicing...")
    doc = fitz.open(pdf_path)
    
    current_question = 1  # The number we are currently hunting for
    
    # Loop through every single page in the PDF
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        
        y_coordinates = []
        
        # Keep hunting for questions on this page until we can't find the next one
        while True:
            q_label = f"{current_question}"
            
            # Search the page for the exact string (e.g., "1.")
            text_instances = page.search_for(q_label)
            
            # To avoid false positives (like a "1." in a paragraph), we can verify
            # that the "1." is positioned on the far left side of the page (e.g., x < 100)
            valid_instance = None
            for inst in text_instances:
                if inst.x0 < 100:  # Adjust this depending on the exam margin
                    valid_instance = inst
                    break
            
            if valid_instance:
                # We found the question! Record its Y-coordinate.
                top_y = max(0, valid_instance.y0 - 15) # 15 pixel margin
                y_coordinates.append({
                    "question": current_question,
                    "y_start": top_y
                })
                print(f"Found Question {current_question} on Page {page_num + 1}")
                current_question += 1 # Increment and hunt for the next number!
            else:
                # The next question is not on this page. Break the while loop
                # and move to slicing what we have, then go to the next page.
                break 
                
        # If we found any questions on this page, slice them up
        if y_coordinates:
            # Sort them top-to-bottom just in case
            y_coordinates = sorted(y_coordinates, key=lambda k: k['y_start'])
            
            for i, item in enumerate(y_coordinates):
                q_num = item["question"]
                y_top = item["y_start"]
                
                # The image ends where the next question begins, or at the bottom of the page
                if i + 1 < len(y_coordinates):
                    y_bottom = y_coordinates[i + 1]["y_start"]
                else:
                    y_bottom = page_height - 50 # 50 pixel margin at the bottom
                    
                # Define the rectangle and capture the image
                clip_rect = fitz.Rect(0, y_top, page_width, y_bottom)
                pix = page.get_pixmap(clip=clip_rect, matrix=fitz.Matrix(2, 2))
                
                output_filename = f"Question_{q_num}.png"
                pix.save(output_filename)
                
    print(f"\nFinished! Sliced up to Question {current_question - 1}.")

# ==========================================
# Run the Auto-Slicer
# ==========================================
if __name__ == "__main__":
    # Just point it to your file, and let it do all the work!
    pdf_file = r"D:\PycharmProjects\PaperSplitter2.0\ExperiData\Sample_Past_Paper.pdf" 
    auto_slice_entire_exam(pdf_file)