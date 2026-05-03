import fitz  # PyMuPDF
import re
import os

def extract_paper_name_from_filename(pdf_path):
    """
    extract paper name and year from PDF name

    
    - ENGAA_2016_S1_QuestionPaper.pdf → ENGAA_2016_S1
    - ESAT_Physics_2025_June.pdf → ESAT_Physics_2025
    - TMUA_2024_Paper1.pdf → TMUA_2024_Paper1
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        str: 提取的试卷名称
    """
    # 获取文件名（不含路径）
    filename = os.path.basename(pdf_path)
    
    # 去掉 .pdf 扩展名
    name_without_ext = os.path.splitext(filename)[0]
    
    # 移除常见的后缀关键词
    suffixes_to_remove = [
        '_QuestionPaper',
        '_Question_Paper',
        '_QP',
        '_Paper',
        '_Exam',
        '_Test'
    ]
    
    paper_name = name_without_ext
    for suffix in suffixes_to_remove:
        if suffix in paper_name:
            paper_name = paper_name.split(suffix)[0]
            break
    
    return paper_name

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

def find_question_with_advanced_regex(page, question_num, expected_x=None):
    """
    Find question number using advanced regex and a strict Vertical Anchor.
    """
    blocks = page.get_text("blocks")
    q_str = str(question_num)
    
    for block in blocks:
        if len(block) < 5:
            continue
        bx0, by0, bx1, by1, text = block[:5]
        
        # 1. Broad left-side filter
        if bx0 > 80: 
            continue
            
        # 2. Ignore Headers and Footers
        if by0 < 50 or by0 > (page.rect.height - 60):
            continue

        # 3. Validate context using our advanced regex
        if is_valid_question_label(text, q_str):
            
            block_rect = fitz.Rect(bx0, by0, bx1, by1)
            words = page.get_text("words", clip=block_rect)
            
            for w in words:
                wx0, wy0, wx1, wy1, wtext = w[:5]
                
                # ---------------------------------------------------------
                # THE VERTICAL ANCHOR CHECK
                # ---------------------------------------------------------
                if expected_x is not None:
                    # If we have locked the anchor, this number MUST be exactly
                    # aligned with Question 1 (allow 10 pixels for minor PDF rendering shifts)
                    if abs(wx0 - expected_x) > 10:
                        continue 
                else:
                    # If we haven't found Question 1 yet, it must be on the extreme edge
                    if wx0 > 60: 
                        continue
                
                # Clean the word (strip trailing periods or parentheses)
                clean_wtext = re.sub(r'[\.\)]$', '', wtext.strip())
                
                # If we found the exact number, return ITS precise coordinates
                if clean_wtext == q_str:
                    return (wx0, wy0, wx1, wy1)
            
    return None

def auto_slice_entire_exam(pdf_path, paper_name, output_folder="output_questions"):
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
    
    paper_folder = os.path.join(output_folder, paper_name)
    
    if not os.path.exists(paper_folder):
        os.makedirs(paper_folder)
        print(f"📁 Created paper-specific folder: {paper_folder}")
    current_question = 1
    start_page_num=3
    for page_num in range(start_page_num, len(doc)-start_page_num):
        page = doc[page_num]
        page_width = page.rect.width
        
        y_coordinates = []
        
       # Add this variable right before the `while True:` loop
        expected_q_x = None
        
        while True:
            # Pass the anchor to the search function
            position = find_question_with_advanced_regex(page, current_question, expected_q_x)
            
            if position:
                x0, y0, x1, y1 = position
                top_y = max(0, y0 - 8)
                
                # ---------------------------------------------------------
                # LOCK THE ANCHOR WHEN WE FIND QUESTION 1
                # ---------------------------------------------------------
                if expected_q_x is None:
                    expected_q_x = x0
                    print(f"🔒 Locked Question Column Anchor at X={expected_q_x:.2f}")
                
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
                output_filename = os.path.join(paper_folder, f"Question_{q_num}.png")
                pix.save(output_filename)
                
                print(f"  💾 Saved: {output_filename}")
    
    print(f"\n✅ Finished! Total questions: {current_question - 1}")
    print(f"📂 All images saved to: {os.path.abspath(paper_folder)}")
    
    return current_question - 1

# ==========================================
# Run the Auto-Slicer
# ==========================================
if __name__ == "__main__":
    # 只需要提供PDF文件路径，程序会自动从文件名中提取试卷名称
    pdf_file = r"D:\PycharmProjects\PaperSplitter2.0\ExperiData\ENGAA_2016_S1_QuestionPaper.pdf" 
    
    # 自动提取试卷名称
    paper_name = extract_paper_name_from_filename(pdf_file)
    print(f"📋 从文件名提取的试卷名称: {paper_name}")
    
    auto_slice_entire_exam(pdf_file, paper_name)
