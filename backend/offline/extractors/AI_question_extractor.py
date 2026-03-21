import fitz  # PyMuPDF
import re
import os

def is_valid_question_label(text, question_num):
    """
    Validate if text is a valid question label.
    
    Matches numbers surrounded by whitespace or at line start,
    followed by a period, parenthesis, or just whitespace on both sides.
    """
    # Build regex patterns
    patterns = [
        # Pattern 1: whitespace + number + period + whitespace
        rf"(?<![a-zA-Z0-9]){question_num}\.(?=\s)",
        
        # Pattern 2: whitespace + number + parenthesis + whitespace
        rf"(?<![a-zA-Z0-9]){question_num}\)(?=\s)",
        
        # Pattern 3: line start + optional whitespace + number + period/parenthesis
        rf"^\s*{question_num}[\.\)](?=\s)",
        
        # Pattern 4: whitespace + number + whitespace (pure number format)
        rf"(?<![a-zA-Z0-9]){question_num}(?=\s)",
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True
    
    return False

def find_question_with_advanced_regex(page, question_num):
    """
    Find question number using advanced regex AND exact word coordinates.
    """
    blocks = page.get_text("blocks")
    q_str = str(question_num)
    
    for block in blocks:
        if len(block) < 5:
            continue
        bx0, by0, bx1, by1, text = block[:5]
        
        # 1. Filter: Left side of page only
        if bx0 > 100:
            continue
            
        # 2. Filter: Ignore Headers/Footers
        if by0 < 25 or by0 > (page.rect.height - 25):
            continue

        # 3. Validate context using our advanced regex
        if is_valid_question_label(text, q_str):
            
            # ---------------------------------------------------------
            # THE FIX: We found the valid block! Now find the EXACT word 
            # inside this block to prevent cutting off previous options.
            # ---------------------------------------------------------
            block_rect = fitz.Rect(bx0, by0, bx1, by1)
            words = page.get_text("words", clip=block_rect)
            
            for w in words:
                wx0, wy0, wx1, wy1, wtext = w[:5]
                
                # The actual number must also be on the left margin
                if wx0 > 100: 
                    continue
                
                # Clean the word (strip trailing periods or parentheses)
                clean_wtext = re.sub(r'[\.\)]$', '', wtext.strip())
                
                # If we found the exact number, return ITS precise coordinates
                if clean_wtext == q_str:
                    return (wx0, wy0, wx1, wy1)
            
            # Fallback just in case the exact word wasn't found
            return (bx0, by0, bx1, by1)
            
    return None

def auto_slice_entire_exam(pdf_path, output_folder="output_questions"):
    """
    Automatically slice entire exam paper (enhanced anti-false-positive version).
    
    Args:
        pdf_path: Path to PDF file
        output_folder: Output folder name (default: output_questions)
    """
    print(f"🔍 Opening {pdf_path} for automated slicing...")
    doc = fitz.open(pdf_path)
    
    # Create output folder
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created output folder: {output_folder}")
    
    current_question = 1
    start_page_num=3
    for page_num in range(start_page_num, len(doc)-start_page_num):
        page = doc[page_num]
        page_width = page.rect.width
        
        y_coordinates = []
        
        while True:
            # Find using advanced regex (block processing + regex validation)
            position = find_question_with_advanced_regex(page, current_question)
            
            if position:
                x0, y0, x1, y1 = position
                top_y = max(0, y0-8)
                
                y_coordinates.append({
                    "question": current_question,
                    "y_start": top_y,
                    "page": page_num + 1
                })
                print(f"✓ Question {current_question} → Page {page_num + 1}, Y={top_y}")
                current_question += 1
            else:
                # Try to find next number
                break
        
        # Slice and save
        if y_coordinates:
            y_coordinates = sorted(y_coordinates, key=lambda k: k['y_start'])
            
            for i, item in enumerate(y_coordinates):
                q_num = item["question"]
                y_top = item["y_start"]
                
                if i + 1 < len(y_coordinates):
                    y_bottom = y_coordinates[i + 1]["y_start"]
                else:
                    y_bottom = page.rect.height - 50
                
                clip_rect = fitz.Rect(0, y_top, page_width, y_bottom)
                pix = page.get_pixmap(clip=clip_rect, matrix=fitz.Matrix(2, 2))
                
                # Save to output folder
                output_filename = os.path.join(output_folder, f"Question_{q_num}.png")
                pix.save(output_filename)
                
                print(f"  💾 Saved: {output_filename}")
    
    print(f"\n✅ Finished! Total questions: {current_question - 1}")
    print(f"📂 All images saved to: {os.path.abspath(output_folder)}")
    
    return current_question - 1

# ==========================================
# Run the Auto-Slicer
# ==========================================
if __name__ == "__main__":
    # Just point it to your file, and let it do all the work!
    pdf_file = r"D:\PycharmProjects\PaperSplitter2.0\ExperiData\ENGAA_2016_S1_QuestionPaper.pdf" 
    auto_slice_entire_exam(pdf_file)