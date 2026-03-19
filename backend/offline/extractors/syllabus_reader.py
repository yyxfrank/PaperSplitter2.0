import pdfplumber
import re

def extract_syllabus_text(pdf_path,start_page,end_page):
    """
    Extracts and returns all text from a given PDF file.
    """
    print(f"Processing: {pdf_path}...\n")
    full_text = ""
    
    # Safely open the PDF
    with pdfplumber.open(pdf_path) as pdf:
        
        # Loop through pages in the document
        for i in range(start_page,end_page):
            page=pdf.pages[i]
            
            # Extract the text from the current page
            page_text = page.extract_text()
            
            # Check if text was actually found (scanned images might return None)
            if page_text:
                full_text += f"\n--- Page {i + 1} ---\n"
                full_text += page_text
            else:
                print(f"Warning: No extractable text found on page {i + 1}.")
                
    return full_text

def is_content_page(page_text):
    """
    determine whether this page is a content page
    """
    if not page_text:
        return False
    
    # get first row
    first_line = page_text.split('\n')[0].strip().lower()
    
    # check if it contains keywords
    keywords = ['content', 'catalogue', 'contents', 'table of contents']
    
    for keyword in keywords:
        if keyword in first_line:
            return True
    
    return False

def parse_syllabus_chapters(pdf_path, sub=False):
    """
    Splits raw syllabus text into a dictionary of structured chapters.
    """
    # This Regex looks for "P " followed by a number, a colon, and text.
    chapter_pattern = r"P(\d+)\.\s*([A-Za-z\s-]+)"
    with pdfplumber.open(pdf_path) as pdf:
        first_five_pages=pdf.pages[:5]
        # Loop through first five page in the document
        for i, page in enumerate(first_five_pages):
            
            # Extract the text from the current page
            page_text = page.extract_text()
            chapters={}
            # Check if text was actually found (scanned images might return None)
            if page_text:
                if is_content_page(page_text):
                    print(f"find Content page {i + 1}")
                    C_items=re.finditer(chapter_pattern, page_text)
                    if C_items:
                        for item in C_items:
                            chapters[item.group(2)]=[item.group(1)]
                            # if there's no need for sub-chapters, skip this chapter
                            if not sub:
                                continue
                            # if we want to find sub-chapters, add page number range to the chapter dictionary
                            current_numbers=re.findall(r'\d+', item.group(0))
                            page_number=current_numbers[-1] if current_numbers else None
                            lines = page_text.split('\n')
                            current_line_idx = page_text[:item.start()].count('\n')
                            next_last = None
                            if current_line_idx + 1 < len(lines):
                                next_line = lines[current_line_idx + 1]
                                next_numbers = re.findall(r'\d+', next_line)
                                next_last = next_numbers[-1] if next_numbers else None
                            if page_number and next_last:
                                chapters[item.group(2)].append(page_number)
                                chapters[item.group(2)].append(next_last)
                    else:
                        print(f"Warning: No chapter found on page {i + 1}.")
                    break
            else:
                print(f"Warning: No extractable text found on page {i + 1}.")
    if not sub:
        return chapters           
    # Split the raw text into a list of chunks based on the pattern
    raw_chapters = chapters
    for chapter in raw_chapters:
        raw_text=extract_syllabus_text(pdf_path,int(raw_chapters[chapter][1]),int(raw_chapters[chapter][2]))
        raw_chapters[chapter] = split_into_subchapters(raw_text)
    structured_syllabus = {}
    
    for chunk in raw_chapters:
        chunk = chunk.strip()
        if not chunk:
            continue
            
        # Extract the title (the first line) and the body (everything else)
        lines = chunk.split('\n', 1)
        if len(lines) == 2:
            title = lines[0].strip()
            content = lines[1].strip()
            structured_syllabus[title] = content
            
    return structured_syllabus

def split_into_subchapters(chapter_text):
    """
    Takes the full text of a chapter and splits it into sub-chapters 
    based on the 'Px.y' pattern.
    """
    # Lookahead regex: splits the text right before 'P' followed by numbers, dot, numbers.
    # E.g., it matches the invisible space before "P1.1", "P12.4", etc.
    subchapter_pattern = r'(?=P\d+\.\d+)'
    
    # Split the massive chapter string into chunks
    chunks = re.split(subchapter_pattern, chapter_text)
    
    subchapters = {}
    
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
            
        # Separate the "Px.y" heading from the rest of the body text
        match = re.match(r'(P\d+\.\d+)(.*)', chunk, re.DOTALL)
        
        if match:
            heading = match.group(1).strip()
            body = match.group(2).strip()
            subchapters[heading] = body
            
    return subchapters


def is_color_black(color_value):
    """
    Checks if a pdfplumber color value represents black in RGB, Grayscale, or CMYK.
    """
    if color_value is None:
        return False
        
    # If it's a single number (Grayscale)
    if isinstance(color_value, (int, float)):
        return color_value == 0 or color_value == 0.0
        
    # If it's a tuple or list (RGB, Grayscale tuple, or CMYK)
    if isinstance(color_value, (tuple, list)):
        # Check RGB or Grayscale (all values are 0)
        if all(c == 0 or c == 0.0 for c in color_value):
            return True
        # Check CMYK (First three are 0, last is 1)
        if len(color_value) == 4:
            if color_value[0] == 0 and color_value[1] == 0 and color_value[2] == 0 and color_value[3] in (1, 1.0):
                return True
                
    return False

def extract_subchapters_from_black_frames(pdf_path, start_page_idx, end_page_idx):
    """
    Extracts text ONLY from inside rectangles that have a black border or black fill.
    """
    subchapters = []
    
    with pdfplumber.open(pdf_path) as pdf:
        # Loop through the specific chapter pages
        for i in range(start_page_idx, end_page_idx):
            page = pdf.pages[i]
            
            if page.rects:
                for rect in page.rects:
                    # Get the border color and fill color
                    border_color = rect.get('stroking_color')
                    fill_color = rect.get('non_stroking_color')
                    
                    # If EITHER the border or the fill is black, grab the text!
                    if is_color_black(border_color) or is_color_black(fill_color):
                        
                        # Define the bounding box (x0, top, x1, bottom)
                        bbox = (rect['x0'], rect['top'], rect['x1'], rect['bottom'])
                        
                        # Extract the text strictly from inside this box
                        frame_text = page.within_bbox(bbox).extract_text()
                        
                        if frame_text:
                            # Clean up the text and add it to our list
                            clean_text = frame_text.strip()
                            subchapters.append(clean_text)
                            print(f"Found black frame with text: {clean_text}")
                            
    return subchapters
# Example Usage:
dummy_raw_text = """
Introduction stuff here...
Chapter 1: Kinematics
This chapter covers velocity, acceleration, and graphs.
Chapter 2: Forces
This chapter covers Newton's laws and friction.
"""

chapters = parse_syllabus_chapters(dummy_raw_text)
for title in chapters.keys():
    print(f"Found: {title}")
# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # Replace with the actual path to your syllabus PDF
    pdf_file_path = "ExperiData/ESAT_Guide_Physics_June2025.pdf" 
    
    try:
        extracted_data = extract_syllabus_text(pdf_file_path)
        
        # Print the first 1000 characters just to verify it worked
        print("Extraction Successful! Here is a preview:\n")
        print(extracted_data[:1000]) 
        
    except FileNotFoundError:
        print(f"Error: Could not find the file at {pdf_file_path}. Please check the path.")